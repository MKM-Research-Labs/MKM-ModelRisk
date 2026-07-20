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
# The per-model collection of declared model-to-model dependencies. Named once so
# the derivation (which reads it to build the 'string of pearls') and the
# declaration-time acyclicity guard agree on the key.
DEPENDENCIES_COLLECTION = "dependencies"
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
# The four RACI accountabilities, defining who does what for a product's use of
# models in production (the RACI operating model, held at the product level).
VALID_RACI_CODES = ("Responsible", "Accountable", "Consulted", "Informed")
# An operational event's MRC review state. "Pending" = raised on the product,
# awaiting a committee; "Received" = the MRC reviewed and formally received it.
VALID_EVENT_REVIEW_STATUS = ("Pending", "Received")
# A queued sign-off request (owner-raised) as it moves from raised to
# attached-to-a-meeting. "Pending" = raised, awaiting a meeting of the target
# MRC; "Attached" = pulled onto a meeting agenda; "Withdrawn" = cancelled.
VALID_SIGNOFF_REQUEST_STATUS = ("Pending", "Attached", "Completed", "Rejected", "Withdrawn")
# What a sign-off request asks the committee to ratify. One queue serves them all
# so a committee has a single approvals list rather than one per decision type.
# "rag" proposes a new risk rating; "retire" hibernates the subject (it drops out
# of the active inventory); "reactivate" brings a hibernated subject back.
VALID_SIGNOFF_KINDS = ("rag", "retire", "reactivate", "handoff")
# Named once so the domain rules and the routing agree on it. A hibernated
# subject is read-only *except* for this queue: a reactivate request has to be
# raised on the very subject it would bring back, so exempting it is what keeps
# hibernation reversible rather than a one-way trip.
SIGNOFF_REQUESTS_COLLECTION = "signoff_requests"
SIGNOFF_HISTORY_COLLECTION = "signoff_history"
# The committee's own machinery: the queue it works and the record of what it
# decided. Both are exempt from a subject's read-only-when-hibernated rule —
# a decision must be recordable even when it is the decision that hibernated the
# subject, and a reactivate is raised and minuted on a subject that is still
# hibernated at the time.
SIGNOFF_COLLECTIONS = (SIGNOFF_REQUESTS_COLLECTION, SIGNOFF_HISTORY_COLLECTION)
# The committee's decision on a sign-off request.
VALID_SIGNOFF_OUTCOME = ("Approved", "Rejected", "Revoked")

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
        {"key": "model_id", "label": "Related model", "type": "text",
         "reference": "model_inventory", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    # The field lineage of a model-to-model handoff: one item per field that
    # crosses the edge, stated as a *pair* — the provider's (giver's) field mapped
    # to the consumer's (receiver's) field, so the interoperability template's
    # provider→consumer handover is captured field by field. Lives on a
    # ModelHandoff aggregate, not a model — the handoff is what the MRC reviews.
    "field_lineage": {"label": "Field lineage", "id_prefix": "FL", "fields": [
        {"key": "provider_field", "label": "Provider field", "type": "text", "required": True},
        {"key": "provider_type", "label": "Provider type", "type": "text"},
        {"key": "provider_units", "label": "Provider units", "type": "text"},
        {"key": "consumer_field", "label": "Consumer field", "type": "text", "required": True},
        {"key": "consumer_type", "label": "Consumer type", "type": "text"},
        {"key": "consumer_units", "label": "Consumer units", "type": "text"},
        {"key": "note", "label": "Mapping / compatibility note", "type": "text"},
    ]},
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
        # MRC review of the event (W4b feed-up). Set by the committee when it
        # receives the event at a meeting; not edited on the add form.
        {"key": "mrc_status", "label": "MRC status", "type": "choice",
         "options": VALID_EVENT_REVIEW_STATUS, "hidden": True},
        {"key": "review_comments", "label": "MRC comments", "type": "text", "hidden": True},
        {"key": "mrc_meeting", "label": "Received at meeting", "type": "text", "hidden": True},
    ]},
    # The RACI operating model for a product: who is Responsible / Accountable /
    # Consulted / Informed for the product's use of models in production. Held at
    # the product level (a product uses models in production); the per-event R/A/C/I
    # on operational_failure_events records who acted on a specific incident.
    "raci_roles": {"label": "RACI roles", "id_prefix": "RC", "fields": [
        {"key": "role", "label": "Role", "type": "text", "required": True},
        {"key": "raci", "label": "RACI", "type": "choice",
         "options": VALID_RACI_CODES, "required": True},
        {"key": "assigned_to", "label": "Assigned to", "type": "text", "reference": "people"},
        {"key": "backup", "label": "Backup", "type": "text", "reference": "people"},
        {"key": "description", "label": "Description", "type": "text"},
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
