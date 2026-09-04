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
"""Product MRC sign-off: derive the responsible committee from the product's own
Division/Line of Business and raise a sign-off request. Mirrors ``api_models_signoff``;
registered on the shared ``product_bp`` blueprint."""
from __future__ import annotations

from datetime import date

from flask import jsonify

from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.mrc import get_meeting, matching_mrc
from src.governance.product import get_product
from src.governance.reference import get_reference_lists
from src.command import require_confirmation
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import (
    PRODUCT_SUBJECT,
    REQUESTS,
    _newest,
    raise_signoff,
)
from src.web._lifecycle_request import request_lifecycle_change
from src.web.api_product import product_bp


def _product_mrc(product_data: dict):
    """The committee responsible for a product, from its own Division/Line of Business.

    A product may be allocated at Division only (Line of Business blank); ``matching_mrc``
    resolves the covering committee (Line of Business-level → Division-level → Company).
    """
    mrc, level = matching_mrc(product_data.get("division"),
                              product_data.get("line_of_business"), get_reference_lists())
    return mrc, level


def _product_pending_signoff(product_data: dict) -> dict | None:
    """The product's current active (Pending or Attached) sign-off request."""
    active = [r for r in (product_data.get(REQUESTS) or [])
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
    """The MRC for this product (from its Division/Line of Business) + any pending sign-off."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    data = product["data"] or {}
    mrc, level = _product_mrc(data)
    return jsonify({"mrc": mrc, "level": level,
                    "pending_signoff": _product_pending_signoff(data)})


@product_bp.post("/<product_id>/request-signoff")
def product_request_signoff(product_id: str):
    """Owner raises an MRC sign-off for the product's current RAG rating. Routed
    to the product's committee (from its Division/Line of Business) and queued; attaches
    to a Scheduled meeting at once, else waits for one to be scheduled."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    data = product["data"] or {}
    # A proposed rating may be supplied (a RAG change proposed for MRC sign-off);
    # otherwise fall back to the product's current rating.
    proposed_rag = json_body().get("proposed_rag") or data.get("rag_rating")
    if not proposed_rag:
        return jsonify({"error": "set the product's RAG rating before requesting sign-off"}), 400
    mrc, _level = _product_mrc(data)
    if mrc is None:
        org = " / ".join(v for v in (data.get("division"), data.get("line_of_business")) if v)
        reason = ("no Division/Line of Business is set" if not org
                  else f"no MRC committee covers this product's org ({org})")
        return jsonify({"error": f"cannot request sign-off — {reason}. "
                                 "Set the product's Division/Line of Business / configure an "
                                 "MRC under Admin → MRC first"}), 400
    ctx = context_from_request(json_body())
    raise_signoff(ctx, PRODUCT_SUBJECT, product_id,
                  proposed_rag=proposed_rag, target_mrc=mrc["value"], note=json_body().get("note"))
    return jsonify(get_product(product_id)), 201


@product_bp.post("/<product_id>/request-retire")
def product_request_retire(product_id: str):
    """Owner asks the MRC to ratify retiring (hibernating) the Product.

    The Product stays in the estate and editable while the request is queued — it
    only drops out once the committee approves. A Product used to retire the moment
    its owner pressed the button, which made it the last record type whose
    hibernation nobody ratified.
    """
    return request_lifecycle_change(PRODUCT_SUBJECT, product_id, kind="retire",
                                    expect_retired=False)


@product_bp.post("/<product_id>/request-reactivate")
def product_request_reactivate(product_id: str):
    """Owner asks the MRC to ratify bringing a hibernated Product back."""
    return request_lifecycle_change(PRODUCT_SUBJECT, product_id, kind="reactivate",
                                    expect_retired=True)
