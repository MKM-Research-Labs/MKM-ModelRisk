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
"""HTTP API for the immutable audit trail (the event log)."""
from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

from src.database import Event, read_all
from src.governance.collections import (
    EVENT_ITEM_ADDED,
    EVENT_ITEM_REMOVED,
    EVENT_ITEM_UPDATED,
)

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")


def _flat_fields(payload: dict) -> dict[str, Any]:
    """Payload entries that are item fields (not routing/metadata keys)."""
    return {k: v for k, v in payload.items()
            if k not in ("collection", "item_id") and not k.startswith("_")}


def _changes(event: Event) -> list[dict[str, Any]]:
    """A per-field before/after list for collection events (empty otherwise).

    New events carry the old values under ``_changes`` / ``_removed``; older
    events predate that capture, so their ``from`` is ``None`` (rendered as a
    plain "set to" rather than an "old -> new").
    """
    payload = event.payload or {}
    if event.event_type == EVENT_ITEM_UPDATED:
        meta = payload.get("_changes")
        if meta:
            return [{"field": k, "from": d.get("from"), "to": d.get("to")}
                    for k, d in meta.items()]
        return [{"field": k, "from": None, "to": v} for k, v in _flat_fields(payload).items()]
    if event.event_type == EVENT_ITEM_ADDED:
        return [{"field": k, "from": None, "to": v} for k, v in _flat_fields(payload).items()]
    if event.event_type == EVENT_ITEM_REMOVED:
        removed = payload.get("_removed") or {}
        return [{"field": k, "from": v, "to": None} for k, v in removed.items()]
    return []


def _target(event: Event) -> dict[str, Any] | None:
    """The specific record a collection event acted on (list + item id)."""
    payload = event.payload or {}
    if payload.get("collection"):
        return {"collection": payload["collection"], "item_id": payload.get("item_id")}
    return None


def _event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "global_seq": event.global_seq,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": event.aggregate_id,
        "stream_seq": event.stream_seq,
        "event_type": event.event_type,
        "actor": event.actor,
        "reason": event.reason,
        "recorded_at": event.recorded_at.isoformat(),
        "payload": event.payload,
        "target": _target(event),
        "changes": _changes(event),
    }


@audit_bp.get("")
def list_events():
    """Return the full event log in global order, most recent first."""
    events = read_all()
    return jsonify([_event_to_dict(e) for e in reversed(events)])
