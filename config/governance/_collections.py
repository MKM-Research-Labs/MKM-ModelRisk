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
from config.governance._assessments import (  # noqa: F401 (re-export)
    ASSESSMENT_COLLECTION_SPECS, EVALUATIONS_COLLECTION, FAIRNESS_COLLECTION,
    MONITORING_COLLECTION,
    VALID_EVALUATION_KINDS, VALID_EVALUATION_VERDICTS)
from config.governance._inventory import VALID_RAG_RATINGS
from config.governance._signoff_collections import (  # noqa: F401 (re-export)
    SIGNOFF_COLLECTION_SPECS, SIGNOFF_COLLECTIONS, SIGNOFF_HISTORY_COLLECTION,
    SIGNOFF_REQUESTS_COLLECTION, VALID_SIGNOFF_KINDS, VALID_SIGNOFF_OUTCOME,
    VALID_SIGNOFF_REQUEST_STATUS)
from config.governance._review import (REVIEW_COLLECTION_SPECS,
                                       VALID_REVIEWER_VERDICTS)

# Closed value sets used by structured collections.
# Status vocabularies held as admin lists (see LIFECYCLE_STAGE_LIST in _inventory
# for the shape): the record stores a stable value, a screen shows a label, and
# only the label is the institution's to change.
IMPACT_LIST = "impact_level"
PRIORITY_LIST = "priority_level"
REMEDIATION_STATUS_LIST = "remediation_status"
VQ_STATUS_LIST = "vq_status"

VALID_IMPACT = ("Low", "Medium", "High")
VALID_PRIORITY = ("Low", "Medium", "High")
VALID_REMEDIATION_STATUS = ("Open", "In Progress", "Closed")
VALID_ACTION_STATUS = ("Open", "Closed")
# The one status that settles a remediation step. Named so that "how much is still
# outstanding" is decided in one place: a tab badge and a committee report must not
# disagree about whether a step still counts.
CLOSED_REMEDIATION_STATUS = "Closed"
VALID_VQ_STATUSES = (
    "Addressed", "Partially Addressed", "Not Addressed", "Not Applicable",
)
VALID_DEPENDENCY_DIRECTIONS = ("upstream", "downstream")
# Which way an item moves when its order is changed. Order is meaningful in some
# collections — the review questionnaire is asked in the order it is listed — so it
# is changed by a recorded move rather than by a position field somebody has to
# keep consistent.
VALID_MOVE_DIRECTIONS = ("up", "down")
# The per-model collection of declared model-to-model dependencies. Named once so
# the derivation (which reads it to build the 'string of pearls') and the
# declaration-time acyclicity guard agree on the key.
DEPENDENCIES_COLLECTION = "dependencies"
# The per-model list of data sources (feeds) the model pulls its inputs from. A
# model may draw on several; two models that list the same source are joined by
# the 'shares a source' edge on the neighbourhood view. Field-level detail (which
# fields come from which source) can be layered on later without breaking this —
# for now it is the recognition that the model pulls data from these sources.
DATA_SOURCES_COLLECTION = "data_sources"
# Fairness and bias assessment, one row per attribute assessed. Shared across the
# model inventory, ML Applications and AI Systems: "who could this disadvantage" is
# the same question of all three, and asking it three different ways would make the
# estate-wide answer unobtainable.

# What a test actually returned, one row per evaluation run. Shared across the model
# inventory, ML Applications and AI Systems: "has this been measured, and what did it
# say" is the same question of all three.
#
# This is what turns ``benchmark_tests: Yes`` into evidence. That flag records that
# testing happened and nothing else -- not what was tested, not against what, not what
# it found, not when. A committee cannot challenge a Yes.

# Whether a feed comes from inside the institution or from a third party. The
# distinction is a governance one, not a label: an EXTERNAL source is a third-party
# dependency, so the questions that follow are provenance, licensing, and whether the
# fit could be reproduced if the feed changed or went away. An internal one raises
# none of those. Blank means nobody has said yet, which is not the same as internal.
VALID_DATA_SOURCE_KINDS = ("Internal", "External")
# How sensitive the data in a feed is. A property of the FEED rather than of any one
# record that consumes it, for the same reason ``kind`` is: reclassifying a feed
# should happen once, not once per model that happens to read it.
#
# Ordered by how much it would matter if it were exposed, so a reader can see at a
# glance which end of the list a source sits at. Blank means nobody has classified it,
# which is not the same as "not sensitive" -- and is the finding.
VALID_DATA_SENSITIVITY = ("Public", "Internal", "Confidential",
                          "Personal data (PII)", "Regulated client data")
# Whether this feed may leave the institution at all. The question AIR-RC-001 turns
# on, and it has to be answerable about the FEED before it can be answered about any
# system that sends it somewhere: a record saying "we send confidential data to a
# hosted model" means nothing until somebody has said whether that feed was ever
# allowed out.
VALID_DATA_EGRESS = ("May not leave the institution",
                     "May leave under contract",
                     "May leave freely")
# A version's place in the development lifecycle. "New" = a fresh version just
# cut; "Being Enhanced" = active development against it; "No New Development" =
# stable, still in use but frozen; "Marked for Removal" = scheduled to retire.
# Admin-managed, like every other status vocabulary: an institution names the arc its
# own versions move through. Held here beside the field it serves.
VERSION_LIFECYCLE_LIST = "version_lifecycle"
VALID_VERSION_LIFECYCLE = (
    "New", "Being Enhanced", "No New Development", "Marked for Removal",
)
# Stakeholder-informed flags on an Operational Failure Event (W4b). Each is an
# independent Yes/No because in practice an event may inform one and not the
# other (e.g. internal noise that didn't reach the client).
VALID_INFORMED = ("Yes", "No")
# The RACI accountabilities and the roles that hold them live in ``_raci``: the
# roles are an admin list, and DEFAULT_RACI is only what that list is seeded with.
from config.governance._raci import (DEFAULT_RACI, RACI_ROLE_LIST,  # noqa: E402,F401
                                     VALID_RACI_CODES)
# An operational event's MRC review state. "Pending" = raised on the product,
# awaiting a committee; "Received" = the MRC reviewed and formally received it.
VALID_EVENT_REVIEW_STATUS = ("Pending", "Received")
# A queued sign-off request (owner-raised) as it moves from raised to
# attached-to-a-meeting. "Pending" = raised, awaiting a meeting of the target
# MRC; "Attached" = pulled onto a meeting agenda; "Withdrawn" = cancelled.
# The subset that is still in flight — raised and not yet settled either way. A
# subject with one of these in its queue reads as "pending sign-off" rather than
# as a draft, wherever that lifecycle is derived.
ACTIVE_SIGNOFF_REQUEST_STATUS = ("Pending", "Attached")

# Structured collections on a model: arrays of items. Each item is built from the
# field specs below; ``id_prefix`` seeds generated item ids (e.g. AS-001). One
# generic add/update/remove command set serves every collection.
COLLECTION_SPECS = {
    **SIGNOFF_COLLECTION_SPECS,
    **REVIEW_COLLECTION_SPECS,
    "assumptions": {"label": "Assumptions", "id_prefix": "AS", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT,
         "reference": IMPACT_LIST},
        {"key": "monitoring", "label": "Monitoring", "type": "text"},
        {"key": "mitigation", "label": "Mitigation", "type": "text"},
    ]},
    "limitations": {"label": "Limitations", "id_prefix": "LM", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT,
         "reference": IMPACT_LIST},
        {"key": "monitoring_trigger", "label": "Monitoring trigger", "type": "text"},
        {"key": "compensating_control", "label": "Compensating control", "type": "text"},
    ]},
    # Known model weaknesses — a lighter register than Limitations (no monitoring
    # / compensating control), sitting alongside it on the Limitations tab.
    "model_weaknesses": {"label": "Model weaknesses", "id_prefix": "MW", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT,
         "reference": IMPACT_LIST},
    ]},
    "validation_questions": {"label": "Validation questions", "id_prefix": "VQ", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text"},
        {"key": "question", "label": "Question", "type": "text", "required": True},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_VQ_STATUSES,
         "reference": VQ_STATUS_LIST},
        {"key": "rationale", "label": "Rationale", "type": "text"},
        {"key": "evidence", "label": "Evidence", "type": "text"},
        # The reviewer's side of the same question. Stamped by the endpoint that
        # records the verdict, never typed: an attribution the browser supplies is
        # not evidence of anything.
        {"key": "reviewer_verdict", "label": "Reviewer", "type": "choice",
         "options": VALID_REVIEWER_VERDICTS},
        {"key": "reviewer_comment", "label": "Reviewer comment", "type": "text"},
        {"key": "reviewed_by", "label": "Reviewed by", "type": "text", "hidden": True},
        {"key": "reviewed_at", "label": "Reviewed at", "type": "text", "hidden": True},
    ]},
    "remediation_steps": {"label": "Remediation", "id_prefix": "RM", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text", "reference": "people"},
        {"key": "priority", "label": "Priority", "type": "choice", "options": VALID_PRIORITY,
         "reference": PRIORITY_LIST},
        {"key": "due_date", "label": "Due date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_REMEDIATION_STATUS,
         "reference": REMEDIATION_STATUS_LIST},
    ]},
    "dependencies": {"label": "Model dependencies", "id_prefix": "DEP", "fields": [
        {"key": "direction", "label": "Direction", "type": "choice",
         "options": VALID_DEPENDENCY_DIRECTIONS, "required": True},
        {"key": "model_id", "label": "Related model", "type": "text",
         "reference": "model_inventory", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    # Data sources (feeds) the model pulls its inputs from. ``data_source`` is a
    # strict reference to the admin Data Source list, so "these two models share a
    # source" matches on a defined id, never on free-text spelling.
    DATA_SOURCES_COLLECTION: {"label": "Data sources", "id_prefix": "SRC", "fields": [
        {"key": "data_source", "label": "Data source", "type": "text",
         "reference": "data_source", "strict_reference": True, "required": True},
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
        # Picked from the admin RACI role list. The shipped roles stand in only while
        # that list is empty; an entry recorded under a role since removed keeps it.
        {"key": "role", "label": "Role", "type": "choice", "required": True,
         "options": tuple(role for _code, role in DEFAULT_RACI),
         "reference": RACI_ROLE_LIST},
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

# The measured-about-a-record collections, folded in so COLLECTION_SPECS stays the one
# table every record type reads. They live in their own module (see _assessments) but
# there is no second place to look them up.
COLLECTION_SPECS.update(ASSESSMENT_COLLECTION_SPECS)
# The record's own history — versions and changes — merged the same way.
from config.governance._history_collections import (  # noqa: E402
    HISTORY_COLLECTION_SPECS)
COLLECTION_SPECS.update(HISTORY_COLLECTION_SPECS)
