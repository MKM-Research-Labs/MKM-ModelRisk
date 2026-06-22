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

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")


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
    }


@audit_bp.get("")
def list_events():
    """Return the full event log in global order, most recent first."""
    events = read_all()
    return jsonify([_event_to_dict(e) for e in reversed(events)])
