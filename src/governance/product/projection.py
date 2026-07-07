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
"""Product read model: a current-state projection of the event log into ``product_view``."""
from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from src.database import app_connection, read_all
from src.governance.product._state import apply, initial_state
from src.governance.product.commands import AGGREGATE_TYPE


def derived_identifier(data: dict[str, Any]) -> str | None:
    """``<AnalyticsModelID>.<MarketDataModelID>.<CalculatingAgent>`` once bound."""
    parts = [data.get(key) for key in ("analytics_model", "market_data_model", "calculating_agent")]
    return ".".join(parts) if all(parts) else None


def _document(state) -> dict[str, Any]:
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    data["identifier"] = derived_identifier(data)
    return data


def rebuild_product_view(config=None) -> int:
    """Rebuild the read model from the event log; return the Product count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    with app_connection(config) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM product_view")
        for product_id, (state, version) in states.items():
            cur.execute(
                "INSERT INTO product_view (product_id, data, retired, version) VALUES (%s, %s, %s, %s)",
                (product_id, Jsonb(_document(state)), state.retired, version),
            )
    return len(states)


def _row_to_dict(row: tuple) -> dict[str, Any]:
    return {"product_id": row[0], "data": row[1], "retired": row[2], "version": row[3]}


def get_product(product_id: str, config=None) -> dict[str, Any] | None:
    with app_connection(config) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT product_id, data, retired, version FROM product_view WHERE product_id = %s", (product_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row is not None else None


def list_products(config=None) -> list[dict[str, Any]]:
    with app_connection(config) as conn, conn.cursor() as cur:
        cur.execute("SELECT product_id, data, retired, version FROM product_view ORDER BY product_id")
        rows = cur.fetchall()
    return [_row_to_dict(row) for row in rows]
