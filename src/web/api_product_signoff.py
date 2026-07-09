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
"""Product MRC sign-off: derive the responsible committee (via the product's
Analytics Model) and raise a sign-off request. Mirrors ``api_models_signoff``;
registered on the shared ``product_bp`` blueprint."""
from __future__ import annotations

from flask import jsonify

from src.governance.model_inventory import get_model
from src.governance.mrc import get_meeting, matching_mrc
from src.governance.product import get_product
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import PRODUCT_SUBJECT, _newest, raise_signoff
from src.web.api_product import product_bp


def _product_mrc(product_data: dict):
    """The committee responsible for a product, via its Analytics Model's org."""
    analytics_model = product_data.get("analytics_model")
    model = get_model(analytics_model) if analytics_model else None
    data = (model["data"] if model else {}) or {}
    mrc, level = matching_mrc(data.get("division"), data.get("department"), get_reference_lists())
    return mrc, level, analytics_model


def _product_pending_signoff(product_data: dict) -> dict | None:
    """The product's current active (Pending or Attached) sign-off request."""
    active = [r for r in (product_data.get("rag_signoff_requests") or [])
              if r.get("status") in ("Pending", "Attached")]
    request = _newest(active)
    if request is None:
        return None
    result = {"proposed_rag": request.get("proposed_rag"),
              "target_mrc": request.get("target_mrc"), "status": request.get("status")}
    if request.get("status") == "Attached" and request.get("meeting_id"):
        meeting = get_meeting(request["meeting_id"])
        mdata = (meeting["data"] if meeting else {}) or {}
        result.update({"meeting_id": request["meeting_id"],
                       "meeting_title": mdata.get("title"), "meeting_date": mdata.get("date")})
    return result


@product_bp.get("/<product_id>/mrc")
def product_mrc(product_id: str):
    """The MRC for this product (via its Analytics Model) + any pending sign-off."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    data = product["data"] or {}
    mrc, level, via_model = _product_mrc(data)
    return jsonify({"mrc": mrc, "level": level, "via_model": via_model,
                    "pending_signoff": _product_pending_signoff(data)})


@product_bp.post("/<product_id>/request-signoff")
def product_request_signoff(product_id: str):
    """Owner raises an MRC sign-off for the product's current RAG rating. Routed
    to the product's committee (via its Analytics Model) and queued; attaches to
    a Scheduled meeting at once, else waits for one to be scheduled."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    data = product["data"] or {}
    proposed_rag = data.get("rag_rating")
    if not proposed_rag:
        return jsonify({"error": "set the product's RAG rating before requesting sign-off"}), 400
    mrc, _level, via_model = _product_mrc(data)
    if mrc is None:
        reason = ("no Analytics Model is bound" if not via_model
                  else f"no MRC committee covers Analytics Model {via_model}")
        return jsonify({"error": f"cannot request sign-off — {reason}. "
                                 "Bind a model / configure an MRC under Admin → MRC first"}), 400
    ctx = context_from_request(json_body())
    raise_signoff(ctx, PRODUCT_SUBJECT, product_id,
                  proposed_rag=proposed_rag, target_mrc=mrc["value"], note=json_body().get("note"))
    return jsonify(get_product(product_id)), 201
