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

Its own module because it is its own concern -- the exchange showing that a record was
challenged, rather than the workflow's state -- and shared across record types for the
same reason the stages are. A challenge raised against an AI System is evidence of
exactly what a challenge raised against a model is.

Nothing here is ever edited or removed: the collection is append-only (see
``APPEND_ONLY_COLLECTIONS``), a challenge's Open/Resolved state is derived from whether
a later note answers it, and a correction is a new note, as it would be in minutes.
"""
from __future__ import annotations

from flask import jsonify

from config.governance import (CHALLENGE_OPEN, CHALLENGE_RESOLVED, NOTE_KIND_CHALLENGE,
                               NOTE_ROLE_OTHER, NOTE_ROLE_OWNER, NOTE_ROLE_REVIEWER,
                               VALID_NOTE_KINDS)
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._review_stages import stage_by_key, stamped_now

REVIEW_NOTES = "review_notes"


def _identities(actor: str) -> set[str]:
    """Every name this signed-in identity answers to.

    The actor is an SSO identity (an email); a record names its owner and reviewer by
    the People-directory *name* ("Johnny Mattimore"). Comparing the two directly never
    matches, so the directory is what joins them -- otherwise every note in the estate
    would be filed as a Participant and the record of challenge would show a review
    nobody in particular carried out.
    """
    known = {actor} if actor else set()
    for person in (get_reference_lists().get("people") or []):
        if person.get("email") and person["email"] == actor and person.get("name"):
            known.add(person["name"])
    return known


def role_of(data: dict, actor: str) -> str:
    """Which side of the review the author is on, worked out from the record.

    Derived from the record's own owner and reviewer rather than offered as a choice:
    "who challenged whom" must not be a matter of what somebody picked from a dropdown.
    Anyone else who joins the exchange is a participant, which is honest -- the platform
    attributes, it does not police who may speak.
    """
    known = _identities(actor)
    if (data.get("peer_reviewer") or "") in known:
        return NOTE_ROLE_REVIEWER
    if (data.get("owner") or "") in known:
        return NOTE_ROLE_OWNER
    return NOTE_ROLE_OTHER


def challenges(data: dict) -> list[dict]:
    """Every challenge raised, each with its derived state and the note answering it.

    Nothing is stored closed: a challenge is Open until some later note points back at
    it, so the state is read off the thread rather than written onto the row -- which is
    what lets the whole collection be append-only.
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


def register_review_note_route(blueprint, subject) -> None:
    """Attach the thread endpoint for one record type."""
    noun = subject.kind.replace("_", " ")

    @blueprint.post("/<subject_id>/review/note")
    def post_note(subject_id: str):
        """Add one note to a review stage's thread.

        The thread is the evidence that the record was challenged, so the author, their
        side of the review and the time are stamped here from the signed-in identity,
        and nothing posted can be edited or removed afterwards (the domain refuses). A
        note may answer an earlier challenge, which is how a challenge stops being open.
        """
        record = subject.get(subject_id)
        if record is None:
            return jsonify({"error": f"{noun} not found"}), 404
        body = json_body()
        text = (body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "a note cannot be empty"}), 400
        kind = body.get("kind") or VALID_NOTE_KINDS[0]
        if kind not in VALID_NOTE_KINDS:
            return jsonify({"error": f"kind must be one of: {', '.join(VALID_NOTE_KINDS)}"}), 400
        stage = body.get("stage")
        if stage not in stage_by_key(subject):
            return jsonify({"error": f"unknown review stage: {stage}"}), 400
        ctx = context_from_request(body)
        data = record.get("data") or {}
        subject.add_item_as("post_review_note", ctx, subject_id, REVIEW_NOTES, {
            "stage": stage, "text": text, "kind": kind,
            "resolves": (body.get("resolves") or "").strip(),
            "author": ctx.principal.actor,
            "author_role": role_of(data, ctx.principal.actor),
            "posted_at": stamped_now(),
        })
        subject.rebuild()
        return jsonify(subject.get(subject_id)), 201

    return post_note
