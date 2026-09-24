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
"""The criticality weights a division may set, as the Admin editor lists them.

Every name the audit scores, the label a person knows it by, and the firm-wide
value it starts from -- so the editor shows what a blank input means rather than
leaving the administrator to guess, and never offers a name the validator would
refuse. Built from the same sections the validator and the resolver read.
"""
from __future__ import annotations

from config.governance import (
    COLLECTION_SPECS,
    ML_APPLICATION_COLLECTION_SPECS,
    ML_APPLICATION_FIELD_SPECS,
    MODEL_FIELD_SPECS,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_FIELD_SPECS,
)
from config.governance._ai_system import (AI_SYSTEM_COLLECTION_SPECS,
                                          AI_SYSTEM_FIELD_SPECS)
from config.governance._completeness_weights import (AUDIT_WEIGHT_MAX,
                                                     AUDIT_WEIGHT_MIN,
                                                     AUDIT_WEIGHT_SECTIONS)

# Where a name's label comes from, per kind. A field shared by several kinds of
# record keeps the first label found, so a model's reads as it does on the model.
_SPEC_SETS = {
    "field": (MODEL_FIELD_SPECS, PRODUCT_FIELD_SPECS, ML_APPLICATION_FIELD_SPECS,
              AI_SYSTEM_FIELD_SPECS),
    "collection": (COLLECTION_SPECS, PRODUCT_COLLECTION_SPECS,
                   ML_APPLICATION_COLLECTION_SPECS, AI_SYSTEM_COLLECTION_SPECS),
    "document": (),   # a documentation category is its own label
}


def _label(kind: str, name: str) -> str:
    for specs in _SPEC_SETS[kind]:
        if name in specs:
            return specs[name].get("label", name)
    return name


def weight_catalogue() -> dict:
    """``{min, max, sections: [{kind, policy_key, label, rows: [{name, label, firm}]}]}``."""
    sections = []
    for kind, section in AUDIT_WEIGHT_SECTIONS.items():
        rows = [{"name": name, "label": _label(kind, name),
                 "firm": section["table"].get(name, section["default"])}
                for name in section["names"]]
        rows.sort(key=lambda r: (r["label"].lower(), r["name"]))
        sections.append({"kind": kind, "policy_key": section["policy_key"],
                         "label": section["label"], "rows": rows})
    return {"min": AUDIT_WEIGHT_MIN, "max": AUDIT_WEIGHT_MAX, "sections": sections}
