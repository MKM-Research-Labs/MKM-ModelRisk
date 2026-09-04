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
"""What a meeting IS: MRC settings, branding and meeting field specs (rule R1).

What a meeting CONTAINS — its agenda, minutes, participants, models in scope and
actions — is ``_mrc_collections``. Import ``MRC_COLLECTION_SPECS`` from
``config.governance``, which re-exports both halves.
"""
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
# An agreed action is open the moment the committee agrees it — nobody minutes an
# action that is already closed, so the form should not ask.
DEFAULT_ACTION_STATUS = "Open"
# The owner asks; the committee decides. An owner who believes an action is done moves
# it here, and it stays here until an MRC ratifies the closure — the same shape as a
# proposed role or a draft risk policy. Nobody settles their own obligation.
REQUESTED_CLOSURE_ACTION_STATUS = "Closure requested"
# The one status that settles an action. Named so that "what is still outstanding"
# is decided in one place: the model's MRC linkage and the committee's own review of
# actions must not disagree about whether an action still counts.
CLOSED_ACTION_STATUS = "Closed"
VALID_ACTION_STATUSES = (DEFAULT_ACTION_STATUS, REQUESTED_CLOSURE_ACTION_STATUS,
                         CLOSED_ACTION_STATUS)
# An action outlives the meeting that agreed it: it is worked between meetings and
# closed at a later one, so these two fields stay editable after the meeting is sealed.
# Everything else about an action — its wording, its owners, the model it concerns — is
# part of what the committee is recorded as having agreed, and seals with the minutes.
# Nothing already issued changes: the minutes PDF is generated once, at close.
ACTION_LIVE_FIELDS = ("status", "updates")
# Named once so the rule that gates closure, the API that ratifies it and the read
# views all agree on which collection carries the committee's actions.
ACTIONS_COLLECTION = "actions"
# Where an update's supporting file is stored. Evidence stays with the action rather
# than being filed on the model: a model-side documentation category would make the
# completeness audit expect closure evidence on every model on the register.
ACTION_EVIDENCE_SCOPE = "action_evidence"
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
