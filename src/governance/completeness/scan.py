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
"""Reading the registers and the upload directory for the completeness audit.

The I/O half of the audit, kept apart from ``_rules`` so the scoring stays pure.
The one thing this module knows that the rules cannot is whether a document
recorded on a record can actually be produced: the register is a claim, the
filesystem is the fact, and an audit that trusts the claim would report evidence
that nobody can download as evidence held.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    COLLECTION_SPECS,
    DOC_CATEGORIES,
    MODEL_FIELD_SPECS,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_FIELD_SPECS,
)
from src.files import upload_path
from src.governance.completeness._rules import audit_entity
from src.governance.documents import model_scope
from src.governance.model_inventory.projection import list_models
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.product.projection import list_products
from src.governance.risk_policy import load as load_policy

MODEL_KIND = "Model"
PRODUCT_KIND = "Product"


def product_scope(product_id: str) -> str:
    """Where a product's uploaded files live. Mirrors ``model_scope``; named here
    because the product API composes the same string inline."""
    return f"product/{product_id}"


def _retrievable(scope: str):
    """A predicate saying whether a recorded document's file is on disk."""
    def check(doc: dict[str, Any]) -> bool:
        filename = doc.get("filename")
        if not filename:
            return False
        try:
            return upload_path(scope, filename).exists()
        except (OSError, ValueError):
            return False
    return check


def _audit(kind, entity_id, name, data, field_specs, collection_specs, scope, as_of):
    return audit_entity(
        entity_kind=kind, entity_id=entity_id, entity_name=name or "", data=data,
        field_specs=field_specs, collection_specs=collection_specs,
        doc_categories=DOC_CATEGORIES, risk=compute_risk_rating(data, as_of=as_of),
        as_of=as_of, available=_retrievable(scope),
    )


def scan(as_of: str, config=None, model_ids=None, product_ids=None) -> list[dict[str, Any]]:
    """Audit every model and product, worst weighted completeness first.

    Products follow the models so that a reader working down the register meets
    the model gaps before the product gaps that inherit from them.

    ``model_ids`` / ``product_ids`` scope the audit to a named subset (the models
    and products in scope for one MRC committee); leaving them ``None`` audits the
    whole estate — the global Audit Reports behaviour. An empty sequence audits
    nothing of that kind, so a committee that oversees only models still gets a
    models-only report rather than the whole estate.
    """
    want_models = None if model_ids is None else set(model_ids)
    want_products = None if product_ids is None else set(product_ids)
    rows = []
    for model in list_models(config=config):
        if want_models is not None and model["model_id"] not in want_models:
            continue
        data = model.get("data") or {}
        rows.append(_audit(
            MODEL_KIND, model["model_id"], data.get("name"), data,
            MODEL_FIELD_SPECS, COLLECTION_SPECS,
            model_scope(model["model_id"]), as_of))
    for product in list_products(config=config):
        if want_products is not None and product["product_id"] not in want_products:
            continue
        data = product.get("data") or {}
        rows.append(_audit(
            PRODUCT_KIND, product["product_id"], data.get("product"), data,
            PRODUCT_FIELD_SPECS, PRODUCT_COLLECTION_SPECS,
            product_scope(product["product_id"]), as_of))
    rows.sort(key=lambda r: (r["completeness"], r["entity_id"]))
    return rows


def ratified_divisions(models: list[dict], config=None) -> set:
    """The divisions whose risk policy their own committee has actually approved.

    A division still running on the firm-wide seed default has criteria, but not
    criteria it has adopted, and the framework-coverage section turns on that
    difference: ISO 6.3.4 asks the organisation to *define* its risk criteria, and
    inheriting a default is the absence of that decision rather than the making
    of it.
    """
    divisions = {(m.get("data") or {}).get("division") for m in models}
    return {division for division in divisions if division
            and load_policy(division, config)["approved"]}


def findings(rows: list[dict]) -> list[dict]:
    """Every gap across every record, most severe first — the priority register."""
    gaps = [gap for row in rows for gap in row["gaps"]]
    gaps.sort(key=lambda g: (-g["severity"], g["entity_id"], g["key"]))
    return gaps
