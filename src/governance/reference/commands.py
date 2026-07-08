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
"""Commands to maintain the admin-managed reference lists (people + menus)."""
from __future__ import annotations

from typing import Any

from config.governance import REFERENCE_SPECS
from src.database import Event, append_event
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.reference._store import AGGREGATE_ID, AGGREGATE_TYPE, load


def _record(decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID,
        event_type=event_type, payload=payload, actor=actor, reason=reason,
        expected_version=version, config=config,
    )


def add_option(
    *, list_name: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add an entry to a reference list (a menu value or a person record)."""
    collections, version = load(config)
    decision = coll.decide_add(
        collections, REFERENCE_SPECS, collection=list_name, fields=fields
    )
    return _record(decision, version, actor, reason, config)


def update_option(
    *, list_name: str, item_id: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Edit an existing reference entry (e.g. a company's name or owner)."""
    collections, version = load(config)
    decision = coll.decide_update(
        collections, REFERENCE_SPECS, collection=list_name, item_id=item_id, fields=fields
    )
    return _record(decision, version, actor, reason, config)


def remove_option(
    *, list_name: str, item_id: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Remove a value from a menu list."""
    collections, version = load(config)
    decision = coll.decide_remove(
        collections, REFERENCE_SPECS, collection=list_name, item_id=item_id
    )
    return _record(decision, version, actor, reason, config)
