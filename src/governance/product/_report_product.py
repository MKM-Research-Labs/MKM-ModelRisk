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
"""One product's dossier for the Product Document — the product-side twin of the
model dossier in ``_report_model``.

A product is a combination of models priced on a calculating agent, so its dossier
leads with the component models it pulls together (the same models whose packs the
product pack bundles) and then reports the product's own record: classification,
bindings, governance, the registers it carries (assumptions, limitations,
remediation, operational events, RACI) and the MRC sign-off history. Absent
material is stated as absent, not omitted, exactly as the model dossier does.
"""
from __future__ import annotations

from typing import Any

from config.files import HIDDEN_DOC_EXTENSIONS
from config.governance import (PRODUCT_COLLECTION_SPECS, PRODUCT_COMPONENTS,
                               PRODUCT_FIELD_SPECS)
from src.files import extension
from src.governance.latex import _esc, _para_table, _section, _wrappable
from src.governance.model_inventory import get_model

NOT_RECORDED = "\\textit{Not recorded.}\n\n"

# The description opens the dossier as a paragraph, so it is not repeated in the
# field table beneath it.
SKIP_FIELDS = {"description"}

# The field group the derived review-due status is appended to.
REVIEW_DATES_GROUP = "Review dates"
REVIEW_DUE_LABEL = "Review due (at document date)"
# The field group the derived identifier is appended to: the product's identity is
# its bound models plus its agent, which is exactly what this group is about.
BINDINGS_GROUP = "Bindings"
IDENTIFIER_LABEL = "Derived identifier"

# How each register is laid out: per-column widths for a table, or "blocks" for a
# register whose fields carry too much prose to sit side by side in one row.
LAYOUTS: dict[str, Any] = {
    "assumptions": (0.46, 0.10, 0.22, 0.22),
    "limitations": (0.46, 0.10, 0.22, 0.22),
    "remediation_steps": (0.42, 0.15, 0.10, 0.13, 0.20),
    "raci_roles": (0.20, 0.10, 0.22, 0.18, 0.30),
    "operational_failure_events": "blocks",
    "signoff_history": "blocks",
}

# The registers making up the dossier, in review order, after the component models.
COLLECTIONS = [
    ("assumptions", None),
    ("limitations", None),
    ("remediation_steps", "Remediation plan"),
    ("operational_failure_events", "Operational-event log"),
    ("raci_roles", "RACI operating model"),
    ("signoff_history", "Model Risk Committee sign-off history"),
]


def items(data: dict, name: str) -> list[dict]:
    """A collection's entries, skipping any malformed non-object entry rather than
    failing the whole document over one bad record."""
    return [i for i in data.get(name) or [] if isinstance(i, dict)]


def _value(data: dict, key: str) -> str:
    value = data.get(key)
    if value is None or value == "":
        return "Not recorded"
    return str(value)


def _groups() -> dict[str, list[str]]:
    """The product's field groups, in the order the specs declare them."""
    groups: dict[str, list[str]] = {}
    for key, spec in PRODUCT_FIELD_SPECS.items():
        if key not in SKIP_FIELDS:
            groups.setdefault(spec.get("group", "Other"), []).append(key)
    return groups


def _field_group(data: dict, title: str, keys: list[str], extra: list) -> str:
    rows = [[PRODUCT_FIELD_SPECS[k].get("label", k), _value(data, k)] for k in keys] + extra
    return _section(title, _para_table(["Field", "Value"], rows, [0.28, 0.72]))


def _component_models(data: dict, config) -> str:
    """The models this product binds, each resolved to its inventory name so the
    document names what the product is built from — the same models the product
    pack bundles. A component whose model has left the inventory is still listed,
    marked as such, rather than silently dropped."""
    components = items(data, PRODUCT_COMPONENTS)
    if not components:
        return _section("Component models", NOT_RECORDED)
    rows = []
    for comp in components:
        model_id = str(comp.get("model_id") or "")
        model = get_model(model_id, config=config) if model_id else None
        if model is not None:
            name = (model.get("data") or {}).get("name") or ""
            model_cell = f"{model_id} --- {name}" if name else model_id
        elif model_id:
            model_cell = f"{model_id} (not in the inventory)"
        else:
            model_cell = "Not recorded"
        rows.append([comp.get("component_type", ""), model_cell, comp.get("role", "")])
    body = _para_table(["Type", "Model", "Role in product"], rows, [0.26, 0.44, 0.30])
    return _section("Component models", body)


def _blocks(entries: list[dict], fields: list[dict]) -> str:
    """One labelled block per item, each field on its own line so long rationales
    wrap instead of being squeezed into a table column."""
    out = []
    for index, item in enumerate(entries, start=1):
        lines = ["\\textbf{" + _esc(str(index)) + ".}\\quad "]
        for field in fields:
            value = item.get(field["key"])
            if value is None or value == "":
                continue
            lines.append("\\textbf{" + _esc(field["label"]) + ":} " + _wrappable(value) + " \\\\\n")
        out.append("".join(lines).rstrip(" \\\n") + "\n\n")
    return "".join(out)


def _collection(data: dict, name: str, label: str | None) -> str:
    spec = PRODUCT_COLLECTION_SPECS[name]
    fields = spec["fields"]
    entries = items(data, name)
    title = label or spec["label"]
    if not entries:
        return _section(title, NOT_RECORDED)
    layout = LAYOUTS[name]
    if layout == "blocks":
        return _section(title, _blocks(entries, fields))
    rows = [[item.get(f["key"], "") for f in fields] for item in entries]
    return _section(title, _para_table([f["label"] for f in fields], rows, list(layout)))


def _documents(data: dict) -> str:
    """The evidence pack attached to the product. Sources filed beside their PDF
    (``.tex``) are left out: they are the same document listed twice."""
    docs = [d for d in items(data, "documents")
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    if not docs:
        return _section("Attached documents", NOT_RECORDED)
    rows = [[d.get("category", ""), d.get("filename", ""), d.get("description", "")]
            for d in docs]
    body = _para_table(["Category", "File", "Description"], rows, [0.22, 0.33, 0.45])
    return _section("Attached documents", body)


def product_section(product: dict, review_status: str, config=None) -> str:
    """A product's complete dossier as top-level sections, for the Product Document."""
    data = product.get("data", {})
    parts = [_section("Overview", _wrappable(data.get("description") or "") + "\n\n"
                      if data.get("description") else NOT_RECORDED)]
    parts.append(_component_models(data, config))
    for group, keys in _groups().items():
        extra = []
        if group == REVIEW_DATES_GROUP:
            extra = [[REVIEW_DUE_LABEL, review_status]]
        elif group == BINDINGS_GROUP:
            extra = [[IDENTIFIER_LABEL, data.get("identifier") or "Not yet derived"]]
        parts.append(_field_group(data, group, keys, extra))
    for name, label in COLLECTIONS:
        parts.append(_collection(data, name, label))
    parts.append(_documents(data))
    return "".join(parts)
