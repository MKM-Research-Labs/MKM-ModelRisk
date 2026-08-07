# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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

from config.governance import (DATA_SOURCE_LIST, DEFAULT_DATA_SOURCES,
                               DEFAULT_MODEL_TYPES, DEFAULT_VENDORS,
                               MODEL_TYPE_LIST, REFERENCE_SPECS, VENDOR_LIST)
from config.identity import SYSTEM_ACTOR
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
    reason: str | None = None, config=None, allow_readonly: bool = False,
) -> Event:
    """Edit an existing reference entry (e.g. a company's name or owner).

    ``allow_readonly`` is passed only by the process that grants a readonly field — the
    MRC ratifying a person's roles — never by the admin edit screen.
    """
    collections, version = load(config)
    decision = coll.decide_update(
        collections, REFERENCE_SPECS, collection=list_name, item_id=item_id, fields=fields,
        allow_readonly=allow_readonly,
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


def ensure_default_model_types(*, actor: str = SYSTEM_ACTOR, config=None) -> int:
    """Seed the model-type list on a fresh install; return how many were added.

    A reference list with no entries renders as a free-text box rather than a
    dropdown (see ``resolve_field``), so an unseeded database would let every
    model be typed by hand and leave the Product bindings with no roles to read.

    Only fires when the list is empty. An adopter who has renamed our defaults,
    or deleted the ones that do not apply to them, must not find them back at the
    next restart -- so this seeds a vacuum, it does not reconcile a list someone
    has since curated.
    """
    collections, _ = load(config)
    if collections.get(MODEL_TYPE_LIST):
        return 0
    for entry in DEFAULT_MODEL_TYPES:
        add_option(list_name=MODEL_TYPE_LIST, fields=dict(entry), actor=actor,
                   reason="Seed default model types on first run", config=config)
    return len(DEFAULT_MODEL_TYPES)


# Single-value lists whose defaults seed on a fresh install, keyed by list name.
_DEFAULT_SIMPLE_LISTS = {
    DATA_SOURCE_LIST: DEFAULT_DATA_SOURCES,
    VENDOR_LIST: DEFAULT_VENDORS,
}


def ensure_default_reference_lists(*, actor: str = SYSTEM_ACTOR, config=None) -> int:
    """Seed the simple admin lists (data source, vendor); return how many added.

    Same rule as ``ensure_default_model_types``: each list is seeded only while
    empty, so an adopter who has curated (renamed, pruned, or extended) a list
    never finds the defaults back at the next restart. A model's ``vendor`` field
    and ``data_sources`` collection are strict references, so an unseeded list
    would leave those fields with nothing to pick.
    """
    added = 0
    for list_name, values in _DEFAULT_SIMPLE_LISTS.items():
        collections, _ = load(config)
        if collections.get(list_name):
            continue
        for value in values:
            add_option(list_name=list_name, fields={"value": value}, actor=actor,
                       reason=f"Seed default {list_name} on first run", config=config)
        added += len(values)
    return added
