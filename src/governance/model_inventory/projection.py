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
"""Model-inventory read model.

A current-state projection of the event log into ``model_inventory_view``. The
projection is derived and fully rebuildable: ``rebuild_inventory_view`` replays
the log from zero. Queries (``get_model``, ``list_models``) serve the read side.
"""
from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from src.database import app_connection, read_all
from src.governance.model_inventory._state import apply, initial_state
from src.governance.model_inventory.commands import AGGREGATE_TYPE


def _document(state) -> dict[str, Any]:
    """Scalar fields plus each non-empty collection, as one JSONB document."""
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def rebuild_inventory_view(config=None) -> int:
    """Rebuild the read model from the event log; return the model count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM model_inventory_view")
            for model_id, (state, version) in states.items():
                cur.execute(
                    "INSERT INTO model_inventory_view "
                    "(model_id, data, retired, version) VALUES (%s, %s, %s, %s)",
                    (model_id, Jsonb(_document(state)), state.retired, version),
                )
    return len(states)


def _row_to_dict(row: tuple) -> dict[str, Any]:
    return {
        "model_id": row[0],
        "data": row[1],
        "retired": row[2],
        "version": row[3],
    }


def get_model(model_id: str, config=None) -> dict[str, Any] | None:
    """Return one model's current state, or ``None`` if not present."""
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT model_id, data, retired, version "
                "FROM model_inventory_view WHERE model_id = %s",
                (model_id,),
            )
            row = cur.fetchone()
    return _row_to_dict(row) if row is not None else None


def list_models(config=None) -> list[dict[str, Any]]:
    """Return all models in the inventory, ordered by ``model_id``."""
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT model_id, data, retired, version "
                "FROM model_inventory_view ORDER BY model_id"
            )
            rows = cur.fetchall()
    return [_row_to_dict(row) for row in rows]
