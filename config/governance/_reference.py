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

# Order: Company first (top of the hierarchy), then Division, Department, People.
REFERENCE_LISTS = ("company", "division", "department", "people")

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
    "people": {"label": "People", "id_prefix": "PE", "display": "name", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "organisation", "label": "Organisation", "type": "text"},
    ]},
}
