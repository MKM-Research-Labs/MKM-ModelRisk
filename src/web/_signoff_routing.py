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
"""Sign-off request routing shared by the model- and meeting-side endpoints.

A Risk-rating sign-off request is raised by the model owner and queued against
the model's responsible MRC (``rag_signoff_requests`` on the model). It waits as
``Pending`` until a meeting of that committee is scheduled, at which point it is
pulled onto the meeting agenda and marked ``Attached``. This module holds the
two shared operations — attach one request, and drain all Pending requests for a
committee — used by ``api_models_signoff`` (raise) and ``api_mrc.lifecycle``
(schedule). It imports only governance functions (no blueprints) to stay
cycle-free.
"""
from __future__ import annotations

from typing import Any

from src.command import CommandContext, dispatch
from src.governance.model_inventory import (
    get_model,
    list_models,
    rebuild_inventory_view,
    update_collection_item as _model_update,
)
from src.governance.mrc import (
    add_collection_item as _mrc_add,
    get_meeting,
    list_meetings,
    rebuild_meeting_view,
)


def _newest(items: list[dict]) -> dict | None:
    """The item with the highest generated id suffix (e.g. SR-003 over SR-001)."""
    def _seq(item: dict) -> int:
        try:
            return int(str(item.get("item_id", "")).rsplit("-", 1)[-1])
        except ValueError:
            return -1
    return max(items, key=_seq) if items else None


def earliest_scheduled_for_mrc(target_mrc: str, config=None) -> dict | None:
    """The soonest Scheduled meeting bound to ``target_mrc`` (by date), if any."""
    scheduled = [
        m for m in list_meetings(config)
        if m.get("status") == "Scheduled" and (m["data"] or {}).get("mrc") == target_mrc
    ]
    scheduled.sort(key=lambda m: (m["data"] or {}).get("date") or "9999-99-99")
    return scheduled[0] if scheduled else None


def attach_request(
    ctx: CommandContext, model_id: str, request_item: dict, meeting: dict, config=None,
) -> None:
    """Put a queued request onto a meeting's agenda and mark it Attached.

    Two events (agenda item on the meeting; status update on the model request),
    both under the caller's single confirmation. Rebuilds both read models.
    """
    meeting_id = meeting["meeting_id"]
    proposed = request_item.get("proposed_rag")
    dispatch(
        "add_collection_item", _mrc_add, context=ctx,
        meeting_id=meeting_id, collection="agenda",
        fields={
            "title": f"Risk rating sign-off: {model_id} → {proposed}",
            "subject_model_id": model_id,
            "proposed_rag": proposed,
            "status": "Pending",
        },
    )
    rebuild_meeting_view(config)
    # Recover the id the engine assigned so the request can point back at it.
    refreshed = get_meeting(meeting_id, config=config) or {"data": {}}
    agenda = [
        a for a in (refreshed["data"].get("agenda") or [])
        if a.get("subject_model_id") == model_id and a.get("proposed_rag") == proposed
    ]
    agenda_item = _newest(agenda)
    dispatch(
        "update_collection_item", _model_update, context=ctx,
        model_id=model_id, collection="rag_signoff_requests", item_id=request_item["item_id"],
        fields={
            "status": "Attached", "meeting_id": meeting_id,
            "agenda_item_id": (agenda_item or {}).get("item_id", ""),
        },
    )
    rebuild_inventory_view(config)


def drain_pending_for_meeting(ctx: CommandContext, meeting: dict, config=None) -> int:
    """Attach every Pending request for this meeting's MRC onto its agenda.

    Called after a meeting is scheduled. Returns the number attached.
    """
    target_mrc = (meeting.get("data") or {}).get("mrc")
    if not target_mrc:
        return 0
    attached = 0
    for model in list_models(config):
        data = model.get("data") or {}
        for req in data.get("rag_signoff_requests") or []:
            if req.get("status") == "Pending" and req.get("target_mrc") == target_mrc:
                # Re-read the model each time so request ids stay valid across the
                # updates we apply within this loop.
                fresh = get_model(model["model_id"], config=config) or {"data": {}}
                current = next(
                    (r for r in (fresh["data"].get("rag_signoff_requests") or [])
                     if r.get("item_id") == req.get("item_id")),
                    None,
                )
                if current and current.get("status") == "Pending":
                    attach_request(ctx, model["model_id"], current, meeting, config=config)
                    attached += 1
    return attached
