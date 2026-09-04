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
"""The model review workflow: its stages, statuses and triggers (coding rule R1).

Split out of ``_inventory`` because the review is a process the inventory
records the state of, not a property of a model — and because the workflow is
about to grow the sign-off and its report.
"""
# --- The review workflow -----------------------------------------------------
# The review runs as five stages in the order the work happens. The reviewer gives
# each stage an interim approval, which moves the review on and sets the model's
# review status — so "where is this review up to" is answered by the work done,
# not by somebody remembering to update a dropdown.
#
# Interim approval is not a lock. Earlier stages stay open, because a reviewer who
# reaches the limitations and needs to reopen a question must be able to; what the
# approval records is that the two of them agreed at that point, and who said so.
REVIEW_STAGES = (
    {"key": "documents", "label": "Preliminary documents", "status": "Documents reviewed"},
    # The assumptions come before the nine questions because the sixth question
    # asks whether they are documented and justified: answering it means reading
    # them, so the review reads them first.
    {"key": "assumptions", "label": "Assumptions", "status": "Assumptions agreed"},
    {"key": "questions", "label": "The nine questions", "status": "Questions answered"},
    {"key": "weaknesses", "label": "Model weaknesses", "status": "Weaknesses agreed"},
    {"key": "limitations", "label": "Limitations of use", "status": "Limitations agreed"},
    {"key": "monitoring", "label": "Monitoring approach", "status": "Monitoring agreed"},
    # Last before sign-off: the committee should see what the review found outstanding,
    # and what is being done about it, before it signs anything off.
    {"key": "remediation", "label": "Remediation", "status": "Remediation agreed"},
)
REVIEW_STAGE_KEYS = tuple(stage["key"] for stage in REVIEW_STAGES)

# --- One workflow, three record types -----------------------------------------
# The stages above are the SAME for a model, an ML Application and an AI System:
# from a governance perspective the three are model-governed records and are
# reviewed identically. Two things legitimately differ, and only two.
#
# First, where each record keeps the questionnaire the "questions" stage works
# through. The stage is the same act -- the reviewer forms a verdict on each
# question the owner answered -- but a model is asked SR 26-2's nine, while ML
# Applications and AI Systems have questionnaires of their own.
#
# Keys are ``Subject.kind`` (src/web/_signoff_subject.py), the record-type
# vocabulary the committee routing already uses. Values are asserted against the
# per-record constants by a test, so this cannot drift from them.
REVIEW_PROGRESS_COLLECTION = "review_progress"
REVIEW_QUESTION_COLLECTIONS = {
    "model": "validation_questions",
    "ml_application": "ml_review_questions",
    "ai_system": "ai_review_questions",
}

# Second, what that stage is CALLED. "The nine questions" is a term of art for a
# model -- it names SR 26-2's nine specifically -- and reusing the phrase for a
# twelve-question AI questionnaire would be wrong rather than merely odd. The
# stage key never changes; only its label does.
REVIEW_QUESTION_STAGE_KEY = "questions"
REVIEW_QUESTION_STAGE_LABELS = {
    "model": "The nine questions",
    "ml_application": "The ML review questions",
    "ai_system": "The AI review questions",
}


def review_stages_for(kind: str) -> tuple[dict, ...]:
    """The review stages as one record type sees them.

    Same stages, same order, same statuses for every record type -- the only
    substitution is the questions stage's label. A caller that wants "the stages"
    without a record type in hand still gets the model's wording, which is the
    platform's default vocabulary.
    """
    label = REVIEW_QUESTION_STAGE_LABELS.get(kind)
    if not label:
        return REVIEW_STAGES
    return tuple(
        {**stage, "label": label} if stage["key"] == REVIEW_QUESTION_STAGE_KEY else stage
        for stage in REVIEW_STAGES
    )
DEFAULT_REVIEW_STATUS = "Not started"
# A new cycle is recorded, never a reset: the stage register is append-only, so
# starting a review writes a marker row and the stages agreed *before* it belong
# to the review that has already been signed off. The previous cycle stays
# readable — its approvals, its notes and its filed report are the history.
CYCLE_START_STAGE = "cycle-start"
# The status a signed-off review leaves behind.
SIGNED_OFF_REVIEW_STATUS = "Signed off"
VALID_REVIEW_STATUSES = (
    (DEFAULT_REVIEW_STATUS,) + tuple(stage["status"] for stage in REVIEW_STAGES)
    + (SIGNED_OFF_REVIEW_STATUS,)
)

# Why this review is happening. A review is not only a calendar event: a new
# version, a change of owner or a direction from the committee all start one, and
# what the reviewer should look at differs in each case.
VALID_REVIEW_TRIGGERS = (
    "Periodic", "New version", "Owner change", "MRC directed",
)
# The trigger that puts the "has the documentation been brought up to date?"
# checklist in front of the owner. A new version is the case where the model's
# write-up, its sensitivities and its test evidence all go stale at once.
NEW_VERSION_TRIGGER = "New version"

# The reviewer's position on one of the nine questions. Distinct from the owner's
# status: the owner says what the model does, the reviewer says whether that
# answer stands. A question can be Addressed by its owner and Challenged by its
# reviewer at the same time — that disagreement is the review doing its job, and
# the record has to be able to hold it.
DEFAULT_REVIEWER_VERDICT = "Not reviewed"
VALID_REVIEWER_VERDICTS = (DEFAULT_REVIEWER_VERDICT, "Accepted", "Challenged")
# The verdict that stands in the way of sign-off: a challenge is either answered
# or it is a reason the review is not finished.
CHALLENGED_VERDICT = "Challenged"

# --- The record of challenge --------------------------------------------------
# The thread between owner and reviewer is not a convenience: it is the evidence
# that the model was challenged, and it is printed in the report the committee
# receives. A note is either an ordinary remark or a Challenge — a stated
# objection, which is Open until a later note answers it.
NOTE_KIND_NOTE = "Note"
NOTE_KIND_CHALLENGE = "Challenge"
VALID_NOTE_KINDS = (NOTE_KIND_NOTE, NOTE_KIND_CHALLENGE)
# A challenge is Open until a later note answers it. Both words are derived state
# — no row is ever edited to carry them — but they are named here so the console,
# the sign-off gate and the report all use the same two.
CHALLENGE_OPEN = "Open"
CHALLENGE_RESOLVED = "Resolved"

# Which side of the review a note came from. Derived from the signed-in identity
# against the model's owner and reviewer — never typed, and never chosen from a
# dropdown, or "who challenged whom" would be a matter of what somebody selected.
NOTE_ROLE_OWNER = "Owner"
NOTE_ROLE_REVIEWER = "Reviewer"
NOTE_ROLE_OTHER = "Participant"

# Collections nobody may edit or delete, only add to. A challenge that could be
# tidied away afterwards is not evidence of anything: the record of what was said
# in a review has to be as fixed as the log it sits in.
# The sign-off joins the notes: an attestation that could be rewritten later
# would not be an attestation.
APPEND_ONLY_COLLECTIONS = ("review_notes", "review_signoffs")


# --- What the review stores ---------------------------------------------------
# The review's own collections live here rather than with the model's other
# registers: they describe the process, not the model, and keeping them beside the
# vocabulary they use means a change to the workflow is one file.
REVIEW_COLLECTION_SPECS = {
    # The owner/reviewer exchange, one row per note, scoped to the stage it was
    # said under. Append-only (see APPEND_ONLY_COLLECTIONS): this is the evidence
    # that the model was challenged, and evidence that can be edited afterwards is
    # not evidence. A correction is a new note, as it would be in minutes.
    "review_notes": {"label": "Review notes", "id_prefix": "RN", "fields": [
        {"key": "stage", "label": "Stage", "type": "text", "required": True},
        {"key": "text", "label": "Note", "type": "textarea", "required": True},
        {"key": "kind", "label": "Kind", "type": "choice", "options": VALID_NOTE_KINDS},
        # On an answering note: the challenge it answers. A challenge is Open
        # until some later note points at it — derived, never stored, because
        # storing it would mean editing the challenge to close it, and the whole
        # point of this collection is that nothing in it is ever edited.
        {"key": "resolves", "label": "Answers challenge", "type": "text", "hidden": True},
        # Stamped from the signed-in identity, never typed.
        {"key": "author", "label": "Author", "type": "text", "hidden": True},
        {"key": "author_role", "label": "Role", "type": "text", "hidden": True},
        {"key": "posted_at", "label": "Posted", "type": "text", "hidden": True},
    ]},
    # The reviewer's sign-off: the commentary, the moment, and the report it
    # produced. Append-only — a second cycle adds a second row, and what was
    # attested last time stands.
    "review_signoffs": {"label": "Review sign-offs", "id_prefix": "RS", "fields": [
        {"key": "commentary", "label": "Final commentary", "type": "textarea", "required": True},
        {"key": "signed_by", "label": "Signed by", "type": "text", "hidden": True},
        {"key": "signed_at", "label": "Signed at", "type": "text", "hidden": True},
        {"key": "report_filename", "label": "Report file", "type": "text", "hidden": True},
        {"key": "report_original_name", "label": "Report", "type": "text", "hidden": True},
    ]},
    # The reviewer's interim approvals, one row per stage agreed. Append-only by
    # intent: it is the record of who agreed what, and when, as the review ran —
    # the same reason the challenge threads will be. A stage approved twice
    # (reopened, re-agreed) leaves both rows standing.
    "review_progress": {"label": "Review progress", "id_prefix": "RP", "fields": [
        {"key": "stage", "label": "Stage", "type": "text", "required": True},
        {"key": "stage_label", "label": "Stage name", "type": "text"},
        {"key": "status", "label": "Review status set", "type": "text"},
        {"key": "note", "label": "Reviewer's note", "type": "text"},
        {"key": "approved_by", "label": "Approved by", "type": "text"},
        {"key": "approved_at", "label": "Approved at", "type": "text"},
    ]},
}


# --- The review's own fields --------------------------------------------------
# The fields the review workflow itself writes to, defined once and included by every
# record type that carries the workflow. They were a model's alone until the workflow
# was generalised, which meant an ML Application or an AI System could be taken through
# the stages but could not record WHY the review was happening or what its scope was --
# the start-cycle endpoint refused, because ``review_trigger`` was not a field it had.
#
# Shared rather than copied into three field-spec dicts, on the lesson the grouped
# option-label helper taught: four copies existed, one of them carried something the
# others did not, and a status vocabulary renamed in Admin displayed by its stored
# value on every screen but one.
# The brief the owner writes before a review starts, and who is to do it by when.
# Held here rather than in the console, which is where both of these lived: a list of
# field keys in JavaScript is a second definition of the form, and it drifts the first
# time a field is renamed in config.
REVIEW_BRIEF_FIELDS = ("review_trigger", "review_scope", "peer_reviewer",
                       "review_due_date")

# Shown only when the trigger is a new version: the three documents that go stale
# together, so the reviewer is not reading last version's write-up against this one.
NEW_VERSION_CHECKLIST = ("review_docs_updated", "review_sensitivities_updated",
                         "review_test_docs_updated")

REVIEW_FIELD_SPECS = {
    # Stage 1: the owner says what this review is for before anyone starts it. A
    # reviewer handed a record and no brief writes the review they imagine is wanted;
    # the scope is where the owner says what has changed and what they want looked at.
    "review_scope": {"label": "Scope of this review", "type": "textarea", "group": "Review"},
    "review_trigger": {
        "label": "Why this review", "type": "choice",
        "options": VALID_REVIEW_TRIGGERS, "group": "Review",
    },
    "review_due_date": {"label": "Expected completion", "type": "date", "group": "Review"},
    # The new-version checklist. Shown only when the trigger is a new version: the owner
    # confirms the three documents that go stale together have been brought up to date
    # and loaded, so the reviewer is not reading last version's write-up against this
    # version's record.
    "review_docs_updated": {
        "label": "Model documentation updated and loaded", "type": "choice",
        "options": ("Yes", "No"), "group": "Review",
    },
    "review_sensitivities_updated": {
        "label": "Sensitivities updated and loaded", "type": "choice",
        "options": ("Yes", "No"), "group": "Review",
    },
    "review_test_docs_updated": {
        "label": "Test documentation updated and loaded", "type": "choice",
        "options": ("Yes", "No"), "group": "Review",
    },
}
