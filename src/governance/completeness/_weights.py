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
"""What the division the record belongs to has ratified for its audit.

The single place a division's audit settings and criticality weights are read.
The gaps (what a record is missing) and the denominator (what it holds) must
weigh on the same scale, or a division that re-weights a field would see its
completeness figure computed half on its own weights and half on the firm's --
so both read through here rather than each consulting the config tables.

``audit_policy`` is the ``audit`` section of the division's live risk policy, as
the risk envelope carries it. Any name it does not set reads through to the
firm-wide table, and a name the table does not list to that kind's default.
"""
from __future__ import annotations

from config.governance import AUDIT_POLICY_DEFAULTS
from config.governance._completeness_weights import AUDIT_WEIGHT_SECTIONS


def setting(audit_policy: dict | None, key: str) -> float:
    """One audit setting: the division's if its committee has ratified one, else the
    firm-wide value. Read here rather than at the call sites so a division that has
    set two of seven is scored on those two and the defaults for the rest."""
    value = (audit_policy or {}).get(key)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) \
        else AUDIT_POLICY_DEFAULTS[key]


def criticality(kind: str, name: str, audit_policy: dict | None = None) -> float:
    """The weight of a missing ``kind`` ("field", "collection", "document") ``name``."""
    section = AUDIT_WEIGHT_SECTIONS[kind]
    value = ((audit_policy or {}).get(section["policy_key"]) or {}).get(name)
    # Validated on the way in; checked again here because a policy approved before
    # the validator existed must fall back rather than raise mid-audit.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return section["table"].get(name, section["default"])
