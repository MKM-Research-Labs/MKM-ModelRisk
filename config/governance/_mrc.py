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
"""MRC settings, branding and meeting field specs (coding rule R1)."""
from config.governance._inventory import VALID_RAG_RATINGS

# --- MRC settings & branding (header for the console and Meeting Pack PDF) ---
# Address, handbook reference and framework were dropped as not required; the
# ToR document (uploaded separately) carries that detail. What remains is the
# institution name, the chair and the meeting cadence.
VALID_FREQUENCY = ("Monthly", "Quarterly", "Semi-annual", "Annual")
MRC_SETTINGS_SPECS = (
    {"key": "org_name", "label": "Organisation name", "type": "text"},
    {"key": "chair", "label": "Chair", "type": "text"},
    {"key": "frequency", "label": "Frequency", "type": "choice", "options": VALID_FREQUENCY},
)
MRC_SETTINGS_KEYS = tuple(spec["key"] for spec in MRC_SETTINGS_SPECS)
MRC_SETTINGS_DEFAULTS = {
    "frequency": "Quarterly",
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
# the org scope (company/division/department). All five of those are derived
# on read from the MRC entry; they're not stored on the meeting.
MEETING_FIELD_SPECS = {
    "mrc": {"label": "MRC", "type": "text", "reference": "mrc"},
    "title": {"label": "Title", "type": "text"},
    "date": {"label": "Date", "type": "date"},
    "time": {"label": "Time", "type": "text"},
    "location": {"label": "Location", "type": "text"},
    "status": {"label": "Status", "type": "choice", "options": VALID_MEETING_STATUSES},
}
# ``company`` is not a meeting field — the institution is a singleton
# (see MRC settings org_name). Division/department are derived from the MRC.
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
        # A manually-added agenda item is just Title / Description / Presenter
        # (plus an optional document). Status + the sign-off routing fields are
        # set by the workflow, not the add form, so they are hidden from it.
        {"key": "status", "label": "Status", "type": "choice",
         "options": VALID_AGENDA_STATUS, "hidden": True},
        {"key": "document_filename", "label": "Document file", "type": "text", "hidden": True},
        {"key": "document_original_name", "label": "Document", "type": "text", "hidden": True},
        # W4c — sign-off agenda items link back to a model/product and carry the
        # proposed RAG. When Approved at the meeting, the subject's official
        # rag_rating snaps to proposed_rag. Set by request-signoff, not by hand.
        {"key": "subject_model_id", "label": "Subject model",
         "type": "text", "reference": "model_inventory", "hidden": True},
        {"key": "subject_product_id", "label": "Subject product", "type": "text", "hidden": True},
        {"key": "proposed_rag", "label": "Proposed RAG",
         "type": "choice", "options": VALID_RAG_RATINGS, "hidden": True},
        # Phase MRC-4: back-pointers on an escalation-child item — the child
        # (on the parent MRC's meeting) knows which item it was escalated from.
        # Not shown on the add form.
        {"key": "escalated_from_meeting_id", "label": "Escalated from meeting",
         "type": "text", "hidden": True},
        {"key": "escalated_from_agenda_id", "label": "Escalated from item",
         "type": "text", "hidden": True},
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
        {"key": "text", "label": "Minutes", "type": "textarea"},
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
        # Per-model analysis document uploaded for this meeting. Hidden metadata;
        # the Models tab renders an upload/download control per in-scope model.
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
