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
"""MRC settings, branding and meeting field specs (coding rule R1)."""
from config.governance._collections import VALID_SIGNOFF_KINDS
from config.governance._inventory import VALID_RAG_RATINGS
from config.reporting import (DEFAULT_AUTHOR, DEFAULT_CLASSIFICATION,
                              DEFAULT_LEGAL_NOTICE)

# --- MRC settings & branding (header for the console and Meeting Pack PDF) ---
# Address, handbook reference and framework were dropped as not required; the
# ToR document (uploaded separately) carries that detail. What remains is the
# institution name, the chair and the meeting cadence.
VALID_FREQUENCY = ("Monthly", "Quarterly", "Semi-annual", "Annual")

# The status a closed meeting carries. Named once: the write domain refuses to
# amend a meeting in this state, and the console hides its edit controls.
CLOSED_MEETING_STATUS = "Completed"

# How far ahead the successor meeting is scheduled, per committee frequency.
# Closing a meeting schedules the next one, so a committee that meets on a cycle
# always has its next date on the record rather than in somebody's diary.
MEETING_INTERVAL_MONTHS = {
    "Monthly": 1, "Quarterly": 3, "Semi-annual": 6, "Annual": 12,
}
DEFAULT_INTERVAL_MONTHS = 3
# The wording every generated PDF carries. These are one institution's words, not
# platform constants: the values in ``config/reporting.py`` are only the shipped
# defaults, and an adopter overrides them here (Admin > Misc) rather than editing
# code. Grouped as "misc" so the Admin tab knows which sub-tab shows them.
MISC_SETTINGS_GROUP = "misc"
# Paragraphs of the legal notice are separated by a blank line, so a multi-paragraph
# notice can be typed into (and read back from) one text box.
LEGAL_NOTICE_SEPARATOR = "\n\n"
MRC_SETTINGS_SPECS = (
    {"key": "org_name", "label": "Organisation name", "type": "text"},
    {"key": "chair", "label": "Chair", "type": "text"},
    {"key": "frequency", "label": "Frequency", "type": "choice", "options": VALID_FREQUENCY},
    # Comma-separated taxonomy of model types used to tag external reference
    # documents (the top-level Documents tab). Admin-editable here; the Documents
    # tab reads it to offer tags and to filter.
    {"key": "document_model_types", "label": "Document model types",
     "type": "text", "group": MISC_SETTINGS_GROUP},
    # --- Generated-document wording (title page and running footer) ---
    {"key": "report_classification", "label": "Classification banner", "type": "text",
     "group": MISC_SETTINGS_GROUP},
    {"key": "report_author", "label": "Prepared by", "type": "text",
     "group": MISC_SETTINGS_GROUP},
    {"key": "report_legal_notice", "label": "Legal notice", "type": "textarea",
     "group": MISC_SETTINGS_GROUP},
)
MRC_SETTINGS_KEYS = tuple(spec["key"] for spec in MRC_SETTINGS_SPECS)
MRC_SETTINGS_DEFAULTS = {
    "frequency": "Quarterly",
    # Starter taxonomy for tagging external reference documents; Admin-editable.
    "document_model_types": (
        "Hazard, Pricing, Valuation, Resilience-Credit, Analytics, "
        "Regulatory, Market & Product, Academic & Method"
    ),
    "report_classification": DEFAULT_CLASSIFICATION,
    "report_author": DEFAULT_AUTHOR,
    "report_legal_notice": LEGAL_NOTICE_SEPARATOR.join(DEFAULT_LEGAL_NOTICE),
}

# --- Model Risk Committee (MRC) meetings ---
VALID_MEETING_STATUSES = ("Scheduled", "Completed")
DEFAULT_MEETING_STATUS = "Scheduled"
VALID_ACTION_STATUSES = ("Open", "Closed")
# Phase MRC-4: an agenda item can be "Escalated" instead of Completed when the
# chair can't approve a sign-off and passes it up to a higher-tier MRC.
VALID_AGENDA_STATUS = ("Pending", "Completed", "Escalated", "Rejected")
VALID_PARTICIPANT_STATUS = ("Invited", "Attended", "Apologies", "Declined")
# A model's analysis review at the MRC is a "confirmation to proceed" — that it
# was reviewed, discussed and agreed to proceed — not a formal risk sign-off.
VALID_ANALYSIS_STATUS = ("Pending", "Reviewed — agreed to proceed")

# Model review-status thresholds (days until next review), for the Models tab.
REVIEW_DUE_SOON_DAYS = 30
REVIEW_UPCOMING_DAYS = 90

# Scalar meeting fields (title/date are mandatory at scheduling time). Each
# meeting belongs to an MRC committee (the ``mrc`` binding, chosen from the
# Admin > MRC list) — that committee carries the chair, level and cadence and
# the org scope (company/division / line of business). All five of those are derived
# on read from the MRC entry; they're not stored on the meeting.
MEETING_FIELD_SPECS = {
    "mrc": {"label": "MRC", "type": "text", "reference": "mrc"},
    # The meeting's name, as it heads the console and the Meeting Pack. Editable
    # like the logistics below — a meeting gets renamed when its period or scope
    # turns out differently from what was scheduled — but never to nothing: it is
    # how a committee refers to the meeting in its own minutes.
    "title": {"label": "Title", "type": "text", "required": True},
    "date": {"label": "Date", "type": "date"},
    "time": {"label": "Time", "type": "text"},
    "location": {"label": "Location", "type": "text"},
    "status": {"label": "Status", "type": "choice", "options": VALID_MEETING_STATUSES},
    # Lifecycle flags/artefacts, set by workflow (not the schedule form). Hidden.
    # agenda_locked: the chair/secretary has finalised the agenda for distribution.
    # minutes_filename/name: the generated minutes PDF saved when the meeting closes.
    "agenda_locked": {"label": "Agenda locked", "type": "text", "hidden": True},
    "minutes_filename": {"label": "Minutes file", "type": "text", "hidden": True},
    "minutes_original_name": {"label": "Minutes name", "type": "text", "hidden": True},
}
# ``company`` is not a meeting field — the institution is a singleton
# (see MRC settings org_name). Division / line of business are derived from the MRC.
MEETING_FIELDS = tuple(MEETING_FIELD_SPECS.keys())

# Structured collections on a meeting — same generic engine as the inventory.
# Field names follow the PhysicalRisk MRC schema.
MRC_COLLECTION_SPECS = {
    "agenda": {"label": "Agenda", "id_prefix": "AG", "fields": [
        {"key": "title", "label": "Title", "type": "text", "required": True},
        {"key": "description", "label": "Description", "type": "text"},
        {"key": "presenter", "label": "Presenter", "type": "text"},
        # A standing template item's role (rollcall / minutes_signoff /
        # review_signoff / review_analysis / aob), so the UI renders it bespoke
        # rather than as a generic card. Blank for manually-added items. Hidden.
        {"key": "kind", "label": "Kind", "type": "text", "hidden": True},
        # On the minutes_signoff item: the id of the previous meeting whose minutes
        # are being reviewed/signed off (chosen from prior closed meetings). Hidden.
        {"key": "prev_minutes_meeting", "label": "Previous minutes meeting",
         "type": "text", "hidden": True},
        # A manually-added agenda item is just Title / Description / Presenter
        # (plus an optional document). Status + the sign-off routing fields are
        # set by the workflow, not the add form, so they are hidden from it.
        {"key": "status", "label": "Status", "type": "choice",
         "options": VALID_AGENDA_STATUS, "hidden": True},
        {"key": "document_filename", "label": "Document file", "type": "text", "hidden": True},
        {"key": "document_original_name", "label": "Document", "type": "text", "hidden": True},
        # W4c — sign-off agenda items link back to a model/product and say what
        # the committee is being asked to ratify. ``signoff_kind`` mirrors the
        # queued request's kind (rag / retire / reactivate); it is deliberately
        # not the ``kind`` field above, which marks a standing-template role.
        # Approving a "rag" item snaps the subject's rag_rating to proposed_rag;
        # a "retire" hibernates it; a "reactivate" brings it back. Set by the
        # request routing, not by hand.
        {"key": "subject_model_id", "label": "Subject model",
         "type": "text", "reference": "model_inventory", "hidden": True},
        {"key": "subject_product_id", "label": "Subject product", "type": "text", "hidden": True},
        # A "handoff" sign-off item links back to the model-to-model handoff
        # ("from~to") the committee is being asked to approve. Set by the routing.
        {"key": "subject_handoff_id", "label": "Subject handoff", "type": "text", "hidden": True},
        # An "event review" agenda item links to a product's operational-failure
        # event (the event's item id, with subject_product_id naming the product).
        {"key": "subject_event_id", "label": "Subject event", "type": "text", "hidden": True},
        {"key": "signoff_kind", "label": "Sign-off kind", "type": "choice",
         "options": VALID_SIGNOFF_KINDS, "hidden": True},
        {"key": "proposed_rag", "label": "Proposed RAG",
         "type": "choice", "options": VALID_RAG_RATINGS, "hidden": True},
        # Phase MRC-4: back-pointers on an escalation-child item — the child
        # (on the parent MRC's meeting) knows which item it was escalated from.
        # Not shown on the add form.
        {"key": "escalated_from_meeting_id", "label": "Escalated from meeting",
         "type": "text", "hidden": True},
        {"key": "escalated_from_agenda_id", "label": "Escalated from item",
         "type": "text", "hidden": True},
        # State of the standing "Governance completeness audit" item. The audit is
        # run from the item (scoped to this committee's in-scope models/products),
        # saved as a per-meeting PDF, and re-runnable until the meeting closes:
        # audit_version bumps on each run, the file fields point at the latest PDF,
        # and generated_at/by stamp who last ran it. audit_comfort/note capture the
        # committee's comfort with the outcome. All set by the workflow, not the
        # add form, so hidden. Zero counts are stored as strings (the collection
        # engine keeps field values as text).
        {"key": "audit_version", "label": "Audit version", "type": "text", "hidden": True},
        {"key": "audit_filename", "label": "Audit file", "type": "text", "hidden": True},
        {"key": "audit_original_name", "label": "Audit name", "type": "text", "hidden": True},
        {"key": "audit_generated_at", "label": "Audit generated at", "type": "text", "hidden": True},
        {"key": "audit_generated_by", "label": "Audit generated by", "type": "text", "hidden": True},
        {"key": "audit_entities", "label": "Records audited", "type": "text", "hidden": True},
        {"key": "audit_findings", "label": "Findings", "type": "text", "hidden": True},
        # The committee's free-text notes on the audit outcome, recorded on the
        # item and carried into the minutes.
        {"key": "audit_notes", "label": "Audit notes", "type": "text", "hidden": True},
    ]},
    # Presenter is picked from the meeting's participants and the minute may
    # reference the model or product it concerns; the UI renders both (plus the
    # expandable text box) from meeting context. A model sign-off auto-creates a
    # minute here. model_id/product_id are mutually exclusive.
    "minutes": {"label": "Minutes", "id_prefix": "MIN", "fields": [
        {"key": "title", "label": "Title", "type": "text", "required": True},
        {"key": "presenter", "label": "Presenter", "type": "text"},
        {"key": "model_id", "label": "Model", "type": "text", "reference": "model_inventory"},
        {"key": "product_id", "label": "Product", "type": "text"},
        {"key": "handoff_id", "label": "Handoff", "type": "text"},
        {"key": "text", "label": "Minutes", "type": "textarea"},
        # The agenda item this minute is filed under, so the Minutes tab reads as
        # a walk-through of the agenda. Blank = general/unfiled. Hidden.
        {"key": "agenda_item_id", "label": "Agenda item", "type": "text", "hidden": True},
    ]},
    "participants": {"label": "Participants", "id_prefix": "P", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "organisation", "label": "Organisation", "type": "text"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_PARTICIPANT_STATUS},
    ]},
    "models_in_scope": {"label": "Models", "id_prefix": "MS", "fields": [
        {"key": "model_id", "label": "Model", "type": "text", "required": True},
        # Who presents this model at the meeting (a person from the register).
        {"key": "presenter", "label": "Presenter", "type": "text", "reference": "people"},
        # The MRC's confirmation to proceed on the model's analysis (reviewed,
        # discussed, agreed) plus an optional discussion note. Not a sign-off.
        {"key": "analysis_status", "label": "Analysis outcome", "type": "choice",
         "options": VALID_ANALYSIS_STATUS},
        {"key": "analysis_note", "label": "Analysis note", "type": "text"},
        # What the committee is letting the presenter proceed on the basis of —
        # the conditions/scope of the confirmation to proceed, in the presenter's
        # own terms. Recorded alongside the outcome, distinct from the discussion.
        {"key": "proceed_basis", "label": "Basis to proceed", "type": "text"},
        # The paper tabled for this item: a reference to a document the model
        # already holds, not a copy taken into the meeting. A committee reviews
        # what the model actually has on file, and one document cannot drift from
        # the other. Uploading is done on the model's Docs tab.
        {"key": "analysis_item_id", "label": "Tabled paper", "type": "text", "hidden": True},
        # Retained so meetings that filed their own copy before the change still
        # render and still appear in their pack.
        {"key": "analysis_filename", "label": "Analysis file", "type": "text", "hidden": True},
        {"key": "analysis_original_name", "label": "Analysis name", "type": "text", "hidden": True},
    ]},
    # Products in scope for analysis — the exact mirror of models_in_scope, so the
    # Signoff tab's Analysis section can cover products alongside models.
    "products_in_scope": {"label": "Products", "id_prefix": "PS", "fields": [
        {"key": "product_id", "label": "Product", "type": "text", "required": True},
        {"key": "presenter", "label": "Presenter", "type": "text", "reference": "people"},
        {"key": "analysis_status", "label": "Analysis outcome", "type": "choice",
         "options": VALID_ANALYSIS_STATUS},
        {"key": "analysis_note", "label": "Analysis note", "type": "text"},
        # What the committee is letting the presenter proceed on the basis of —
        # the conditions/scope of the confirmation to proceed, in the presenter's
        # own terms. Recorded alongside the outcome, distinct from the discussion.
        {"key": "proceed_basis", "label": "Basis to proceed", "type": "text"},
        {"key": "analysis_item_id", "label": "Tabled paper", "type": "text", "hidden": True},
        {"key": "analysis_filename", "label": "Analysis file", "type": "text", "hidden": True},
        {"key": "analysis_original_name", "label": "Analysis name", "type": "text", "hidden": True},
    ]},
    "decisions": {"label": "Decisions", "id_prefix": "D", "fields": [
        {"key": "description", "label": "Decision", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "model_id", "label": "Model", "type": "text", "reference": "model_inventory"},
    ]},
    "actions": {"label": "Actions", "id_prefix": "A", "fields": [
        {"key": "description", "label": "Action", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text"},
        {"key": "target_date", "label": "Target date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_ACTION_STATUSES},
        {"key": "model_id", "label": "Model", "type": "text", "reference": "model_inventory"},
    ]},
}

# The standing agenda seeded onto every new MRC meeting, in running order (AOB
# always last). Each item's ``kind`` drives the bespoke per-item UI renderer and
# marks it as a template item, so generic agenda replay (the demo seeder) skips
# these to avoid duplicating what the seeding helper already adds.
STANDING_AGENDA = (
    {"kind": "rollcall", "title": "Rollcall and Confirmation of Quorum",
     "description": "Confirm attendance in the participants panel; the meeting "
                    "may proceed only once quorate."},
    {"kind": "minutes_signoff", "title": "Sign-off of the previous MRM minutes",
     "description": "Proposed by the chair."},
    {"kind": "review_signoff", "title": "Review model sign-off",
     "description": "Risk-rating sign-offs are reviewed in the Models tab (Approvals)."},
    {"kind": "review_analysis", "title": "Review model analysis",
     "description": "Model analyses are reviewed in the Models tab (Analysis) — "
                    "confirmation to proceed and any actions."},
    {"kind": "completeness_audit", "title": "Governance completeness audit",
     "description": "Run and review the completeness audit for the models and "
                    "products in scope for this committee; record the committee's "
                    "notes on the outcome."},
    # Who sits on this committee, and what they are allowed to be. A person's roles
    # decide who may own, validate and approve, so granting them is the committee's
    # decision rather than an administrator's — the same reasoning that sends the risk
    # policy here rather than letting Admin set it directly.
    {"kind": "membership", "title": "Committee membership and roles",
     "description": "Ratify proposed changes to who sits on this committee and the "
                    "roles they hold. Proposed in Admin -> People; a role takes effect "
                    "only once ratified here."},
    {"kind": "aob", "title": "Any Other Business (AOB)", "description": ""},
)
STANDING_AGENDA_KINDS = frozenset(item["kind"] for item in STANDING_AGENDA)
