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
"""What a meeting CONTAINS: the structured collections on an MRC meeting.

Split out of ``_mrc.py``, which holds what a meeting IS — its own fields, its
statuses, the settings and branding around it. These are the lists it carries:
the agenda, the minutes, who attended, the models in scope, the actions.

The seam is not a line count. The two halves change for different reasons: a
meeting gains a field when the committee records something new about the meeting
itself; these gain one when a new kind of record can be decided about, which is
what a fourth and fifth subject in the sign-off routing did.
"""
from config.governance._collections import VALID_SIGNOFF_KINDS
from config.governance._inventory import VALID_RAG_RATINGS
from config.governance._mrc import (DEFAULT_ACTION_STATUS, VALID_ACTION_STATUSES,
                                    VALID_AGENDA_STATUS, VALID_ANALYSIS_STATUS,
                                    VALID_PARTICIPANT_STATUS)

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
        # request routing, not by hand. One subject field per register below.
        {"key": "subject_model_id", "label": "Subject model", "type": "text",
         "reference": "model_inventory", "hidden": True},
        {"key": "subject_product_id", "label": "Subject product", "type": "text", "hidden": True},
        {"key": "subject_handoff_id", "label": "Subject handoff", "type": "text", "hidden": True},
        {"key": "subject_ml_application_id", "label": "Subject ML Application", "type": "text", "hidden": True},
        {"key": "subject_ai_system_id", "label": "Subject AI System", "type": "text", "hidden": True},
        # An "event review" agenda item links to a product's operational-failure
        # event (the event's item id, with subject_product_id naming the product).
        {"key": "subject_event_id", "label": "Subject event", "type": "text", "hidden": True},
        {"key": "signoff_kind", "label": "Sign-off kind", "type": "choice",
         "options": VALID_SIGNOFF_KINDS, "hidden": True},
        {"key": "proposed_rag", "label": "Proposed RAG",
         "type": "choice", "options": VALID_RAG_RATINGS, "hidden": True},
        # An owner ratification: who it was and who it now is, so the committee
        # reads the change on the agenda item rather than opening the model.
        {"key": "from_owner", "label": "Previous owner", "type": "text", "hidden": True},
        {"key": "to_owner", "label": "New owner", "type": "text", "hidden": True},
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
    # reference the record it concerns; the UI renders that (plus the expandable text
    # box) from meeting context. A ratified sign-off auto-creates a minute here.
    #
    # One id field per record type the committee can decide about, and they are
    # mutually exclusive. The list has to hold every subject in the sign-off routing:
    # a minute is written for each ratified decision under the subject's own id, so a
    # record type missing from here cannot be minuted — and because the minute is
    # written inside the approval, the whole decision is refused rather than merely
    # going unrecorded.
    "minutes": {"label": "Minutes", "id_prefix": "MIN", "fields": [
        {"key": "title", "label": "Title", "type": "text", "required": True},
        {"key": "presenter", "label": "Presenter", "type": "text"},
        {"key": "model_id", "label": "Model", "type": "text", "reference": "model_inventory"},
        {"key": "product_id", "label": "Product", "type": "text"},
        {"key": "handoff_id", "label": "Handoff", "type": "text"},
        {"key": "ml_application_id", "label": "ML Application", "type": "text"},
        {"key": "ai_system_id", "label": "AI System", "type": "text"},
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

    # ML Applications in scope for analysis. An ML Application's analysis is presented
    # to the committee exactly as a model's is: same outcome vocabulary, same tabled
    # paper, same basis to proceed. It had none of this until 2026-09-06, so an ML
    # Application could be governed but never actually discussed at a meeting.
    "ml_applications_in_scope": {"label": "ML Applications", "id_prefix": "MLS", "fields": [
        {"key": "ml_application_id", "label": "ML Application", "type": "text", "required": True},
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

    # AI Systems in scope for analysis, on the same footing. Governance of AI is the
    # governance of a model: the same triggers reach the same committee, and being
    # presented for analysis is one of them.
    "ai_systems_in_scope": {"label": "AI Systems", "id_prefix": "AIS", "fields": [
        {"key": "ai_system_id", "label": "AI System", "type": "text", "required": True},
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
    # An agreed action starts from the model it concerns: the model is picked first
    # because that is what the owner tick-boxes default from. An action may be owned
    # by more than one person, so ``owner`` holds a list (a bare string from before
    # this change still reads as a single owner). There is no target date — progress
    # is recorded as dated updates against the action, the same shape a product-owned
    # action already uses.
    "actions": {"label": "Actions", "id_prefix": "A", "fields": [
        {"key": "model_id", "label": "Model", "type": "text", "reference": "model_inventory"},
        {"key": "description", "label": "Action", "type": "text", "required": True},
        {"key": "owner", "label": "Owners", "type": "multichoice", "reference": "people"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_ACTION_STATUSES,
         "default": DEFAULT_ACTION_STATUS},
        {"key": "updates", "label": "Updates", "type": "text", "hidden": True},
    ]},
}


# What a meeting can put in scope for analysis, one entry per governed record type.
#
# Analysis is one of the sign-off triggers, and the triggers are the same for a model,
# an ML Application, an AI System and a Product — so this table has an entry for each
# rather than the endpoints being written out per type. Three copies of the same
# routes had already drifted before it existed: models filed the tabled paper onto the
# record and products did not, and the two batch-set endpoints lived in different
# files.
#
# ``name_field`` is the only genuine difference between them: a Product keeps its name
# under ``product`` and everything else under ``name``.
MEETING_SCOPE = {
    "model": {"collection": "models_in_scope", "id_key": "model_id",
              "url": "models", "name_field": "name",
              "noun": "model", "plural": "models"},
    "product": {"collection": "products_in_scope", "id_key": "product_id",
                "url": "products", "name_field": "product",
                "noun": "product", "plural": "products"},
    "ml_application": {"collection": "ml_applications_in_scope",
                       "id_key": "ml_application_id", "url": "ml-applications",
                       "name_field": "name",
                       "noun": "ML Application", "plural": "ML Applications"},
    "ai_system": {"collection": "ai_systems_in_scope", "id_key": "ai_system_id",
                  "url": "ai-systems", "name_field": "name",
                  "noun": "AI System", "plural": "AI Systems"},
}

# The in-scope collections, for callers that only need the names.
MEETING_SCOPE_COLLECTIONS = tuple(cfg["collection"] for cfg in MEETING_SCOPE.values())

