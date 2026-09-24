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
"""What an AI System's sign-off carries to its committee: where it sits on the grid.

Spec v0.5 §3.3 (AIGov edition) makes grid position a routing input. Here it is an input
to what the committee is SHOWN, never to which committee it goes to: every record is
signed off by the committee for its division and line of business, and routing on a
record's attributes was removed on 2026-09-06 for good reason (docs/MLGov/
implementation_plan.md §11b; decided again 2026-09-24).

So the position travels with the request. It is copied onto the request when the request
is raised and onto the agenda item when it is attached — the evidence as it stood when
the decision was put to the committee, which is what the minute should record. Set once
and never edited, for that reason.
"""
from __future__ import annotations

COMMITTEE_CONTEXT_KEYS = ("grid_position", "governance_intensity", "property_coverage")

# Immutable on both collections: a request, and the agenda item made from it, say what
# the committee was asked on. ``hidden`` only on the agenda, whose manual add-an-item form
# would otherwise offer three fields nobody should type.
_FIELDS = (
    {"key": "grid_position", "label": "Grid position", "type": "text", "immutable": True},
    {"key": "governance_intensity", "label": "Governance intensity", "type": "text",
     "immutable": True},
    {"key": "property_coverage", "label": "Property coverage", "type": "text",
     "immutable": True},
)
SIGNOFF_REQUEST_CONTEXT_FIELDS = [dict(f) for f in _FIELDS]
AGENDA_CONTEXT_FIELDS = [{**f, "hidden": True} for f in _FIELDS]

__all__ = ["AGENDA_CONTEXT_FIELDS", "COMMITTEE_CONTEXT_KEYS",
           "SIGNOFF_REQUEST_CONTEXT_FIELDS"]
