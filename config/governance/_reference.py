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
"""Admin-managed reference data: people directory + menu lists (coding rule R1).

Each spec's ``display`` field is the value shown in dropdowns that reference it.
"""

# Order: the Company org hierarchy first, then the MRC committees anchored to
# that hierarchy, then the Product platform (Calculating Agent), then the
# People directory. Market Data Models are no longer a reference list — they
# live in the Model Inventory tagged type="Market Data Model".
REFERENCE_LISTS = (
    "company", "division", "department", "mrc", "calculating_agent", "people",
)

# MRC committees are anchored to one of the three org tiers. A Department-level
# MRC only sees models in that department; Division sees everything across its
# departments; Company sees the whole inventory. Approvals can be escalated up
# this hierarchy manually (never automatic).
VALID_MRC_LEVELS = ("Company", "Division", "Department")
VALID_MRC_FREQUENCIES = ("Monthly", "Quarterly", "Semi-annual", "Annual")

# The org hierarchy cascades: a Division belongs to a Company, a Department to a
# Division. Each unit carries an Owner (a person), so model ownership attaches to
# the org hierarchy rather than to a single committee setting.
_OWNER = {"key": "owner", "label": "Owner", "type": "text", "reference": "people"}
REFERENCE_SPECS = {
    "company": {"label": "Company", "id_prefix": "CO", "display": "value", "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
        dict(_OWNER),
    ]},
    "division": {"label": "Division", "id_prefix": "DV", "display": "value", "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
        {"key": "company", "label": "Company", "type": "text", "reference": "company", "required": True},
        dict(_OWNER),
    ]},
    "department": {"label": "Department", "id_prefix": "DP", "display": "value", "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
        {"key": "division", "label": "Division", "type": "text", "reference": "division", "required": True},
        dict(_OWNER),
    ]},
    # --- MRC committees anchored to the org hierarchy ---
    # ``value`` is the MRC's unique identifier (e.g. MRC-EMEA-RATES); ``name`` is
    # the human-readable label. ``level`` fixes which org tier this committee
    # sits at; ``scope_value`` is which specific Division/Department it covers
    # (unused for a Company-level MRC).
    "mrc": {"label": "MRC", "id_prefix": "MRC", "display": "value", "fields": [
        {"key": "value", "label": "MRC ID", "type": "text", "required": True},
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "level", "label": "Level", "type": "choice",
         "options": VALID_MRC_LEVELS, "required": True},
        {"key": "scope_value", "label": "Division / Department", "type": "text"},
        {"key": "chair", "label": "Chair", "type": "text", "reference": "people"},
        {"key": "frequency", "label": "Frequency", "type": "choice",
         "options": VALID_MRC_FREQUENCIES},
        # The committee's Terms of Reference document, uploaded per committee via
        # the dedicated /tor endpoints. Hidden from the table/add form — the
        # detail view renders an upload/download control instead.
        {"key": "tor_filename", "label": "ToR file", "type": "text", "hidden": True},
        {"key": "tor_original_name", "label": "ToR name", "type": "text", "hidden": True},
    ]},
    # --- Product reference data (platform) ---
    "calculating_agent": {"label": "Calculating Agent", "id_prefix": "CA", "display": "value",
                          "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
    ]},
    "people": {"label": "People", "id_prefix": "PE", "display": "name", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "organisation", "label": "Organisation", "type": "text"},
    ]},
}
