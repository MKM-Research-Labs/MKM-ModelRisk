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
