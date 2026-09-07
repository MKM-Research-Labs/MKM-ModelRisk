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
``CollectionItemAdded`` / ``CollectionItemUpdated`` / ``CollectionItemRemoved`` /
``CollectionItemMoved`` (order is state, so changing it is an event too).

This module is pure: ``fold`` rebuilds state from events; ``decide_*`` validate a
command against the per-collection spec and return ``(event_type, payload)`` or
raise ``DomainError``. Aggregate-specific guards (does the aggregate exist? is it
retired?) stay in each aggregate's rules, which call into these helpers.
"""
from __future__ import annotations

from typing import Any

from config.governance import VALID_MOVE_DIRECTIONS
from src.governance.errors import DomainError

EVENT_ITEM_ADDED = "CollectionItemAdded"
EVENT_ITEM_UPDATED = "CollectionItemUpdated"
EVENT_ITEM_REMOVED = "CollectionItemRemoved"
# Order is state, so changing it is an event like any other. Keeping the order in
# the log rather than in a position field on each item means there is no second
# copy of it to fall out of step, and the audit trail shows who reordered what.
EVENT_ITEM_MOVED = "CollectionItemMoved"

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
    if event_type == EVENT_ITEM_MOVED:
        items = list(collections.get(collection, ()))
        index = next((i for i, it in enumerate(items) if it["item_id"] == payload["item_id"]), None)
        if index is None:
            return {**collections, collection: tuple(items)}
        swap = index - 1 if payload.get("direction") == "up" else index + 1
        if 0 <= swap < len(items):
            items[index], items[swap] = items[swap], items[index]
        return {**collections, collection: tuple(items)}
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


def _find_item(collections: dict, collection: str, item_id: str) -> dict | None:
    return next((it for it in collections.get(collection, ()) if it["item_id"] == item_id), None)


def next_item_id(items, prefix: str) -> str:
    """Mint the next id for a collection: one past the highest number in use.

    Numbering from the item *count* instead reissues an id as soon as one has been
    removed — that is how the governance Documents area came to hold two DOC-017s.
    Nothing downstream distinguishes them: ``fold`` applies an update to every item
    whose id matches and a removal to all of them, so retagging one document
    silently retags the other and deleting one deletes both.

    Ids of removed items are not reserved — the numbering follows what is on the
    record, not what once was — so retiring the newest item frees its number again.
    That leaves no two live items sharing an id, which is the collision that bites.
    """
    highest = 0
    for item in items:
        tail = str(item.get("item_id", "")).rsplit("-", 1)[-1]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return f"{prefix}-{highest + 1:03d}"


def _validate(
    spec: dict, fields: dict[str, Any], *, require_required: bool, allow_readonly: bool = False
) -> None:
    by_key = {f["key"]: f for f in spec["fields"]}
    for key, value in fields.items():
        field_spec = by_key.get(key)
        if field_spec is None:
            raise DomainError(f"unknown field: {key}")
        # None clears a field — how a proposal is withdrawn once it has been ruled on.
        if value is None:
            continue
        # A readonly field is written by one sanctioned path and no other — a person's
        # ratified roles are granted by their MRC, so the generic edit screen must not be
        # able to set them, whatever it sends.
        # An immutable field is set when the item is created and never afterwards
        # (adds validate with require_required, updates do not): a status
        # vocabulary's stored value is what every record already holds, so editing
        # it would orphan them all. The label beside it is what changes.
        if field_spec.get("immutable") and not require_required:
            raise DomainError(
                f"{field_spec['label']} cannot be changed once set — records already "
                "carry it. Edit what it is shown as instead")
        if field_spec.get("readonly") and not allow_readonly:
            raise DomainError(
                f"{field_spec['label']} is not set directly — it is recorded by the "
                "process that grants it")
        # A reference-backed choice draws its live values from an admin-managed list.
        # ``options`` on such a field is the SHIPPED SEED, not the vocabulary: an
        # institution that adds an impact level, a priority or a lifecycle in Admin
        # must be able to use it, and checking the seed here rejected exactly that --
        # the admin list accepted the new word and every record refused it. This
        # module is pure and cannot read the list, so membership is checked against
        # the live vocabulary in the command layer (reference.reject_unknown_values),
        # which is the same split the multichoice branch below describes.
        if (field_spec["type"] == "choice" and not field_spec.get("reference")
                and value not in field_spec["options"]):
            allowed = ", ".join(field_spec["options"])
            raise DomainError(f"{field_spec['label']} must be one of: {allowed}")
        # A multichoice holds SEVERAL of its options (a person may be both an owner and a
        # committee member). Stored as a list so the record says what it means; a bare
        # string would make "owner" and "owner,chair" the same shape and invite parsing.
        if field_spec["type"] == "multichoice":
            if not isinstance(value, list):
                raise DomainError(f"{field_spec['label']} must be a list of values")
            # A reference-backed multichoice draws its options from an admin-managed
            # list the domain does not hold — an action's owners come from the people
            # directory, which changes without the code moving. Shape is checked here;
            # membership is the reference list's business, exactly as it already is for
            # a reference-backed single choice.
            options = field_spec.get("options")
            unknown = [v for v in value if v not in options] if options else []
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
    item_id = next_item_id(collections.get(collection, ()), spec["id_prefix"])
    payload: dict[str, Any] = {"collection": collection, "item_id": item_id}
    payload.update(fields)
    return EVENT_ITEM_ADDED, payload


def decide_update(
    collections: dict, specs: dict, *, collection: str, item_id: str, fields: dict[str, Any],
    allow_readonly: bool = False,
) -> tuple[str, dict[str, Any]]:
    """``allow_readonly`` is for the one sanctioned writer of a readonly field — the MRC
    ratifying a person's roles. The generic edit path never passes it."""
    spec = _spec(specs, collection)
    current = _find_item(collections, collection, item_id)
    if current is None:
        raise DomainError(f"unknown item: {item_id}")
    _validate(spec, fields, require_required=False, allow_readonly=allow_readonly)
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


def decide_move(
    collections: dict, specs: dict, *, collection: str, item_id: str, direction: str
) -> tuple[str, dict[str, Any]]:
    """Move an item one place up or down its collection.

    Refused at the ends rather than silently doing nothing: a caller that thinks it
    reordered something and did not should be told so.
    """
    _spec(specs, collection)
    if direction not in VALID_MOVE_DIRECTIONS:
        raise DomainError(f"direction must be one of: {', '.join(VALID_MOVE_DIRECTIONS)}")
    items = list(collections.get(collection, ()))
    index = next((i for i, it in enumerate(items) if it["item_id"] == item_id), None)
    if index is None:
        raise DomainError(f"unknown item: {item_id}")
    swap = index - 1 if direction == "up" else index + 1
    if not 0 <= swap < len(items):
        raise DomainError(f"{item_id} is already {'first' if direction == 'up' else 'last'}")
    return EVENT_ITEM_MOVED, {"collection": collection, "item_id": item_id,
                              "direction": direction}
