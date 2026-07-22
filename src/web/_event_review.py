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
"""Operational events feeding up to the MRC (W4b RACI feed-up).

When a meeting is scheduled, every product under that committee contributes its
not-yet-received operational-failure events as agenda items. The committee then
"receives" each one (recording comments and any action items) via ``api_mrc``.
This module owns the allocation; it imports only governance functions to stay
cycle-free.
"""
from __future__ import annotations

from src.command import CommandContext, dispatch
from src.governance.mrc import (
    add_collection_item as _mrc_add,
    get_meeting,
    matching_mrc,
    rebuild_meeting_view,
)
from src.governance.product import list_products
from src.governance.reference import get_reference_lists

RECEIVED = "Received"


def _product_mrc(data: dict) -> str | None:
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"), get_reference_lists())
    return mrc["value"] if mrc else None


def _already_allocated(meeting: dict, product_id: str, event_id: str) -> bool:
    return any(
        a.get("subject_product_id") == product_id and a.get("subject_event_id") == event_id
        for a in (meeting.get("data", {}).get("agenda") or [])
    )


def _event_title(product_id: str, event: dict) -> str:
    summary = (event.get("description") or "").strip()
    if len(summary) > 60:
        summary = summary[:57] + "..."
    return f"Operational event review: {product_id} — {summary}"


def allocate_events_for_meeting(ctx: CommandContext, meeting: dict, config=None) -> int:
    """Add a "received?" agenda item for every not-yet-received operational event on
    the products this committee is responsible for. Idempotent per (product, event)."""
    target_mrc = (meeting.get("data") or {}).get("mrc")
    if not target_mrc:
        return 0
    meeting_id = meeting["meeting_id"]
    allocated = 0
    for product in list_products(config):
        data = product.get("data") or {}
        if _product_mrc(data) != target_mrc:
            continue
        product_id = product["product_id"]
        for event in data.get("operational_failure_events") or []:
            if event.get("mrc_status") == RECEIVED:
                continue
            fresh = get_meeting(meeting_id, config=config) or {"data": {}}
            if _already_allocated(fresh, product_id, event["item_id"]):
                continue
            dispatch(
                "add_collection_item", _mrc_add, context=ctx,
                meeting_id=meeting_id, collection="agenda",
                fields={"title": _event_title(product_id, event), "status": "Pending",
                        "subject_product_id": product_id, "subject_event_id": event["item_id"]},
            )
            rebuild_meeting_view(config)
            allocated += 1
    return allocated
