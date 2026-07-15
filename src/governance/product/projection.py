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

from src.database import read_all, read_view, replace_view
from src.governance.product._state import apply, initial_state
from src.governance.product.commands import AGGREGATE_TYPE

_VIEW = "product_view"
_COLUMNS = ("product_id", "data", "retired", "version")


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
    rows = ((product_id, _document(state), state.retired, version)
            for product_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_product(product_id: str, config=None) -> dict[str, Any] | None:
    rows = read_view(_VIEW, _COLUMNS, where="product_id", value=product_id, config=config)
    return rows[0] if rows else None


def list_products(config=None) -> list[dict[str, Any]]:
    return read_view(_VIEW, _COLUMNS, order_by="product_id", config=config)
