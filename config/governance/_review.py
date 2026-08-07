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
    {"key": "questions", "label": "The nine questions", "status": "Questions answered"},
    {"key": "weaknesses", "label": "Model weaknesses", "status": "Weaknesses agreed"},
    {"key": "limitations", "label": "Limitations of use", "status": "Limitations agreed"},
    {"key": "monitoring", "label": "Monitoring approach", "status": "Monitoring agreed"},
)
REVIEW_STAGE_KEYS = tuple(stage["key"] for stage in REVIEW_STAGES)
DEFAULT_REVIEW_STATUS = "Not started"
# The status a signed-off review leaves behind. The sign-off itself is not built
# yet; the value is named here so the vocabulary is complete and the workflow has
# somewhere to finish.
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
