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
"""The HTTP surface every MRC-ratified per-division policy shares.

Three policies now run the ``ratified_policy`` lifecycle -- the risk policy, the ML
review policy and the functional groups -- and two parts of their APIs were the same
code three times over: the approve/reject pair, and the registry that answers "where
does every division stand". That is the shape that left four ``/fields`` handlers
quietly disagreeing about ``option_labels`` until they were gathered into
``grouped_field_specs``, and a third copy is the cheapest place to stop it.

What actually differs between the three is which command the dispatcher gates and
audits on, and which detail document a caller gets back. Those are arguments; the
bodies are not.
"""
from __future__ import annotations

from typing import Any, Callable

from flask import Blueprint, jsonify

from src.command import dispatch
from src.web._helpers import (context_from_request, json_body,
                              reference_options)


def register_ratification_routes(
    bp: Blueprint, prefix: str, *,
    approve_command: str, approve: Callable[..., Any],
    reject_command: str, reject: Callable[..., Any],
    detail: Callable[[str], dict],
) -> None:
    """Add ``<prefix>/<division>/approve`` and ``/reject`` to ``bp``.

    ``approve_command`` and ``reject_command`` stay each policy's own name --
    ``approve_risk_policy``, not one shared string -- because that name is what
    appears in the audit trail and what the confirm-to-amend policy is keyed on, and
    a reader has to be able to trace it back to the screen that raised it.

    The endpoints are named on the blueprint rather than taking the inner functions'
    names, which would otherwise all be the same; each policy has its own blueprint,
    so ``functional_groups.approve`` and ``risk_policy.approve`` do not collide.
    """

    @bp.post(f"{prefix}/<division>/approve", endpoint="approve")
    def approve_route(division: str):
        """Ratify the division's pending draft at its MRC: it becomes the live policy.

        The meeting is recorded on the event, because "the committee agreed this" is
        only evidence if you can say which sitting agreed it.
        """
        body = json_body()
        dispatch(approve_command, approve, context=context_from_request(body),
                 division=division, meeting_id=body.get("meeting_id"))
        return jsonify(detail(division))

    @bp.post(f"{prefix}/<division>/reject", endpoint="reject")
    def reject_route(division: str):
        """Decline the division's pending draft. The live policy is unchanged."""
        body = json_body()
        dispatch(reject_command, reject, context=context_from_request(body),
                 division=division, meeting_id=body.get("meeting_id"))
        return jsonify(detail(division))


def registry_payload(load: Callable[[str], dict], **extra: Any) -> dict:
    """Every division's live policy and lifecycle state, keyed by division name.

    This is what the console loads once at startup and resolves against a record's
    division, rather than each ``/fields`` endpoint learning to vary by record.

    ``states`` travels with the policies because without it an admin edit that is
    still a draft looks exactly like one that never arrived -- the confusion that
    cost a session when the risk policy first shipped.

    The divisions enumerated are the ones on the admin DIVISION list, so a division
    that has ratified a policy but is not on that list does not appear. All three
    policies behaved that way independently; now they do so in one place, which is
    where it can be reconsidered.
    """
    divisions = reference_options().get("division") or []
    states = {division: load(division) for division in divisions}
    return {
        **extra,
        "divisions": {d: s["live"] for d, s in states.items()},
        "states": {d: {"state": s["state"], "approved_at": s["approved_at"]}
                   for d, s in states.items()},
    }
