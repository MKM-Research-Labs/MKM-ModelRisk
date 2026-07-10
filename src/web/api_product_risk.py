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
"""Product risk assessment + MRC linkage reads: the composite risk rating (heatmap
+ weighted breakdown, identical to a model's) and the meeting decisions/actions
linked to a product. Mirrors the model-side endpoints in ``api_models``;
registered on the shared ``product_bp`` blueprint."""
from __future__ import annotations

from datetime import date

from flask import jsonify

from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.mrc import meeting_items_for_model
from src.governance.product import get_product
from src.web.api_product import product_bp


@product_bp.get("/<product_id>/risk-rating")
def product_risk_rating(product_id: str):
    """Composite risk rating + heatmap for a product (same engine as a model)."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    payload = compute_risk_rating(product["data"] or {}, as_of=date.today().isoformat())
    from src.web.api_product_signoff import _product_pending_signoff  # avoids import cycle
    payload["pending_signoff"] = _product_pending_signoff(product["data"] or {})
    return jsonify(payload)


@product_bp.get("/<product_id>/decisions")
def product_decisions(product_id: str):
    """Read-only: every MRC decision linked to this product (from the meeting log)."""
    if get_product(product_id) is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(meeting_items_for_model("decisions", product_id, field="product_id"))


@product_bp.get("/<product_id>/actions")
def product_actions(product_id: str):
    """Read-only: every MRC action linked to this product (from the meeting log)."""
    if get_product(product_id) is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(meeting_items_for_model("actions", product_id, field="product_id"))
