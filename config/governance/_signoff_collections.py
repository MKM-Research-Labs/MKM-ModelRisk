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
"""The committee's own two collections on a subject (coding rule R1).

A queue of what has been asked of the MRC, and the record of what it decided. They
sit apart from a model's other registers because they are the committee's machinery
rather than the owner's account of the model — and because both are exempt from the
read-only-when-hibernated rule, a reactivate being raised on a subject that is
hibernated at the time.
"""
from __future__ import annotations

from config.governance._committee_context import SIGNOFF_REQUEST_CONTEXT_FIELDS
from config.governance._inventory import VALID_RAG_RATINGS

# Named here with the collections they key, so the two names and the two specs
# travel together.
SIGNOFF_REQUESTS_COLLECTION = "signoff_requests"
SIGNOFF_HISTORY_COLLECTION = "signoff_history"
# The committee's own machinery: the queue it works and the record of what it
# decided. Both are exempt from a subject's read-only-when-hibernated rule — a
# decision must be recordable even when it is the decision that hibernated the
# subject, and a reactivate is raised and minuted on a subject still hibernated.
SIGNOFF_COLLECTIONS = (SIGNOFF_REQUESTS_COLLECTION, SIGNOFF_HISTORY_COLLECTION)

# A queued request as it moves from raised to attached-to-a-meeting. "Pending" =
# raised, awaiting a meeting of the target MRC; "Attached" = pulled onto an agenda.
VALID_SIGNOFF_REQUEST_STATUS = ("Pending", "Attached", "Completed", "Rejected", "Withdrawn")
# "owner" ratifies a change of model owner. The new owner takes the record
# immediately — somebody has to answer for the model today — and the committee
# ratifies the appointment afterwards, so the request carries both names.
VALID_SIGNOFF_KINDS = ("rag", "retire", "reactivate", "handoff", "owner")
# The committee's decision. "Revoked" is retained so a historic log still reads;
# it can no longer be created.
VALID_SIGNOFF_OUTCOME = ("Approved", "Rejected", "Revoked")

SIGNOFF_COLLECTION_SPECS = {
    # W4c — audit of the decisions the MRC took. One entry per decision; each
    # records what was decided, which meeting rubber-stamped it, and — for a
    # rating decision — where the rating came from and went to. ``kind`` mirrors
    # the request it settles, so the rating fields are only meaningful for "rag".
    SIGNOFF_HISTORY_COLLECTION: {"label": "Sign-off history", "id_prefix": "SO", "fields": [
        {"key": "date", "label": "Date", "type": "date", "required": True},
        {"key": "kind", "label": "Kind", "type": "choice",
         "options": VALID_SIGNOFF_KINDS, "required": True},
        {"key": "outcome", "label": "Outcome", "type": "choice", "options": VALID_SIGNOFF_OUTCOME},
        {"key": "from_rating", "label": "From", "type": "choice", "options": VALID_RAG_RATINGS},
        {"key": "to_rating", "label": "To", "type": "choice", "options": VALID_RAG_RATINGS},
        {"key": "meeting_id", "label": "Meeting", "type": "text"},
        {"key": "next_review_date", "label": "Next review", "type": "date"},
        {"key": "note", "label": "Note", "type": "text"},
        {"key": "from_owner", "label": "Previous owner", "type": "text"},
        {"key": "to_owner", "label": "New owner", "type": "text"},
    ]},
    # The owner-raised sign-off queue: a request is routed to the model's
    # responsible MRC (``target_mrc``) and waits as Pending until a meeting of
    # that committee is scheduled, at which point it is pulled onto the agenda
    # and marked Attached (recording the meeting + agenda item it landed on).
    # One queue carries every kind of decision the committee ratifies, so
    # ``kind`` says what is being asked and the kind-specific fields (e.g.
    # ``proposed_rag`` for a rating) are only meaningful for that kind.
    SIGNOFF_REQUESTS_COLLECTION: {"label": "Sign-off requests", "id_prefix": "SR", "fields": [
        {"key": "kind", "label": "Kind", "type": "choice",
         "options": VALID_SIGNOFF_KINDS, "required": True},
        {"key": "proposed_rag", "label": "Proposed RAG", "type": "choice",
         "options": VALID_RAG_RATINGS},
        {"key": "target_mrc", "label": "Target MRC", "type": "text"},
        {"key": "status", "label": "Status", "type": "choice",
         "options": VALID_SIGNOFF_REQUEST_STATUS},
        {"key": "meeting_id", "label": "Meeting", "type": "text"},
        {"key": "agenda_item_id", "label": "Agenda item", "type": "text"},
        {"key": "note", "label": "Note", "type": "text"},
        {"key": "from_owner", "label": "Previous owner", "type": "text"},
        {"key": "to_owner", "label": "New owner", "type": "text"},
        # An AI System's place on the grid when the request was raised (spec §3.3).
        *SIGNOFF_REQUEST_CONTEXT_FIELDS,
    ]},
}
