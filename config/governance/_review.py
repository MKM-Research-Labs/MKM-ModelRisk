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
