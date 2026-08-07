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
"""The record of challenge: the owner/reviewer thread on a review stage.

Its own module because it is its own concern — the exchange that shows a model was
challenged, rather than the workflow's state. Registered on the shared
``models_bp`` blueprint.
"""
from __future__ import annotations

from flask import jsonify

from config.governance import (CHALLENGE_OPEN, CHALLENGE_RESOLVED, NOTE_KIND_CHALLENGE,
                               NOTE_ROLE_OTHER, NOTE_ROLE_OWNER, NOTE_ROLE_REVIEWER,
                               VALID_NOTE_KINDS)
from src.command import dispatch
from src.governance.model_inventory import get_model
from src.governance.model_inventory.commands import add_collection_item
from src.governance.model_inventory.projection import rebuild_inventory_view
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web.api_models import models_bp
from src.web.api_models_review import _STAGE_BY_KEY, _stamped_now

REVIEW_NOTES = "review_notes"


def _identities(actor: str) -> set[str]:
    """Every name this signed-in identity answers to.

    The actor is an SSO identity (an email); a model names its owner and reviewer
    by the People-directory *name* ("Johnny Mattimore"). Comparing the two
    directly never matches, so the directory is what joins them — otherwise every
    note in the estate would be filed as a Participant and the record of challenge
    would show a review nobody in particular carried out.
    """
    known = {actor} if actor else set()
    for person in (get_reference_lists().get("people") or []):
        if person.get("email") and person["email"] == actor and person.get("name"):
            known.add(person["name"])
    return known


def _role(data: dict, actor: str) -> str:
    """Which side of the review the author is on, worked out from the record.

    Derived from the model's own owner and reviewer rather than offered as a
    choice: "who challenged whom" must not be a matter of what somebody picked
    from a dropdown. Anyone else who joins the exchange is a participant, which is
    honest — the platform attributes, it does not police who may speak.
    """
    known = _identities(actor)
    if (data.get("peer_reviewer") or "") in known:
        return NOTE_ROLE_REVIEWER
    if (data.get("owner") or "") in known:
        return NOTE_ROLE_OWNER
    return NOTE_ROLE_OTHER


def challenges(data: dict) -> list[dict]:
    """Every challenge raised, each with its derived state and the note answering it.

    Nothing is stored closed: a challenge is Open until some later note points back
    at it, so the state is read off the thread rather than written onto the row —
    which is what lets the whole collection be append-only.
    """
    notes = data.get(REVIEW_NOTES) or []
    answers = {n.get("resolves"): n for n in notes if n.get("resolves")}
    out = []
    for note in notes:
        if note.get("kind") != NOTE_KIND_CHALLENGE:
            continue
        answer = answers.get(note.get("item_id"))
        out.append({
            **note,
            "state": CHALLENGE_RESOLVED if answer else CHALLENGE_OPEN,
            "answered_by": (answer or {}).get("item_id", ""),
        })
    return out


def open_challenges(data: dict) -> list[dict]:
    """The challenges still standing — what the sign-off gate will refuse over."""
    return [c for c in challenges(data) if c["state"] == CHALLENGE_OPEN]


@models_bp.post("/<model_id>/review/note")
def post_note(model_id: str):
    """Add one note to a review stage's thread.

    The thread is the evidence that the model was challenged, so the author, their
    side of the review and the time are stamped here from the signed-in identity,
    and nothing posted can be edited or removed afterwards (the domain refuses;
    see APPEND_ONLY_COLLECTIONS). A note may answer an earlier challenge, which is
    how a challenge stops being open.
    """
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    body = json_body()
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "a note cannot be empty"}), 400
    kind = body.get("kind") or VALID_NOTE_KINDS[0]
    if kind not in VALID_NOTE_KINDS:
        return jsonify({"error": f"kind must be one of: {', '.join(VALID_NOTE_KINDS)}"}), 400
    stage = body.get("stage")
    if stage not in _STAGE_BY_KEY:
        return jsonify({"error": f"unknown review stage: {stage}"}), 400
    ctx = context_from_request(body)
    data = model.get("data") or {}
    fields = {
        "stage": stage, "text": text, "kind": kind,
        "resolves": (body.get("resolves") or "").strip(),
        "author": ctx.principal.actor,
        "author_role": _role(data, ctx.principal.actor),
        "posted_at": _stamped_now(),
    }
    dispatch(
        "post_review_note", add_collection_item, context=ctx,
        model_id=model_id, collection=REVIEW_NOTES, fields=fields,
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id)), 201


