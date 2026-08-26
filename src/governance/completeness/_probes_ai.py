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
"""Clause probes that only bite on AI Systems.

The FINOS risk catalogue asks questions no model record can answer -- what
foundation model is pinned, what leaves the firm for inference, which tools an
agent may call. Those rows read Not evidenced for as long as the estate holds no
AI System, and that is correct rather than pessimistic.

**Two population rules, and both matter.**

*An AI-specific clause is scored over AI Systems only.* Counting "is a foundation
model version pinned" across an estate of regression models would report a number
that means nothing, and would drag every such row toward zero as the model
inventory grows. ``_is_ai_system`` narrows the population; a zero population is
reported as Not evidenced with the population said out loud, exactly as elsewhere.

*Some clauses bite only on some AI Systems.* AIR-SEC-024 is about agents exceeding
their authority, and a direct-prompting summariser has no agency to exceed. Scoring
it against one would manufacture a gap the institution cannot close and should not
try to. ``_agentic`` and ``_multi_agent`` narrow those rows further.

The discriminator is ``deployment_pattern``: it is required at registration (see
``AI_SYSTEM_REGISTER_FIELDS``), so every AI System carries it and no model or ML
Application has the field at all. That is a deliberate dependency -- if the field
ever stops being required, these probes silently stop finding their population,
which is why it is written down here rather than left to be inferred.
"""
from __future__ import annotations

from config.governance._ai import DEPLOYMENT_PATTERNS
from src.governance.completeness._gaps import _recorded
from src.governance.completeness._probe_helpers import _any_entries, _filled, _share

# The two patterns that give a system agency. Read from the vocabulary rather than
# spelled out, so renaming one in config does not silently empty these populations.
_AGENTIC_PATTERN = DEPLOYMENT_PATTERNS[3]        # "Agentic (tool-using)"
_MULTI_AGENT_PATTERN = DEPLOYMENT_PATTERNS[4]    # "Multi-agent"


def _is_ai_system(data: dict) -> bool:
    return "deployment_pattern" in data


def _agentic(data: dict) -> bool:
    """A system that can act, rather than only answer."""
    return _is_ai_system(data) and data.get("deployment_pattern") in (
        _AGENTIC_PATTERN, _MULTI_AGENT_PATTERN)


def _multi_agent(data: dict) -> bool:
    return _is_ai_system(data) and data.get("deployment_pattern") == _MULTI_AGENT_PATTERN


def _ai(predicate, applies=_is_ai_system):
    """A probe over the AI Systems on the register."""
    return lambda estate: _share(estate, predicate, applies=applies)


# Each entry answers exactly one FINOS risk row, and is named for the row rather
# than for the field it reads -- the field may be renamed, the question will not.
AI_PROBES = {
    # AIR-OP-005: not "which version" but "can it change under us". Both halves are
    # required, because a pinned version with no policy behind it is an accident.
    "ai_versioning": _ai(lambda d: _filled(d, "pinned_version", "version_policy")),
    # AIR-OP-006
    "ai_determinism": _ai(lambda d: _filled(d, "output_variability")),
    # AIR-OP-004: what stops a confident wrong answer -- grounding, and the human
    # who would catch it. Hallucination is not closed by either alone.
    "ai_grounding": _ai(lambda d: _filled(d, "grounding", "human_oversight")),
    # AIR-OP-017
    "ai_explainability": _ai(lambda d: _filled(d, "explainability_approach")),
    # AIR-OP-007: who supplies it and how it is reached. A system whose provider is
    # unrecorded has no availability story that could be assessed.
    "ai_provider": _ai(lambda d: _filled(d, "provider", "hosting")),
    # AIR-OP-014: alignment is the use case bounded by what the system may not do.
    "ai_alignment": _ai(lambda d: _filled(d, "use_case", "guardrails")),
    # AIR-SEC-010
    "ai_guardrails": _ai(lambda d: _filled(d, "guardrails")),
    # AIR-RC-001: what leaves the firm, and what in the contract permits it.
    "ai_egress": _ai(lambda d: _filled(d, "data_egress", "data_egress_basis")),
    # AIR-SEC-024 / AIR-SEC-025 / AIR-PREV-018: agentic systems only.
    "ai_agency": _ai(lambda d: _any_entries(d, "agent_tools") and _recorded(d.get("human_oversight")),
                     applies=_agentic),
    # AIR-OP-028: multi-agent systems only.
    "ai_multi_agent": _ai(lambda d: _filled(d, "guardrails") and _any_entries(d, "agent_tools"),
                          applies=_multi_agent),
}

__all__ = ["AI_PROBES"]
