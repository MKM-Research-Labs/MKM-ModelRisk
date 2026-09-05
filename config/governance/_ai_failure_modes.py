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
"""The failure-mode register: how a system fails, what detects it, what to do then.

One entry per way the system can fail, identified by the FINOS risk it realises and the
mitigation meant to prevent it. Covers the operational failure modes and the FINOS
agentic security cluster — tool chain manipulation, MCP server compromise, agent state
persistence poisoning, credential harvesting — which are the ones a governance record
has no other place to put.

**There is no mitigation-status field here, and its absence is the design.**

Whether a mitigation is in place is already answered, from documents tagged against the
record, by the FINOS coverage view. A status column here would answer the same question
from a different source — and that is precisely how two registers come to disagree,
after which neither is trusted and the firm is worse off than with one. So an entry
holds only what is SPECIFIC to it: which risk it realises, which mitigation is meant to
prevent it, the trigger that would detect it, and the state to fall back to.

This is the easiest thing in the whole plan to reintroduce by accident, because a status
column looks obviously useful on an empty register. A test asserts the absence.
"""
from __future__ import annotations

FAILURE_MODE_COLLECTION = "failure_modes"

# What the register may NOT carry, named so the guard reads as a rule rather than a
# list of strings somebody happened to exclude. Resolved at read time from the tagged
# documents, exactly as the FINOS coverage view resolves it.
FORBIDDEN_FAILURE_MODE_FIELDS = ("mitigation_status", "status", "control_status",
                                 "mitigated", "in_place", "effectiveness")

FAILURE_MODE_SPEC = {
    FAILURE_MODE_COLLECTION: {"label": "Failure modes", "id_prefix": "FM", "fields": [
        {"key": "description", "label": "How it fails", "type": "textarea",
         "required": True},
        # The FINOS pair. Free text against the catalogue's own identifiers rather than
        # a dropdown, because the catalogue is versioned outside this platform and a
        # fixed list would go stale between releases — the coverage view already reads
        # these identifiers the same way.
        {"key": "finos_risk", "label": "FINOS risk (AIR-...)", "type": "text"},
        {"key": "finos_mitigation", "label": "FINOS mitigation (AIR-PREV/DET-...)",
         "type": "text"},
        # What would tell you it had happened. A failure mode nobody would notice is
        # not a managed risk, and this is the column that says whether anybody would.
        {"key": "trigger", "label": "What detects it", "type": "textarea"},
        # Where the system goes when it fires. A trigger with no stated consequence is
        # a metric; the register exists to hold consequences.
        {"key": "fallback", "label": "Fallback state", "type": "textarea"},
        {"key": "identified_on", "label": "Identified on", "type": "date",
         "stacked": True, "default_today": True},
    ]},
}

__all__ = ["FAILURE_MODE_COLLECTION", "FAILURE_MODE_SPEC",
           "FORBIDDEN_FAILURE_MODE_FIELDS"]
