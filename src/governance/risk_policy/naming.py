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
"""What a division calls its risk dimensions.

A division renames a dimension in Admin, its MRC ratifies it, and from that moment
every screen and every generated document has to say the new name. That only holds
if nobody spells the names out: a label written into a field spec, a report heading
or a paragraph of prose keeps printing the old word precisely when the new one
matters. So the names live in one place — the division's approved policy — and
everything that shows a dimension asks here.

The console has the same rule (``Policy.dimensionName`` in helpers.js). The three
dimensions themselves are structural and do not move.
"""
from __future__ import annotations

from config.governance import RISK_DIMENSION_FIELDS, RISK_RATIONALE_FIELDS


def _humanised(key: str) -> str:
    """A name derived from the structure, for a division with no policy recorded.

    Still not a name anybody typed into the source: it falls out of the dimension
    key itself, so it cannot drift from what the platform actually models.
    """
    return key.replace("_", " ").capitalize()


def dimension_label(key: str, division: str = "", policy: dict | None = None) -> str:
    """What ``division`` calls the dimension ``key``."""
    if policy is None:
        from src.governance.risk_policy._store import get_risk_policy
        policy = get_risk_policy(division) if division else None
    dim = ((policy or {}).get("dimensions") or {}).get(key) or {}
    return dim.get("label") or _humanised(key)


def field_label(key: str, default: str, division: str = "", policy: dict | None = None) -> str:
    """The label for one record field, under the division's own vocabulary.

    A dimension field takes the dimension's name; the field justifying it takes
    that name plus "rationale", so renaming a dimension renames its justification
    too. Anything else keeps the label from its field spec.
    """
    dimension = RISK_DIMENSION_FIELDS.get(key)
    if dimension:
        return dimension_label(dimension, division, policy)
    dimension = RISK_RATIONALE_FIELDS.get(key)
    if dimension:
        return dimension_label(dimension, division, policy) + " rationale"
    return default


__all__ = ["dimension_label", "field_label"]
