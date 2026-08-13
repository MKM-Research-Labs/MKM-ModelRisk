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
"""A change of model owner goes to the committee to be ratified.

Who owns a model is who answers for it, so the appointment is the committee's to
ratify — but the record cannot sit ownerless in the meantime. The new owner takes
the model straight away and the ratification follows: the console shows the new
name with the sign-off marked outstanding, and the request carries both names so
the committee ratifies a *change* rather than a fact it cannot check.

Raised automatically when the owner field changes, which is why it lives here
rather than behind a button: an owner change nobody remembered to send is exactly
the gap this closes.
"""
from __future__ import annotations

from src.command import CommandContext, dispatch
from src.governance.model_inventory import get_model
from src.governance.model_inventory.commands import update_model_field
from src.governance.model_inventory.projection import rebuild_inventory_view
from src.governance.reference import get_reference_lists
from src.web._signoff_routing import MODEL_SUBJECT, raise_signoff
from src.governance.mrc import matching_mrc

OWNER_KIND = "owner"


def raise_owner_ratification(ctx: CommandContext, model_id: str, *,
                             from_owner: str | None, to_owner: str | None) -> dict | None:
    """Queue the committee's ratification of an owner change.

    Silent about the cases where there is nothing to ratify — the owner did not
    actually change, or the model's division has no committee — because this runs
    off the back of an ordinary field edit. An owner change that cannot be routed
    must not fail the edit that was actually asked for; the model shows the
    outstanding sign-off either way, and the console says so.
    """
    if (from_owner or "") == (to_owner or ""):
        return None
    model = get_model(model_id)
    if model is None:
        return None
    data = model.get("data") or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"),
                               get_reference_lists())
    if mrc is None:
        return None
    return raise_signoff(
        ctx, MODEL_SUBJECT, model_id, kind=OWNER_KIND, target_mrc=mrc["value"],
        from_owner=from_owner or "", to_owner=to_owner or "",
        note=f"Owner changed from {from_owner or 'unassigned'} to {to_owner or 'unassigned'}",
    )


def pending_owner_request(data: dict) -> dict | None:
    """The undecided owner ratification on a model, if there is one.

    What the console reads to say "this owner is not ratified yet" beside the name
    it is already showing.
    """
    for request in reversed((data or {}).get("signoff_requests") or []):
        if request.get("kind") != OWNER_KIND:
            continue
        if request.get("status") in ("Pending", "Attached"):
            return request
        return None
    return None


__all__ = ["OWNER_KIND", "pending_owner_request", "raise_owner_ratification",
           "set_model_field"]


def set_model_field(ctx: CommandContext, model_id: str, *, field: str, value) -> None:
    """Update one model field, and route the ratification an owner change needs.

    The two belong together: an owner change that skipped the committee would be
    the gap this exists to close, and separating them would let a future caller
    write the field without it.
    """
    was = ((get_model(model_id) or {}).get("data") or {}).get("owner") if field == "owner" else None
    dispatch("update_model_field", update_model_field, context=ctx,
             model_id=model_id, field=field, value=value)
    rebuild_inventory_view()
    if field == "owner":
        raise_owner_ratification(ctx, model_id, from_owner=was, to_owner=value)
