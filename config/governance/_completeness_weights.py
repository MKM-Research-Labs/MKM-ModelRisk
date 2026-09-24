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
"""Which criticality weights a division may set for itself, and within what bounds.

The weights themselves -- what a missing field, collection or documentation
category is worth -- are the firm-wide tables in ``_completeness``. A division's
risk policy may override any of them in its ``audit`` section; an absent key
reads through to the table here, so the tables are the seed and the fallback,
never removed. See docs/design/completeness-weights.md.

Kept apart from ``_completeness`` because the names a division may weight are
every field and collection any audited record is asked for, which means reading
all four kinds' specs -- a dependency the weight tables themselves do not have.
"""
from __future__ import annotations

from config.governance import (
    COLLECTION_CRITICALITY,
    COLLECTION_SPECS,
    DEFAULT_COLLECTION_CRITICALITY,
    DEFAULT_DOC_CRITICALITY,
    DEFAULT_FIELD_CRITICALITY,
    DOC_CATEGORIES,
    DOC_CRITICALITY,
    EXEMPT_COLLECTIONS,
    EXEMPT_DOC_CATEGORIES,
    EXEMPT_FIELDS,
    FIELD_CRITICALITY,
    ML_APPLICATION_COLLECTION_SPECS,
    ML_APPLICATION_FIELD_SPECS,
    MODEL_FIELD_SPECS,
    PRODUCT_AUDIT_DOC_CATEGORIES,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_FIELD_SPECS,
)
from config.governance._ai_system import (AI_SYSTEM_COLLECTION_SPECS,
                                          AI_SYSTEM_FIELD_SPECS)

# The bounds on a division's weight. The floor is the point: a weight is how much
# a gap matters, and a committee that could set one to zero could make a real gap
# disappear from its own remediation list while the report showed it compliant.
# The ceiling is twice the firm-wide top of the scale (1.00, "a validator would
# refuse to sign off around it"), room to say a gap matters more here than anywhere.
AUDIT_WEIGHT_MIN = 0.10
AUDIT_WEIGHT_MAX = 2.00


def _weightable(names, table, exempt) -> frozenset:
    """Everything the audit can raise a gap against, less what it never scores."""
    return frozenset(set(names) | set(table)) - frozenset(exempt)


# Each section of ``policy["audit"]``: the firm-wide table it overrides, the value
# for a name the table does not list, and the names a division may set. The kind
# of gap each section weighs is the key ``completeness._weights`` resolves by.
AUDIT_WEIGHT_SECTIONS = {
    "field": {
        "policy_key": "field_weights",
        "table": FIELD_CRITICALITY,
        "default": DEFAULT_FIELD_CRITICALITY,
        "names": _weightable(
            [*MODEL_FIELD_SPECS, *PRODUCT_FIELD_SPECS, *ML_APPLICATION_FIELD_SPECS,
             *AI_SYSTEM_FIELD_SPECS], FIELD_CRITICALITY, EXEMPT_FIELDS),
    },
    "collection": {
        "policy_key": "collection_weights",
        "table": COLLECTION_CRITICALITY,
        "default": DEFAULT_COLLECTION_CRITICALITY,
        "names": _weightable(
            [*COLLECTION_SPECS, *PRODUCT_COLLECTION_SPECS,
             *ML_APPLICATION_COLLECTION_SPECS, *AI_SYSTEM_COLLECTION_SPECS],
            COLLECTION_CRITICALITY, EXEMPT_COLLECTIONS),
    },
    "document": {
        "policy_key": "doc_weights",
        "table": DOC_CRITICALITY,
        "default": DEFAULT_DOC_CRITICALITY,
        "names": _weightable([*DOC_CATEGORIES, *PRODUCT_AUDIT_DOC_CATEGORIES],
                             DOC_CRITICALITY, EXEMPT_DOC_CATEGORIES),
    },
}

# The policy keys alone, for the validator and the seed.
AUDIT_WEIGHT_KEYS = tuple(s["policy_key"] for s in AUDIT_WEIGHT_SECTIONS.values())
