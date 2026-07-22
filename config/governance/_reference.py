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

# Order: the Division/Line of Business org tree first, then the MRC committees
# anchored to that tree, then the Product platform (Calculating Agent), then
# the People directory. Company is no longer a reference list — it's implicit:
# every instance IS a single institution, and its name lives in the singleton
# MRC settings under org_name. Market Data Models live in the Model Inventory
# tagged type="Market Data Model".
REFERENCE_LISTS = (
    "division", "line_of_business", "mrc", "calculating_agent", "people",
)

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
    # People carry an org unit — Division + Line of Business, backed by the admin lists,
    # exactly like a model's org fields. This anchoring is what makes a person
    # eligible to sit on a given MRC or own a model in that scope. Role and
    # organisation are not tracked — every person belongs to this institution.
    "people": {"label": "People", "id_prefix": "PE", "display": "name", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "division", "label": "Division", "type": "text", "reference": "division"},
        {"key": "line_of_business", "label": "Line of Business", "type": "text", "reference": "line_of_business"},
    ]},
}
