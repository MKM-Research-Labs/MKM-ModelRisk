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
"""Admin-managed reference data: people directory + menu lists (coding rule R1).

Each spec's ``display`` field is the value shown in dropdowns that reference it.
"""
from __future__ import annotations

from config.permissions import ROLES

# Order: the Division/Line of Business org tree first, then the MRC committees
# anchored to that tree, then the Product platform (Calculating Agent), then
# the People directory. Company is no longer a reference list — it's implicit:
# every instance IS a single institution, and its name lives in the singleton
# MRC settings under org_name. Model types and codebases are admin-managed too,
# so an adopter classifies its own estate rather than inheriting ours.
MODEL_TYPE_LIST = "model_type"
CODEBASE_LIST = "codebase"
# The vendors/feeds a model pulls its inputs from (a model's ``data_sources``
# collection picks from this) and who supplies the model itself (a model's
# ``vendor`` field). Both sit next to the Calculating Agent platform list.
DATA_SOURCE_LIST = "data_source"
VENDOR_LIST = "vendor"

REFERENCE_LISTS = (
    "division", "line_of_business", "mrc", "calculating_agent", DATA_SOURCE_LIST,
    MODEL_TYPE_LIST, VENDOR_LIST, CODEBASE_LIST, "people",
)

# What a model type means to a Product's bindings. A Product binds one analytics
# engine and one market-data source, and it picks each from the inventory filtered
# by this role -- NOT by the type's name. The name is admin-editable and the list
# is meant to grow (Curve Model, and whatever an adopter adds next); matching on a
# literal string would mean renaming a type, or adding one, silently emptied the
# market-data dropdown and swept every model into the analytics one.
VALID_BINDING_ROLES = ("Analytics", "Market Data", "Neither")

# The one role the Product bindings branch on, named here so the API never spells
# it as a literal (which is the mistake this whole indirection exists to remove).
MARKET_DATA_ROLE = "Market Data"

# Seeded on first use so the list is never empty (an empty reference list falls
# back to a free-text box, which is how the estate ended up with no types at all).
# An adopter renames or extends these in Admin; the roles are what the bindings
# read, so the names are safe to change.
#
# Analytical models price or quantify risk; Curve Models produce the hazard and
# damage curves the analytical engines consume; Market Data Models produce
# calibrated curves/surfaces. All are models -- they involve methodology and
# judgement, not raw vendor feeds -- which is why they sit on one inventory.
DEFAULT_MODEL_TYPES = (
    {"value": "Analytical Model", "binding_role": "Analytics"},
    {"value": "Curve Model", "binding_role": "Analytics"},
    {"value": "Market Data Model", "binding_role": "Market Data"},
    {"value": "Other", "binding_role": "Neither"},
)

# Simple single-value lists seeded on first use (same "seed a vacuum, never
# reconcile a curated list" rule as the model types above). Data sources are the
# feeds a model pulls its inputs from; Vendor names who supplies the model
# itself. Both are strict lists an adopter re-seeds to its own estate.
#
# The vendor seed names no institution: a fresh install should not plant this
# platform's author in an adopter's inventory, where it would sit in the Vendor
# menu as though it supplied their models. "In-house" is the honest starting
# point (most banks build their own), and every real supplier — including this
# one, on the MKM estate — is added in Admin > Vendor.
DEFAULT_DATA_SOURCES = ("ICE", "Reuters", "Bloomberg", "Manual", "Simulated", "Other")
DEFAULT_VENDORS = ("In-house", "Other")

# MRC committees are anchored to one of the three org tiers. A Line of Business-level
# MRC only sees models in that line of business; Division sees everything across its
# lines of business; Company sees the whole inventory. Approvals can be escalated up
# this hierarchy manually (never automatic).
VALID_MRC_LEVELS = ("Company", "Division", "Line of Business")
VALID_MRC_FREQUENCIES = ("Monthly", "Quarterly", "Semi-annual", "Annual")

# The org hierarchy cascades: a Division is just a name; a Line of Business belongs to a
# Division. (Divisions/Lines of Business no longer carry an Owner — model ownership is
# set on the model itself.)
REFERENCE_SPECS = {
    "division": {"label": "Division", "id_prefix": "DV", "display": "value", "fields": [
        {"key": "value", "label": "Division", "type": "text", "required": True},
    ]},
    "line_of_business": {"label": "Line of Business", "id_prefix": "LOB", "display": "value", "fields": [
        {"key": "value", "label": "Line of Business", "type": "text", "required": True},
        {"key": "division", "label": "Division", "type": "text", "reference": "division", "required": True},
    ]},
    # --- MRC committees anchored to the org hierarchy ---
    # ``value`` is the MRC's unique identifier (e.g. MRC-EMEA-RATES); ``name`` is
    # the human-readable label. ``level`` fixes which org tier this committee
    # sits at; ``scope_value`` is which specific Division/Line of Business it covers
    # (unused for a Company-level MRC).
    "mrc": {"label": "MRC", "id_prefix": "MRC", "display": "value", "fields": [
        {"key": "value", "label": "MRC ID", "type": "text", "required": True},
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "level", "label": "Level", "type": "choice",
         "options": VALID_MRC_LEVELS, "required": True},
        {"key": "scope_value", "label": "Division / Line of Business", "type": "text"},
        {"key": "frequency", "label": "Frequency", "type": "choice",
         "options": VALID_MRC_FREQUENCIES},
        # Membership roster — chosen from people within the committee's org scope.
        # Hidden from the table/add form; the detail renders a Membership section.
        # Chair + Secretary are single people; voting / non-voting are lists.
        {"key": "chair", "label": "Chair", "type": "text", "reference": "people", "hidden": True},
        {"key": "secretary", "label": "Secretary", "type": "text", "reference": "people",
         "hidden": True},
        {"key": "voting_members", "label": "Voting members", "type": "text", "hidden": True},
        {"key": "non_voting_members", "label": "Non-voting members", "type": "text", "hidden": True},
        # Quorum rule — the minimum attendance for the meeting to be quorate and
        # able to proceed. Defaults: Chair + Secretary + 2 voting members
        # (non-voting members do not count towards quorum). Hidden from the
        # table/add form; the committee detail renders a Quorum section.
        # Evaluated per meeting against who is marked Attended.
        {"key": "quorum_require_chair", "label": "Quorum requires chair",
         "type": "choice", "options": ("Yes", "No"), "hidden": True},
        {"key": "quorum_require_secretary", "label": "Quorum requires secretary",
         "type": "choice", "options": ("Yes", "No"), "hidden": True},
        {"key": "quorum_min_voting", "label": "Quorum min voting", "type": "text", "hidden": True},
        # The committee's Terms of Reference document, uploaded per committee via
        # the dedicated /tor endpoints. Hidden from the table/add form — the
        # detail view renders an upload/download control instead.
        {"key": "tor_filename", "label": "ToR file", "type": "text", "hidden": True},
        {"key": "tor_original_name", "label": "ToR name", "type": "text", "hidden": True},
        # A committee is never deleted — only archived. Retained for history and
        # any meetings already bound to it. Hidden from the table/add form; the
        # detail view offers an Archive / Unarchive toggle.
        {"key": "archived", "label": "Archived", "type": "text", "hidden": True},
    ]},
    # --- Product reference data (platform) ---
    "calculating_agent": {"label": "Calculating Agent", "id_prefix": "CA", "display": "value",
                          "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
    ]},
    # The feeds a model draws its inputs from. A model's ``data_sources``
    # collection picks from this list, so "these two models share a source" is a
    # match on a defined id rather than on free-text spelling.
    DATA_SOURCE_LIST: {"label": "Data Source", "id_prefix": "DS", "display": "value", "fields": [
        {"key": "value", "label": "Data source", "type": "text", "required": True},
    ]},
    # --- Model classification ---
    # ``binding_role`` is the machine-readable half of a type: the name is for
    # people and may be renamed freely, the role is what Product bindings filter
    # on. See VALID_BINDING_ROLES above.
    MODEL_TYPE_LIST: {"label": "Model Type", "id_prefix": "MT", "display": "value", "fields": [
        {"key": "value", "label": "Type", "type": "text", "required": True},
        {"key": "binding_role", "label": "Binding role", "type": "choice",
         "options": VALID_BINDING_ROLES, "required": True},
    ]},
    # Who supplies the model itself (as opposed to the data it consumes). Strict,
    # like Model Type: a model cannot name a vendor nobody has defined.
    VENDOR_LIST: {"label": "Vendor", "id_prefix": "VN", "display": "value", "fields": [
        {"key": "value", "label": "Vendor", "type": "text", "required": True},
    ]},
    # A codebase carries the repository it lives in, so the two travel together.
    # Held as one entry rather than two lists because they are one fact: a second,
    # independently-edited repo list can disagree with this one, and then nothing
    # says which is right.
    CODEBASE_LIST: {"label": "Codebase", "id_prefix": "CB", "display": "value", "fields": [
        {"key": "value", "label": "Codebase", "type": "text", "required": True},
        {"key": "repo_location", "label": "Repository location", "type": "text"},
    ]},
    # People carry an org unit — Division + Line of Business, backed by the admin lists,
    # exactly like a model's org fields. This anchoring is what makes a person
    # eligible to sit on a given MRC or own a model in that scope. Organisation is not
    # tracked — every person belongs to this institution.
    #
    # Roles (permissions P2) say what a person may BE; a person may hold several. They are
    # recorded here rather than in a separate register so that adding somebody and saying
    # what they do is one act, and so every change is an audited reference-list event.
    "people": {"label": "People", "id_prefix": "PE", "display": "name", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "email", "label": "Email", "type": "text"},
        # Two fields, because a role is granted by a committee and not by whoever is
        # editing the screen. "Proposed roles" is what an administrator sets; "Roles" is
        # what the MRC has ratified and what the system acts on. Only the ratification
        # path writes it, so it is readonly to the client.
        {"key": "roles", "label": "Roles", "type": "multichoice", "options": list(ROLES),
         "explanations": ROLES, "readonly": True},
        {"key": "pending_roles", "label": "Proposed roles", "type": "multichoice",
         "options": list(ROLES), "explanations": ROLES},
        # The meeting that last ratified this person's roles — the answer to "who
        # granted this approver their seat".
        {"key": "roles_ratified_meeting", "label": "Ratified at", "type": "text",
         "readonly": True},
        {"key": "division", "label": "Division", "type": "text", "reference": "division"},
        {"key": "line_of_business", "label": "Line of Business", "type": "text", "reference": "line_of_business"},
    ]},
}
