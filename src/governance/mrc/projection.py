# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""MRC-meeting read model: a current-state projection of the event log."""
from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from src.database import app_connection, read_all
from src.governance.mrc._state import apply, initial_state
from src.governance.mrc.commands import AGGREGATE_TYPE


def _to_document(state) -> dict[str, Any]:
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def rebuild_meeting_view(config=None) -> int:
    """Rebuild the read model from the event log; return the meeting count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mrc_meeting_view")
            for meeting_id, (state, version) in states.items():
                cur.execute(
                    "INSERT INTO mrc_meeting_view "
                    "(meeting_id, data, status, version) VALUES (%s, %s, %s, %s)",
                    (
                        meeting_id,
                        Jsonb(_to_document(state)),
                        state.fields.get("status"),
                        version,
                    ),
                )
    return len(states)


def _row_to_dict(row: tuple) -> dict[str, Any]:
    return {
        "meeting_id": row[0],
        "data": row[1],
        "status": row[2],
        "version": row[3],
    }


def get_meeting(meeting_id: str, config=None) -> dict[str, Any] | None:
    """Return one meeting's current state, or ``None`` if not present."""
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT meeting_id, data, status, version "
                "FROM mrc_meeting_view WHERE meeting_id = %s",
                (meeting_id,),
            )
            row = cur.fetchone()
    return _row_to_dict(row) if row is not None else None


def list_meetings(config=None) -> list[dict[str, Any]]:
    """Return all meetings, ordered by ``meeting_id``."""
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT meeting_id, data, status, version "
                "FROM mrc_meeting_view ORDER BY meeting_id"
            )
            rows = cur.fetchall()
    return [_row_to_dict(row) for row in rows]


def _enrich(meeting: dict | None, refs: dict[str, list]) -> dict | None:
    """Overlay the derived org scope onto a meeting from its bound MRC."""
    if meeting is None:
        return None
    mrc_value = (meeting["data"] or {}).get("mrc")
    if not mrc_value:
        return meeting
    derived = derive_org_scope(mrc_value, refs)
    if derived:
        meeting["data"] = {**meeting["data"], **derived}
    return meeting


def get_meeting_enriched(meeting_id: str, config=None) -> dict | None:
    """Meeting with company/division/department/chair/frequency derived from MRC."""
    from src.governance.reference import get_reference_lists  # avoid import cycle
    return _enrich(get_meeting(meeting_id, config=config), get_reference_lists(config))


def list_meetings_enriched(config=None) -> list[dict]:
    """Every meeting with its MRC-derived fields folded in."""
    from src.governance.reference import get_reference_lists  # avoid import cycle
    refs = get_reference_lists(config)
    return [_enrich(m, refs) for m in list_meetings(config)]


def derive_org_scope(mrc_value: str | None, refs: dict[str, list]) -> dict[str, Any]:
    """Look up a meeting's org scope + chair + frequency from its MRC.

    The MRC reference row carries a level (Company/Division/Department) and a
    scope_value pointing at one Division or Department. Everything above that
    level chains up through the Division / Department reference lists. Returns
    only the fields we can resolve — missing links produce a partial dict.
    """
    if not mrc_value:
        return {}
    mrc = next(
        (m for m in refs.get("mrc") or [] if m.get("value") == mrc_value), None,
    )
    if not mrc:
        return {}
    result: dict[str, Any] = {}
    for key in ("chair", "frequency"):
        if mrc.get(key):
            result[key] = mrc[key]
    level, scope = mrc.get("level"), mrc.get("scope_value")
    if level == "Department" and scope:
        dept = next(
            (d for d in refs.get("department") or [] if d.get("value") == scope), None,
        )
        if dept:
            result["department"] = dept["value"]
            div = next(
                (v for v in refs.get("division") or [] if v.get("value") == dept.get("division")),
                None,
            )
            if div:
                result["division"] = div["value"]
                if div.get("company"):
                    result["company"] = div["company"]
    elif level == "Division" and scope:
        div = next(
            (v for v in refs.get("division") or [] if v.get("value") == scope), None,
        )
        if div:
            result["division"] = div["value"]
            if div.get("company"):
                result["company"] = div["company"]
    return result


def meeting_items_for_model(
    collection: str, model_id: str, config=None, *, field: str = "model_id",
) -> list[dict[str, Any]]:
    """All items from ``collection`` across every meeting where item[``field``] == ``model_id``.

    Each result is the original item, augmented with the source meeting's id,
    title and date so the model-side read view can credit and link back.

    ``field`` names the key on the item that carries the model reference —
    "model_id" for decisions/actions (default), "subject_model_id" for agenda
    sign-off items (W4c).
    """
    results: list[dict[str, Any]] = []
    for meeting in list_meetings(config):
        data = meeting.get("data") or {}
        for item in data.get(collection) or []:
            if item.get(field) == model_id:
                results.append({
                    **item,
                    "meeting_id": meeting["meeting_id"],
                    "meeting_title": data.get("title"),
                    "meeting_date": data.get("date"),
                })
    return results
