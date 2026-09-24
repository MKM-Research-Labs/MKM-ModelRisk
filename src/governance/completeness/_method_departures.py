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
"""Where a division's scoring basis departs from the firm-wide one.

The appendix prints the firm-wide weights and factors. A division's committee may
ratify its own on its risk policy, and its records are scored on those -- so the
firm-wide tables alone would describe a scoring run that did not happen for that
division. This lists every departure, per division, beside the value it replaced.

It is also the check on the freedom to re-weight: a committee that has softened
its own weights is visible here to every reader of the report, including the
committees that did not.

Read from the rows, which carry the policy each record was scored against, rather
than from the policies themselves: the table then cannot disagree with the scores.
"""
from __future__ import annotations

from config.governance import AUDIT_POLICY_DEFAULTS
from config.governance._completeness_scoring import AUDIT_SETTING_LABELS
from config.governance._completeness_weights import AUDIT_WEIGHT_SECTIONS
from src.governance.completeness._weights import criticality, setting
from src.governance.latex import _para_table

INTRO = (
    "The tables in this appendix are the firm-wide basis. A division's model risk "
    "committee may ratify its own values on the division's risk policy, and that "
    "division's records are scored on them. Every such departure is listed here "
    "beside the firm-wide value it replaces.\n\n"
)
NONE = "No division in this report departs from the firm-wide basis.\n\n"


def _basis_by_division(rows) -> dict[str, dict]:
    """Each division's audit policy, from the first of its records. Every record
    in a division is scored on the same live policy, so any one of them will do."""
    basis: dict[str, dict] = {}
    for row in rows:
        if row.get("division"):
            basis.setdefault(row["division"], row.get("audit_policy") or {})
    return basis


def departures(audit: dict) -> list[list[str]]:
    """``[setting, firm-wide, division's]`` for every value this policy changes.

    Compared by value, not by presence: the seed copies the firm-wide settings
    onto every new policy, so a key being present says nothing about a decision.
    """
    out = []
    for key, firm in AUDIT_POLICY_DEFAULTS.items():
        if setting(audit, key) != firm:
            out.append([AUDIT_SETTING_LABELS[key], f"{firm:.2f}",
                        f"{setting(audit, key):.2f}"])
    for kind, section in AUDIT_WEIGHT_SECTIONS.items():
        for name in sorted(audit.get(section["policy_key"]) or {}):
            firm = section["table"].get(name, section["default"])
            if criticality(kind, name, audit) != firm:
                out.append([f"{section['label']} weight: {name}", f"{firm:.2f}",
                            f"{criticality(kind, name, audit):.2f}"])
    return out


def departures_table(rows) -> str:
    """The appendix subsection body: one row per departure, grouped by division."""
    table = [[division, *departure]
             for division, audit in sorted(_basis_by_division(rows).items())
             for departure in departures(audit)]
    if not table:
        return INTRO + NONE
    return INTRO + _para_table(["Division", "Setting", "Firm-wide", "Division's"], table,
                               [0.22, 0.44, 0.17, 0.17],
                               caption="Division departures from the firm-wide basis")
