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

# --- MRC settings & branding (header for the console and Meeting Pack PDF) ---
VALID_FREQUENCY = ("Monthly", "Quarterly", "Semi-annual", "Annual")
MRC_SETTINGS_SPECS = (
    {"key": "org_name", "label": "Organisation name", "type": "text"},
    {"key": "org_address", "label": "Address", "type": "text"},
    {"key": "chair", "label": "Chair", "type": "text"},
    {"key": "model_owner", "label": "Model owner", "type": "text"},
    {"key": "frequency", "label": "Frequency", "type": "choice", "options": VALID_FREQUENCY},
    {"key": "handbook_reference", "label": "Handbook reference", "type": "text"},
    {"key": "framework", "label": "Framework", "type": "text"},
)
MRC_SETTINGS_KEYS = tuple(spec["key"] for spec in MRC_SETTINGS_SPECS)
MRC_SETTINGS_DEFAULTS = {
    "framework": "MKM Research Labs Model Risk Governance",
    "frequency": "Quarterly",
}

# --- Model Risk Committee (MRC) meetings ---
VALID_MEETING_STATUSES = ("Scheduled", "Completed")
DEFAULT_MEETING_STATUS = "Scheduled"
VALID_ACTION_STATUSES = ("Open", "Closed")
VALID_AGENDA_STATUS = ("Pending", "Completed")
VALID_PARTICIPANT_STATUS = ("Invited", "Attended", "Apologies", "Declined")

# Model review-status thresholds (days until next review), for the Models tab.
REVIEW_DUE_SOON_DAYS = 30
REVIEW_UPCOMING_DAYS = 90

# Scalar meeting fields (title/date are mandatory at scheduling time).
MEETING_FIELD_SPECS = {
    "title": {"label": "Title", "type": "text"},
    "date": {"label": "Date", "type": "date"},
    "time": {"label": "Time", "type": "text"},
    "location": {"label": "Location", "type": "text"},
    "chair": {"label": "Chair", "type": "text", "reference": "people"},
    "status": {"label": "Status", "type": "choice", "options": VALID_MEETING_STATUSES},
}
MEETING_FIELDS = tuple(MEETING_FIELD_SPECS.keys())

# Structured collections on a meeting — same generic engine as the inventory.
# Field names follow the PhysicalRisk MRC schema.
MRC_COLLECTION_SPECS = {
    "agenda": {"label": "Agenda", "id_prefix": "AG", "fields": [
        {"key": "title", "label": "Title", "type": "text", "required": True},
        {"key": "description", "label": "Description", "type": "text"},
        {"key": "presenter", "label": "Presenter", "type": "text"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_AGENDA_STATUS},
    ]},
    "minutes": {"label": "Minutes", "id_prefix": "MIN", "fields": [
        {"key": "title", "label": "Title", "type": "text", "required": True},
        {"key": "presenter", "label": "Presenter", "type": "text"},
        {"key": "text", "label": "Minutes", "type": "text"},
    ]},
    "participants": {"label": "Participants", "id_prefix": "P", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "organisation", "label": "Organisation", "type": "text"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_PARTICIPANT_STATUS},
    ]},
    "models_in_scope": {"label": "Models", "id_prefix": "MS", "fields": [
        {"key": "model_id", "label": "Model", "type": "text", "required": True},
    ]},
    "decisions": {"label": "Decisions", "id_prefix": "D", "fields": [
        {"key": "description", "label": "Decision", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
    ]},
    "actions": {"label": "Actions", "id_prefix": "A", "fields": [
        {"key": "description", "label": "Action", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text"},
        {"key": "target_date", "label": "Target date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_ACTION_STATUSES},
    ]},
}
