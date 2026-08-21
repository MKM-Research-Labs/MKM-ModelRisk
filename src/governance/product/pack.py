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
"""The product pack: a product's own document plus the full pack of every model it
binds, as one ZIP.

A product is a combination of models, so the pack a client or validator needs for
it is the product's own write-up together with the full pack of each component
model — the Model Risk Document and evidence for every model the product pulls in.
Each model's pack is flattened under ``models/<model_id>/`` (Model Risk Document
plus its attachments, foldered by category), so the whole product is browsable
without unzipping again. Every generated PDF is built at the moment of packing, so
a pack never carries a stale write-up, and a CONTENTS listing says what was packed
and what was recorded but unavailable, so the pack explains itself.
"""
from __future__ import annotations

import io
import zipfile

from config.files import HIDDEN_DOC_EXTENSIONS
from config.governance import (COMPONENT_KIND_MODEL, PRODUCT_COMPONENTS,
                               component_kind)
from src.files import extension, upload_path
from src.governance.documents import model_scope, product_scope
from src.governance.model_inventory import get_model
from src.governance.model_inventory.document import render_model_document_pdf
from src.governance.product.document import render_product_document_pdf

PACK_NAME = "{product_id}_product_pack.zip"
DOCUMENT_NAME = "{product_id}_product_document.pdf"
CONTENTS_NAME = "CONTENTS.txt"
UNCATEGORISED = "Other"


def _component_model_ids(product: dict) -> list[str]:
    """Every model the product binds as a component, de-duplicated in first-seen
    order — the models whose full packs this pack pulls in.

    ML Application components are skipped: their ids resolve against a different
    register, and asking the model pack builder for one would either fail or quietly
    bundle nothing. Their own documents are not yet part of this pack — see
    docs/design/mlmodel.md.
    """
    data = product.get("data") or {}
    ids = [str(c["model_id"]) for c in (data.get(PRODUCT_COMPONENTS) or [])
           if isinstance(c, dict) and c.get("model_id")
           and component_kind(c) == COMPONENT_KIND_MODEL]
    seen: set[str] = set()
    return [i for i in ids if not (i in seen or seen.add(i))]


def _packable(data: dict) -> list[dict]:
    """A record's attached documents worth packing: PDFs/evidence, LaTeX excluded."""
    docs = [d for d in (data.get("documents") or []) if isinstance(d, dict)
            and extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    return sorted(docs, key=lambda d: (str(d.get("category") or UNCATEGORISED),
                                       str(d.get("original_name") or "")))


def _add_component_models(archive, product, settings, as_of, config, packed, missing) -> None:
    """Each bound model's full pack, flattened under ``models/<model_id>/``."""
    for model_id in _component_model_ids(product):
        model = get_model(model_id, config=config)
        if model is None:
            missing.append(f"models/{model_id} (not in the inventory)")
            continue
        doc_name = f"models/{model_id}/{model_id}_model_risk_document.pdf"
        archive.writestr(doc_name, render_model_document_pdf(model, settings, as_of))
        packed.append(doc_name)
        for doc in _packable(model.get("data", {})):
            path = upload_path(model_scope(model_id), doc["filename"])
            name = (f"models/{model_id}/" + str(doc.get("category") or UNCATEGORISED) +
                    "/" + str(doc.get("original_name") or doc["filename"]))
            if not path.exists():
                missing.append(name)
                continue
            archive.writestr(name, path.read_bytes())
            packed.append(name)


def _add_product_documents(archive, product, config, packed, missing) -> None:
    """The product's own attached documents, foldered by category."""
    product_id = product["product_id"]
    for doc in _packable(product.get("data", {})):
        path = upload_path(product_scope(product_id), doc["filename"])
        name = ("product_documents/" + str(doc.get("category") or UNCATEGORISED) +
                "/" + str(doc.get("original_name") or doc["filename"]))
        if not path.exists():
            missing.append(name + " (recorded but file missing)")
            continue
        archive.writestr(name, path.read_bytes())
        packed.append(name)


def _contents(product: dict, as_of: str, packed: list[str], missing: list[str]) -> str:
    data = product.get("data", {})
    lines = [
        f"{product['product_id']} --- {data.get('product') or ''}",
        f"Product pack, generated {as_of}",
        f"Identifier: {data.get('identifier') or 'not yet derived'}",
        "",
        "This pack contains:",
    ]
    lines += ["  " + name for name in packed]
    if missing:
        # A file recorded on the record but absent from disk is stated, not
        # skipped: a silently short pack is worse than one that says what is missing.
        lines += ["", "Recorded but not available at the time of packing:"]
        lines += ["  " + name for name in missing]
    return "\n".join(lines) + "\n"


def build_product_pack(product: dict, settings: dict, as_of: str, config=None) -> bytes:
    """A product's Product Document plus the full pack of every model it binds, as
    ZIP bytes (see module docstring)."""
    document_name = DOCUMENT_NAME.format(product_id=product["product_id"])
    packed, missing = [document_name], []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(document_name,
                         render_product_document_pdf(product, settings, as_of, config=config))
        _add_component_models(archive, product, settings, as_of, config, packed, missing)
        _add_product_documents(archive, product, config, packed, missing)
        archive.writestr(CONTENTS_NAME, _contents(product, as_of, packed, missing))
    return buffer.getvalue()


def pack_manifest(product: dict, settings: dict, config=None) -> dict:
    """A cheap preview of what the pack would contain, without compiling any PDF.
    Mirrors ``build_product_pack``'s source selection so the preview matches the
    file a subsequent generate produces, and surfaces the same warnings up front."""
    warnings: list[str] = []
    models: list[dict] = []
    for model_id in _component_model_ids(product):
        model = get_model(model_id, config=config)
        if model is None:
            warnings.append(f"Component model {model_id} is not in the inventory — it will be skipped.")
            models.append({"model_id": model_id, "name": None, "present": False, "attachments": []})
            continue
        data = model.get("data") or {}
        docs = _packable(data)
        for doc in docs:
            if not upload_path(model_scope(model_id), doc["filename"]).exists():
                warnings.append(
                    f"{model_id}: attachment '{doc.get('original_name') or doc['filename']}' "
                    "is recorded but its file is missing.")
        models.append({"model_id": model_id, "name": data.get("name"), "present": True,
                       "attachments": [str(d.get("original_name") or d["filename"]) for d in docs]})
    attachments = []
    for doc in _packable(product.get("data") or {}):
        present = upload_path(product_scope(product["product_id"]), doc["filename"]).exists()
        attachments.append({"name": str(doc.get("original_name") or doc["filename"]),
                            "item_id": doc.get("item_id"), "present": present})
        if not present:
            warnings.append(f"Product document '{doc.get('original_name')}' is recorded "
                            "but its file is missing.")
    if not models:
        warnings.append("This product binds no component models — the pack will carry "
                        "only the Product Document.")
    return {"models": models, "attachments": attachments,
            "includes_product_document": True, "warnings": warnings}
