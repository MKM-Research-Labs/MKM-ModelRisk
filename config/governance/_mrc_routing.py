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
"""Which committee a record must reach, and why.

The org hierarchy decides which committees EXIST and which of them covers a given
division or line of business. These rules decide how far up that hierarchy a particular
record has to go before it can be signed off. They are two different questions and were
one: routing looked only at where a record sat, so an agentic AI System with authority
to act sat with the same committee as a spreadsheet lookup in the same team.

**There is no second committee track, and these rules cannot create one.** They only
raise the LEVEL within the structure that already exists — Line of Business, Division,
Company — so an escalated record goes to the institution's own company committee rather
than to an "AI committee" sitting beside it. A parallel track is how AI governance ends
up somewhere the model risk function does not read.

Its own module because ``_mrc.py`` sits exactly on R2's limit.

**Ordered, and first match wins.** Read them as a list somebody could take to a
committee and argue with, top to bottom, most-escalating first. The last rule matches
everything and states the default.
"""
from __future__ import annotations

from typing import Any

# The levels, broadest last-resort first. Ordered because a rule names a MINIMUM: a
# record required at Division may be taken by the Company committee where no division
# one exists, and never by a Line of Business one.
LEVEL_COMPANY = "Company"
LEVEL_DIVISION = "Division"
LEVEL_LINE_OF_BUSINESS = "Line of Business"

# Ascending authority. A committee at or above the required level may take the record.
LEVEL_ORDER = (LEVEL_LINE_OF_BUSINESS, LEVEL_DIVISION, LEVEL_COMPANY)

# What a rule may test. Every one is a field the three governed record types already
# carry under the same name (an AI System's governance half deliberately carries a
# model's field names), except ``deployment_pattern``, which only an AI System has —
# a rule naming it simply never matches the other two.
ROUTING_INPUTS = ("record_type", "materiality", "complexity", "tier",
                  "deployment_pattern", "eu_ai_act_class")

# The rule that applies when nothing else does: no minimum, so the most specific
# committee covering the record's org location takes it — which is exactly the
# behaviour every record had before these rules existed.
NO_MINIMUM = None

ROUTING_RULES: tuple[dict[str, Any], ...] = (
    {
        "name": "prohibited_ai",
        "when": {"eu_ai_act_class": ("Prohibited",)},
        "level": LEVEL_COMPANY,
        "because": "A system classed Prohibited under the EU AI Act is an "
                   "institution-wide matter, whatever division built it.",
    },
    {
        "name": "high_risk_ai",
        "when": {"eu_ai_act_class": ("High risk (Annex III)",)},
        "level": LEVEL_COMPANY,
        "because": "Annex III brings obligations the firm carries as a whole, not the "
                   "division that happens to own the system.",
    },
    {
        "name": "agentic_ai",
        "when": {"record_type": ("ai_system",),
                 "deployment_pattern": ("Agentic (tool-using)", "Multi-agent")},
        "level": LEVEL_COMPANY,
        "because": "A system that can act — call tools, spend, commit the firm — is "
                   "escalated on what it can DO rather than on how it was rated. Its "
                   "materiality is a judgement; its authority is a fact.",
    },
    {
        "name": "mission_critical",
        "when": {"tier": ("1",)},
        "level": LEVEL_COMPANY,
        "because": "Mission-critical records go to the company committee whatever "
                   "produced them. This is the rule that keeps the three record types "
                   "on one footing.",
    },
    {
        "name": "high_materiality",
        "when": {"materiality": ("High",)},
        "level": LEVEL_DIVISION,
        "because": "High materiality is not a line-of-business decision.",
    },
    {
        "name": "ai_by_default",
        "when": {"record_type": ("ai_system",)},
        "level": LEVEL_DIVISION,
        "because": "Even a direct-prompting system reaches the division: the estate is "
                   "new, and a line of business has nowhere to compare one against.",
    },
    {
        "name": "default",
        "when": {},
        "level": NO_MINIMUM,
        "because": "The most specific committee covering the record's org location, "
                   "which is how every record routed before these rules existed.",
    },
)


def matches(rule: dict[str, Any], record: dict[str, Any]) -> bool:
    """Whether a rule's conditions all hold for a record.

    A condition naming a field the record does not carry never matches — that is what
    lets an AI-only rule sit in one ordered list with the others rather than in a
    branch that asks what kind of record it is first.
    """
    for field, allowed in (rule.get("when") or {}).items():
        if str(record.get(field) or "") not in allowed:
            return False
    return True


def rule_for(record: dict[str, Any]) -> dict[str, Any]:
    """The first rule that matches. The last rule matches everything, so there is
    always one and callers never handle a None."""
    for rule in ROUTING_RULES:
        if matches(rule, record):
            return rule
    return ROUTING_RULES[-1]  # pragma: no cover - the default matches everything


def at_least(level: str | None) -> tuple[str, ...]:
    """The committee levels that may take a record requiring ``level``, most specific
    first — so the resolver still prefers the closest committee that is senior enough."""
    if level is None:
        return LEVEL_ORDER
    return LEVEL_ORDER[LEVEL_ORDER.index(level):]


__all__ = ["LEVEL_COMPANY", "LEVEL_DIVISION", "LEVEL_LINE_OF_BUSINESS", "LEVEL_ORDER",
           "NO_MINIMUM", "ROUTING_INPUTS", "ROUTING_RULES", "at_least", "matches",
           "rule_for"]
