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
"""Asking the committee to hibernate a record — or to bring one back.

Retiring is hibernation, not deletion, and it is the MRC's decision rather than
the owner's. The owner raises a request; the record carries on unchanged until
the committee ratifies it; reactivating takes the same trip in reverse.

That was written for models first, and every record type that can be retired
wants exactly it — so it lives here once, against the ``Subject`` adapter, rather
than being copied per aggregate. The copy is what went wrong before: an AI System
and an ML Application each shipped a Danger tab that POSTed straight to a retire
endpoint, so the one class of decision the committee exists to take was the one
their owners could take alone.

``target_mrc`` sits here too because the routing question — which committee covers
this record's division — is asked by the rating request as well, and had three
identical answers written down. Both name the record type from the subject's own
``noun``, so an error the owner reads says "AI System" rather than "ai_system".
"""
from __future__ import annotations

from flask import jsonify

from src.command import require_confirmation
from src.governance.mrc import matching_mrc
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import raise_signoff
from src.web._signoff_subject import Subject


def target_mrc(record: dict, noun: str):
    """The committee responsible for this record, or an error response.

    ``noun`` is how the record type is named to the person reading the error —
    "model", "AI System", "ML Application".
    """
    data = record["data"] or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"),
                               get_reference_lists())
    if mrc is None:
        return None, (jsonify({"error": f"no MRC committee covers this {noun}'s "
                                        "division / line of business — configure one "
                                        "under Admin → MRC first"}), 400)
    return mrc, None


def request_lifecycle_change(subject: Subject, subject_id: str, *,
                             kind: str, expect_retired: bool, serialise=None):
    """Raise a retire/reactivate request for the committee to ratify.

    The two are the same journey in opposite directions — the only difference is
    which state the record has to be in to ask — so they share one path.

    Retiring takes two gates: the owner confirms the request (recording a reason),
    and the MRC then ratifies it. This is the first of the two; nothing about the
    record changes here.

    ``serialise`` is applied to the record before it is returned, for a screen whose
    read scopes what it hands back (an ML Application's does).
    """
    noun = subject.noun
    record = subject.get(subject_id)
    if record is None:
        return jsonify({"error": f"{noun} not found"}), 404
    if bool(record.get("retired")) is not expect_retired:
        return jsonify(
            {"error": f"{noun} is already retired" if expect_retired is False
                      else f"{noun} is not retired"}
        ), 400
    mrc, error = target_mrc(record, noun)
    if error:
        return error
    body = json_body()
    ctx = context_from_request(body)
    # Gated explicitly: asking to hibernate a record (or wake one) is significant
    # enough to confirm, even though the committee has the final say.
    require_confirmation(f"request_{kind}", ctx)
    raise_signoff(ctx, subject, subject_id, kind=kind,
                  target_mrc=mrc["value"], note=body.get("note"))
    refreshed = subject.get(subject_id)
    return jsonify(serialise(refreshed) if serialise else refreshed), 201
