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
"""Generic, spec-driven engine for structured collections on any aggregate.

A "collections" value is a ``dict[str, tuple[dict]]`` mapping a collection name
(``assumptions``, ``agenda``, …) to its items, each item a dict carrying an
``item_id``. The same three events drive every collection on every aggregate:
``CollectionItemAdded`` / ``CollectionItemUpdated`` / ``CollectionItemRemoved``.

This module is pure: ``fold`` rebuilds state from events; ``decide_*`` validate a
command against the per-collection spec and return ``(event_type, payload)`` or
raise ``DomainError``. Aggregate-specific guards (does the aggregate exist? is it
retired?) stay in each aggregate's rules, which call into these helpers.
"""
from __future__ import annotations

from typing import Any

from src.governance.errors import DomainError

EVENT_ITEM_ADDED = "CollectionItemAdded"
EVENT_ITEM_UPDATED = "CollectionItemUpdated"
EVENT_ITEM_REMOVED = "CollectionItemRemoved"

COLLECTION_EVENTS = (EVENT_ITEM_ADDED, EVENT_ITEM_UPDATED, EVENT_ITEM_REMOVED)


def fold(collections: dict[str, tuple], event_type: str, payload: dict[str, Any]):
    """Apply a collection event; return the new collections dict, or None.

    Returns ``None`` when ``event_type`` is not a collection event, so callers
    can fall through to their own (aggregate-specific) event handling.
    """
    collection = payload.get("collection")
    if event_type == EVENT_ITEM_ADDED:
        item = {k: v for k, v in payload.items() if k != "collection" and not k.startswith("_")}
        return {**collections, collection: collections.get(collection, ()) + (item,)}
    if event_type == EVENT_ITEM_UPDATED:
        item_id = payload["item_id"]
        # ``_``-prefixed keys are audit metadata (e.g. ``_changes`` old→new
        # values), never item state — the fold only applies the flat field keys.
        changes = {k: v for k, v in payload.items()
                   if k not in ("collection", "item_id") and not k.startswith("_")}
        items = tuple(
            {**it, **changes} if it["item_id"] == item_id else it
            for it in collections.get(collection, ())
        )
        return {**collections, collection: items}
    if event_type == EVENT_ITEM_REMOVED:
        items = tuple(
            it for it in collections.get(collection, ()) if it["item_id"] != payload["item_id"]
        )
        return {**collections, collection: items}
    return None


def _spec(specs: dict, collection: str) -> dict:
    spec = specs.get(collection)
    if spec is None:
        raise DomainError(f"unknown collection: {collection}")
    return spec


def _has_item(collections: dict, collection: str, item_id: str) -> bool:
    return any(it["item_id"] == item_id for it in collections.get(collection, ()))


def _find_item(collections: dict, collection: str, item_id: str) -> dict | None:
    return next((it for it in collections.get(collection, ()) if it["item_id"] == item_id), None)


def _validate(spec: dict, fields: dict[str, Any], *, require_required: bool) -> None:
    by_key = {f["key"]: f for f in spec["fields"]}
    for key, value in fields.items():
        field_spec = by_key.get(key)
        if field_spec is None:
            raise DomainError(f"unknown field: {key}")
        if field_spec["type"] == "choice" and value not in field_spec["options"]:
            allowed = ", ".join(field_spec["options"])
            raise DomainError(f"{field_spec['label']} must be one of: {allowed}")
        # A multichoice holds SEVERAL of its options (a person may be both an owner and a
        # committee member). Stored as a list so the record says what it means; a bare
        # string would make "owner" and "owner,chair" the same shape and invite parsing.
        if field_spec["type"] == "multichoice":
            if not isinstance(value, list):
                raise DomainError(f"{field_spec['label']} must be a list of values")
            unknown = [v for v in value if v not in field_spec["options"]]
            if unknown:
                allowed = ", ".join(field_spec["options"])
                raise DomainError(
                    f"{field_spec['label']}: unknown value(s) {', '.join(map(str, unknown))} "
                    f"— must be drawn from: {allowed}")
    if require_required:
        for field_spec in spec["fields"]:
            if field_spec.get("required") and not fields.get(field_spec["key"]):
                raise DomainError(f"{field_spec['label']} is required")


def decide_add(
    collections: dict, specs: dict, *, collection: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    spec = _spec(specs, collection)
    _validate(spec, fields, require_required=True)
    item_id = f"{spec['id_prefix']}-{len(collections.get(collection, ())) + 1:03d}"
    payload: dict[str, Any] = {"collection": collection, "item_id": item_id}
    payload.update(fields)
    return EVENT_ITEM_ADDED, payload


def decide_update(
    collections: dict, specs: dict, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    spec = _spec(specs, collection)
    current = _find_item(collections, collection, item_id)
    if current is None:
        raise DomainError(f"unknown item: {item_id}")
    _validate(spec, fields, require_required=False)
    payload: dict[str, Any] = {"collection": collection, "item_id": item_id}
    payload.update(fields)
    # Capture the before/after for the audit trail (skipped by ``fold``).
    payload["_changes"] = {k: {"from": current.get(k), "to": v} for k, v in fields.items()}
    return EVENT_ITEM_UPDATED, payload


def decide_remove(
    collections: dict, specs: dict, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _spec(specs, collection)
    current = _find_item(collections, collection, item_id)
    if current is None:
        raise DomainError(f"unknown item: {item_id}")
    # Retain the removed item's values so the audit trail can show what was lost.
    removed = {k: v for k, v in current.items() if k != "item_id"}
    return EVENT_ITEM_REMOVED, {"collection": collection, "item_id": item_id, "_removed": removed}
