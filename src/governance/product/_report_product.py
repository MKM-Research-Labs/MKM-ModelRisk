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
from src.governance.risk_policy.naming import field_label
from config.governance import (COMPONENT_KIND_ML, PRODUCT_COLLECTION_SPECS,
                               PRODUCT_COMPONENTS, component_kind,
                               PRODUCT_FIELD_SPECS)
from src.files import extension
from src.governance import report_blocks as rb
from src.governance.latex import _esc, _para_table, _section, _wrappable
from src.governance.report_blocks import NOT_RECORDED, items
from src.governance.ml_application import get_ml_application
from src.governance.model_inventory import get_model


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




def _value(data: dict, key: str) -> str:
    return rb.value(data, key)

def _groups() -> dict[str, list[str]]:
    """The product's field groups, in the order the specs declare them."""
    return rb.field_groups(PRODUCT_FIELD_SPECS, SKIP_FIELDS)

def _field_group(data: dict, title: str, keys: list[str], extra: list) -> str:
    return rb.field_group(data, title, keys, extra, field_specs=PRODUCT_FIELD_SPECS)

def _component_models(data: dict, config) -> str:
    """The models this product binds, each resolved to its inventory name so the
    document names what the product is built from — the same models the product
    pack bundles. A component whose model has left the inventory is still listed,
    marked as such, rather than silently dropped."""
    components = items(data, PRODUCT_COMPONENTS)
    if not components:
        return _section("Components", NOT_RECORDED)
    rows = []
    for comp in components:
        kind = component_kind(comp)
        component_id = str(comp.get("model_id") or "")
        # An ML Application resolves against its own register. Looking it up in the
        # inventory would report a bound component as "not in the inventory" -- a
        # missing model, which is a finding, rather than a component of another kind.
        if kind == COMPONENT_KIND_ML:
            record = get_ml_application(component_id) if component_id else None
            name = (record.get("data") or {}).get("name") or "" if record else ""
            missing = "(not on the ML Application register)"
        else:
            record = get_model(component_id, config=config) if component_id else None
            name = (record.get("data") or {}).get("name") or "" if record else ""
            missing = "(not in the inventory)"
        if record is not None:
            cell = f"{component_id} --- {name}" if name else component_id
        elif component_id:
            cell = f"{component_id} {missing}"
        else:
            cell = "Not recorded"
        rows.append([kind, comp.get("component_type", ""), cell, comp.get("role", "")])
    body = _para_table(["Kind", "Type", "Component", "Role in product"], rows,
                       [0.16, 0.22, 0.36, 0.26], caption="Components")
    return _section("Components", body)




def _collection(data: dict, name: str, label: str | None) -> str:
    return rb.collection(data, name, label, specs=PRODUCT_COLLECTION_SPECS, layouts=LAYOUTS)

def _documents(data: dict) -> str:
    return rb.documents(data)

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
