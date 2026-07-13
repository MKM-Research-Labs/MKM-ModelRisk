# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Structured-collection field specs on a model (coding rule R1)."""
from config.governance._inventory import VALID_RAG_RATINGS

# Closed value sets used by structured collections.
VALID_IMPACT = ("Low", "Medium", "High")
VALID_PRIORITY = ("Low", "Medium", "High")
VALID_REMEDIATION_STATUS = ("Open", "In Progress", "Closed")
VALID_ACTION_STATUS = ("Open", "Closed")
VALID_VQ_STATUSES = (
    "Addressed", "Partially Addressed", "Not Addressed", "Not Applicable",
)
VALID_DEPENDENCY_DIRECTIONS = ("upstream", "downstream")
# A version's place in the development lifecycle. "New" = a fresh version just
# cut; "Being Enhanced" = active development against it; "No New Development" =
# stable, still in use but frozen; "Marked for Removal" = scheduled to retire.
VALID_VERSION_LIFECYCLE = (
    "New", "Being Enhanced", "No New Development", "Marked for Removal",
)
# Stakeholder-informed flags on an Operational Failure Event (W4b). Each is an
# independent Yes/No because in practice an event may inform one and not the
# other (e.g. internal noise that didn't reach the client).
VALID_INFORMED = ("Yes", "No")
# A queued Risk-rating sign-off request (owner-raised) as it moves from raised
# to attached-to-a-meeting. "Pending" = raised, awaiting a meeting of the target
# MRC; "Attached" = pulled onto a meeting agenda; "Withdrawn" = cancelled.
VALID_SIGNOFF_REQUEST_STATUS = ("Pending", "Attached", "Completed", "Rejected", "Withdrawn")
# The committee's decision on a sign-off request.
VALID_SIGNOFF_OUTCOME = ("Approved", "Rejected")

# Structured collections on a model: arrays of items. Each item is built from the
# field specs below; ``id_prefix`` seeds generated item ids (e.g. AS-001). One
# generic add/update/remove command set serves every collection.
COLLECTION_SPECS = {
    "assumptions": {"label": "Assumptions", "id_prefix": "AS", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT},
        {"key": "monitoring", "label": "Monitoring", "type": "text"},
        {"key": "mitigation", "label": "Mitigation", "type": "text"},
    ]},
    "limitations": {"label": "Limitations", "id_prefix": "LM", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT},
        {"key": "monitoring_trigger", "label": "Monitoring trigger", "type": "text"},
        {"key": "compensating_control", "label": "Compensating control", "type": "text"},
    ]},
    # Known model weaknesses — a lighter register than Limitations (no monitoring
    # / compensating control), sitting alongside it on the Limitations tab.
    "model_weaknesses": {"label": "Model weaknesses", "id_prefix": "MW", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT},
    ]},
    "validation_questions": {"label": "Validation questions", "id_prefix": "VQ", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text"},
        {"key": "question", "label": "Question", "type": "text", "required": True},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_VQ_STATUSES},
        {"key": "rationale", "label": "Rationale", "type": "text"},
        {"key": "evidence", "label": "Evidence", "type": "text"},
    ]},
    "version_history": {"label": "Versions", "id_prefix": "V", "fields": [
        {"key": "version", "label": "Version", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "description", "label": "Description", "type": "text"},
        {"key": "author", "label": "Author", "type": "text"},
        {"key": "ref_document", "label": "Reference document", "type": "text"},
        {"key": "lifecycle", "label": "Lifecycle", "type": "choice",
         "options": VALID_VERSION_LIFECYCLE},
    ]},
    "remediation_steps": {"label": "Remediation", "id_prefix": "RM", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text", "reference": "people"},
        {"key": "priority", "label": "Priority", "type": "choice", "options": VALID_PRIORITY},
        {"key": "due_date", "label": "Due date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_REMEDIATION_STATUS},
    ]},
    "change_history": {"label": "Change history", "id_prefix": "CH", "fields": [
        {"key": "version", "label": "Version", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "author", "label": "Author", "type": "text"},
        {"key": "change_type", "label": "Type", "type": "text"},
        {"key": "description", "label": "Description", "type": "text"},
    ]},
    "dependencies": {"label": "Model dependencies", "id_prefix": "DEP", "fields": [
        {"key": "direction", "label": "Direction", "type": "choice",
         "options": VALID_DEPENDENCY_DIRECTIONS, "required": True},
        {"key": "model_id", "label": "Related model", "type": "text", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    # W4c — audit of RAG sign-offs approved by MRC. One entry per approved
    # transition; each records where the change came from, what it was, and
    # which meeting rubber-stamped it.
    "rag_signoff_history": {"label": "Sign-off history", "id_prefix": "SO", "fields": [
        {"key": "date", "label": "Date", "type": "date", "required": True},
        {"key": "outcome", "label": "Outcome", "type": "choice", "options": VALID_SIGNOFF_OUTCOME},
        {"key": "from_rating", "label": "From", "type": "choice", "options": VALID_RAG_RATINGS},
        {"key": "to_rating", "label": "To", "type": "choice",
         "options": VALID_RAG_RATINGS, "required": True},
        {"key": "meeting_id", "label": "Meeting", "type": "text"},
        {"key": "next_review_date", "label": "Next review", "type": "date"},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    # The owner-raised sign-off queue: a request is routed to the model's
    # responsible MRC (``target_mrc``) and waits as Pending until a meeting of
    # that committee is scheduled, at which point it is pulled onto the agenda
    # and marked Attached (recording the meeting + agenda item it landed on).
    "rag_signoff_requests": {"label": "Sign-off requests", "id_prefix": "SR", "fields": [
        {"key": "proposed_rag", "label": "Proposed RAG", "type": "choice",
         "options": VALID_RAG_RATINGS, "required": True},
        {"key": "target_mrc", "label": "Target MRC", "type": "text"},
        {"key": "status", "label": "Status", "type": "choice",
         "options": VALID_SIGNOFF_REQUEST_STATUS},
        {"key": "meeting_id", "label": "Meeting", "type": "text"},
        {"key": "agenda_item_id", "label": "Agenda item", "type": "text"},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    # W4b — Operational Failure Events: post-mortems of incidents touching the
    # model, with RACI (Responsible / Accountable / Consulted / Informed). The
    # Stakeholders leg ("Informed") is split into Client + Senior management so
    # each can be toggled independently.
    "operational_failure_events": {"label": "Events", "id_prefix": "EV", "fields": [
        {"key": "date", "label": "Event date", "type": "date", "required": True},
        {"key": "description", "label": "What happened", "type": "text", "required": True},
        {"key": "remediation", "label": "Remediation", "type": "text"},
        {"key": "responsible", "label": "Responsible (Operational)",
         "type": "text", "reference": "people"},
        {"key": "accountable", "label": "Accountable (Model owner)",
         "type": "text", "reference": "people"},
        {"key": "consulted", "label": "Consulted (MRC)",
         "type": "text", "reference": "people"},
        {"key": "informed_client", "label": "Informed: Client",
         "type": "choice", "options": VALID_INFORMED},
        {"key": "informed_senior_mgmt", "label": "Informed: Senior management",
         "type": "choice", "options": VALID_INFORMED},
    ]},
    # Outstanding action items owned by the model — the MRC revisits and updates
    # these at committee level. Each action carries a history of dated updates to
    # its expected completion (the ``updates`` list, rendered bespoke); the
    # top-level target_date/status track the latest update.
    "actions": {"label": "Actions", "id_prefix": "ACT", "fields": [
        {"key": "description", "label": "Action", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text", "reference": "people"},
        {"key": "target_date", "label": "Target date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_ACTION_STATUS},
        {"key": "raised_meeting", "label": "Raised at", "type": "text", "hidden": True},
        {"key": "updates", "label": "Updates", "type": "text", "hidden": True},
    ]},
}
