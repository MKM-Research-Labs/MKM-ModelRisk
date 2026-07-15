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

from src.database import read_all, read_view, replace_view
from src.governance.mrc._state import apply, initial_state
from src.governance.mrc.commands import AGGREGATE_TYPE

_VIEW = "mrc_meeting_view"
_COLUMNS = ("meeting_id", "data", "status", "version")


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
    rows = ((meeting_id, _to_document(state), state.fields.get("status"), version)
            for meeting_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_meeting(meeting_id: str, config=None) -> dict[str, Any] | None:
    """Return one meeting's current state, or ``None`` if not present."""
    rows = read_view(_VIEW, _COLUMNS, where="meeting_id", value=meeting_id, config=config)
    return rows[0] if rows else None


def list_meetings(config=None) -> list[dict[str, Any]]:
    """Return all meetings, ordered by ``meeting_id``."""
    return read_view(_VIEW, _COLUMNS, order_by="meeting_id", config=config)


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
    scope_value pointing at one Division or Department. Department-level
    committees also resolve their parent Division from the Department
    reference list. Company-level committees are institution-wide and only
    contribute chair + frequency. Returns only the fields we can resolve.
    """
    if not mrc_value:
        return {}
    mrc = next(
        (m for m in refs.get("mrc") or [] if m.get("value") == mrc_value), None,
    )
    if not mrc:
        return {}
    result: dict[str, Any] = {}
    # Chair + frequency + the membership roster all carry through to the meeting,
    # so a meeting knows its committee's members without a second lookup.
    for key in ("chair", "secretary", "frequency", "voting_members", "non_voting_members",
                "quorum_require_chair", "quorum_require_secretary",
                "quorum_min_voting"):
        if mrc.get(key):
            result[key] = mrc[key]
    level, scope = mrc.get("level"), mrc.get("scope_value")
    if level == "Department" and scope:
        dept = next(
            (d for d in refs.get("department") or [] if d.get("value") == scope), None,
        )
        if dept:
            result["department"] = dept["value"]
            if dept.get("division"):
                result["division"] = dept["division"]
    elif level == "Division" and scope:
        div = next(
            (v for v in refs.get("division") or [] if v.get("value") == scope), None,
        )
        if div:
            result["division"] = div["value"]
    return result


def matching_mrc(
    division: str | None, department: str | None, refs: dict[str, list],
) -> tuple[dict[str, Any] | None, str | None]:
    """The most-specific active MRC committee covering an org location.

    The inverse of :func:`derive_org_scope`: given where a model sits, find the
    committee responsible for it. A Department-level committee for the model's
    department wins; failing that a Division-level committee for its division;
    failing that a Company-level (institution-wide) committee. Archived
    committees are never matched. Returns ``(committee, level)`` or
    ``(None, None)`` when nothing covers it.
    """
    active = [m for m in refs.get("mrc") or [] if m.get("archived") != "true"]
    if department:
        dept = next(
            (m for m in active
             if m.get("level") == "Department" and m.get("scope_value") == department),
            None,
        )
        if dept:
            return dept, "Department"
    if division:
        div = next(
            (m for m in active
             if m.get("level") == "Division" and m.get("scope_value") == division),
            None,
        )
        if div:
            return div, "Division"
    company = next((m for m in active if m.get("level") == "Company"), None)
    if company:
        return company, "Company"
    return None, None


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
