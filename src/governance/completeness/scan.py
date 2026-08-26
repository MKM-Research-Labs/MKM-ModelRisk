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

from config.governance import (ML_APPLICATION_COLLECTION_SPECS,
                               ML_APPLICATION_FIELD_SPECS,
    COLLECTION_SPECS,
    FINOS_SHELF,
    DOC_CATEGORIES,
    MODEL_FIELD_SPECS,
    PRODUCT_AUDIT_DOC_CATEGORIES,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_FIELD_SPECS,
)
from src.files import upload_path
from src.governance.completeness._rules import audit_entity
from src.governance.documents import (GOVERNANCE_ARTEFACTS_AGGREGATE,
                                      list_documents, ml_application_scope,
                                      model_scope)
from src.governance.model_inventory.projection import list_models
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.ai_system.projection import list_ai_systems
from src.governance.ml_application.projection import list_ml_applications
from src.governance.product.projection import list_products
from src.governance.risk_policy import load as load_policy

MODEL_KIND = "Model"
PRODUCT_KIND = "Product"
ML_APPLICATION_KIND = "ML Application"


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


def _audit(kind, entity_id, name, data, field_specs, collection_specs, scope, as_of,
           doc_categories=DOC_CATEGORIES):
    """One record's audit. ``doc_categories`` is what this KIND of record is asked to
    evidence, which is not the same as what it may file: a Product is scored on the
    shorter ``PRODUCT_AUDIT_DOC_CATEGORIES`` because the paper about its analytics is
    demanded of its component models, and scoring it here too would raise a finding
    closable only by filing a second copy."""
    return audit_entity(
        entity_kind=kind, entity_id=entity_id, entity_name=name or "", data=data,
        field_specs=field_specs, collection_specs=collection_specs,
        doc_categories=doc_categories, risk=compute_risk_rating(data, as_of=as_of),
        as_of=as_of, available=_retrievable(scope),
    )


def scan(as_of: str, config=None, model_ids=None, product_ids=None,
         ml_application_ids=None) -> list[dict[str, Any]]:
    """Audit every model, product and ML Application, worst completeness first.

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
    want_ml = None if ml_application_ids is None else set(ml_application_ids)
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
            product_scope(product["product_id"]), as_of,
            doc_categories=PRODUCT_AUDIT_DOC_CATEGORIES))
    # ML Applications are audited on the same terms as everything else. An estate
    # half of which is ML, audited on the other half, reports a gap picture that is
    # wrong in the direction that flatters — and nothing on the page would say so.
    # A retired record is out of the estate and out of every figure, exactly as a
    # hibernated model is -- both projections exclude them by default, or the audit
    # reports gaps against records nobody is running.
    for record in list_ml_applications(config=config):
        if want_ml is not None and record["ml_application_id"] not in want_ml:
            continue
        data = record.get("data") or {}
        rows.append(_audit(
            ML_APPLICATION_KIND, record["ml_application_id"], data.get("name"), data,
            ML_APPLICATION_FIELD_SPECS, ML_APPLICATION_COLLECTION_SPECS,
            ml_application_scope(record["ml_application_id"]), as_of))
    rows.sort(key=lambda r: (r["completeness"], r["entity_id"]))
    return rows


def coverage_population(model_ids=None, ml_application_ids=None,
                        ai_system_ids=None, config=None) -> list[dict[str, Any]]:
    """Every record the framework clauses are counted over.

    Models, ML Applications AND AI Systems. The clause probes are field-name lambdas
    over one population, and each later record type carries the same field names a
    model does precisely so it can join that population without a per-type branch
    (see docs/design/mlmodel.md decision 7, and docs/design/finos-coverage.md 6.1).
    Counting the clauses over models alone would report a coverage picture of a
    shrinking slice of the estate as the other two grow — the same failure the gap
    audit had.

    The AI-specific clauses narrow this population again to the AI Systems in it;
    that rule lives with those probes, in ``_probes_ai``, not here.

    Retired records are excluded on every side: out of the estate, out of every
    figure.
    """
    records = list(scoped_models(model_ids, config=config))
    want_ml = None if ml_application_ids is None else set(ml_application_ids)
    for record in list_ml_applications(config=config):
        if want_ml is not None and record["ml_application_id"] not in want_ml:
            continue
        records.append(record)
    want_ai = None if ai_system_ids is None else set(ai_system_ids)
    for record in list_ai_systems(config=config):
        if want_ai is not None and record["ai_system_id"] not in want_ai:
            continue
        records.append(record)
    return records


def scoped_models(model_ids=None, config=None) -> list[dict[str, Any]]:
    """The inventory the report's estate-wide sections read, under the same scope
    rule as ``scan``: ``None`` is the whole estate, an empty sequence is nothing.

    It exists so the two cannot diverge. A committee-scoped audit that scoped its
    findings but not its inventory would print one table counting the committee's
    records beside another counting the firm's, with nothing on the page to say
    which was which.
    """
    models = list_models(config=config)
    if model_ids is None:
        return models
    wanted = set(model_ids)
    return [m for m in models if m["model_id"] in wanted]


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


def finos_evidence(config=None) -> list[dict]:
    """The control documentation filed on the FINOS shelf.

    The FINOS mitigation catalogue is the one part of the coverage table not counted
    from the register: a mitigation is a control the institution runs, largely
    outside this platform, and what a governance record can attest is that the firm
    has described it. So the evidence is the filed paper, and this reads the shelf.

    An empty shelf is not an error and is not hidden. Every mitigation then reads
    Not evidenced, which is the correct account of an institution that has filed
    nothing -- and the sentence in each row says where the document would go.
    """
    return list_documents(GOVERNANCE_ARTEFACTS_AGGREGATE, FINOS_SHELF, config)


def findings(rows: list[dict]) -> list[dict]:
    """Every gap across every record, most severe first — the priority register."""
    gaps = [gap for row in rows for gap in row["gaps"]]
    gaps.sort(key=lambda g: (-g["severity"], g["entity_id"], g["key"]))
    return gaps
