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
"""Product Valuation Model (PVM) field metadata and vocabulary (coding rule R1)."""
from __future__ import annotations

from config.governance._collections import COLLECTION_SPECS

VALID_PVM_STATUS = ("Proposed", "Active", "Suspended", "Retired")

# The three component bindings: set at registration, changed only via a rebind.
# The derived identifier reads them in this order (Analytics leads — it is the
# engine that prices the product; then Market Data, then the Calculating Agent).
PVM_BINDINGS = ("analytics_model", "market_data_model", "calculating_agent")

# Ordered scalar field specs. ``analytics_model`` references the Model Inventory
# (resolved specially, not via a reference list); the other two bindings and the
# owner reference admin lists.
PVM_FIELD_SPECS = {
    "product": {"label": "Product", "type": "text", "group": "Product"},
    "product_id": {"label": "Product ID", "type": "text", "group": "Product"},
    "analytics_model": {"label": "Analytics Model", "type": "text", "group": "Bindings"},
    "market_data_model": {"label": "Market Data Model", "type": "text", "group": "Bindings",
                          "reference": "market_data_model"},
    "calculating_agent": {"label": "Calculating Agent", "type": "text", "group": "Bindings",
                          "reference": "calculating_agent"},
    "status": {"label": "Status", "type": "choice", "options": VALID_PVM_STATUS, "group": "Governance"},
    "owner": {"label": "Owner", "type": "text", "group": "Governance", "reference": "people"},
    "monitoring_approach": {"label": "Monitoring approach", "type": "text", "group": "Monitoring"},
    "monitoring_results": {"label": "Monitoring results", "type": "text", "group": "Monitoring"},
    "notes": {"label": "Notes", "type": "text", "group": "Governance"},
}

# Fields editable through the generic field-edit command (the bindings are not —
# they are changed via rebind; ``status`` Retired is reached via retire).
PVM_EDITABLE_FIELDS = (
    "product", "product_id", "status", "owner",
    "monitoring_approach", "monitoring_results", "notes",
)
PVM_FIELD_CHOICES = {"status": VALID_PVM_STATUS}

# The register form's minimum (besides the mandatory PVM ID).
PVM_REGISTER_FIELDS = ("product", "analytics_model", "market_data_model", "calculating_agent")

# Production-level registers — reuse the inventory's Limitations / Assumptions shapes.
PVM_COLLECTION_SPECS = {
    "limitations": COLLECTION_SPECS["limitations"],
    "assumptions": COLLECTION_SPECS["assumptions"],
}
