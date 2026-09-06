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
"""A change of owner goes to the committee to be ratified — on every record type.

Who owns a record is who answers for it, so the appointment is the committee's to
ratify — but the record cannot sit ownerless in the meantime. The new owner takes it
straight away and the ratification follows: the console shows the new name with the
sign-off marked outstanding, and the request carries both names so the committee
ratifies a *change* rather than a fact it cannot check.

Raised automatically when the owner field changes, which is why it lives here rather
than behind a button: an owner change nobody remembered to send is exactly the gap
this closes.

**Model-only until 2026-09-06.** Changing an ML Application's or an AI System's owner
went to nobody, while changing a model's went to the committee — a difference in
governance that no one chose and that contradicts the rule the AI/ML module is built
to: ownership is a sign-off trigger, and it is the same trigger for all three. Now
written once against ``Subject``, so a record type added later inherits it.
"""
from __future__ import annotations

from src.command import CommandContext
from src.governance.reference import get_reference_lists
from src.web._signoff_routing import MODEL_SUBJECT, raise_signoff
from src.governance.mrc import matching_mrc

OWNER_KIND = "owner"


def raise_owner_ratification(ctx: CommandContext, subject, subject_id: str, *,
                             from_owner: str | None, to_owner: str | None) -> dict | None:
    """Queue the committee's ratification of an owner change, for any record type.

    Silent about the cases where there is nothing to ratify — the owner did not
    actually change, or the record's division has no committee — because this runs
    off the back of an ordinary field edit. An owner change that cannot be routed
    must not fail the edit that was actually asked for; the record shows the
    outstanding sign-off either way, and the console says so.
    """
    if (from_owner or "") == (to_owner or ""):
        return None
    record = subject.get(subject_id)
    if record is None:
        return None
    data = record.get("data") or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"),
                               get_reference_lists())
    if mrc is None:
        return None
    return raise_signoff(
        ctx, subject, subject_id, kind=OWNER_KIND, target_mrc=mrc["value"],
        from_owner=from_owner or "", to_owner=to_owner or "",
        note=f"Owner changed from {from_owner or 'unassigned'} to {to_owner or 'unassigned'}",
    )


def pending_owner_request(data: dict) -> dict | None:
    """The undecided owner ratification on a record, if there is one.

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
           "set_record_field", "set_model_field"]


def set_record_field(ctx: CommandContext, subject, subject_id: str, *,
                     field: str, value) -> None:
    """Update one field on any governed record, and route the ratification an owner
    change needs.

    The two belong together: an owner change that skipped the committee would be the
    gap this exists to close, and separating them would let a caller write the field
    without it. That is precisely how the ML Application and AI System screens came to
    change owners without telling anybody.
    """
    was = ((subject.get(subject_id) or {}).get("data") or {}).get("owner") \
        if field == "owner" else None
    subject.set_field(ctx, subject_id, field, value)
    subject.rebuild()
    if field == "owner":
        raise_owner_ratification(ctx, subject, subject_id, from_owner=was, to_owner=value)


def set_model_field(ctx: CommandContext, model_id: str, *, field: str, value) -> None:
    """The model's spelling of ``set_record_field``, kept so its call site reads the
    same as it did."""
    set_record_field(ctx, MODEL_SUBJECT, model_id, field=field, value=value)
