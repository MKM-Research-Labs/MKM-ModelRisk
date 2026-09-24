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
"""An AI System's grid position and property coverage, as its committee is shown them.

Read off the row the projection already resolves (``grid`` and ``coverage``) and flattened
into the three text fields a sign-off request and its agenda item carry — see
``config/governance/_committee_context.py`` for why it travels with the request rather
than changing where the request goes. Pure.
"""
from __future__ import annotations

from typing import Any


def committee_context(row: dict[str, Any] | None) -> dict[str, str]:
    """``{grid_position, governance_intensity, property_coverage}`` for one AI System.

    An unplaced system says so and what it is missing, rather than sending the committee
    an empty cell it might read as "nothing to see".
    """
    grid = (row or {}).get("grid") or {}
    coverage = (row or {}).get("coverage") or {}
    position = grid.get("position") or ""
    if not grid.get("placed") and grid.get("missing"):
        position = f"{position} — missing {', '.join(grid['missing'])}"
    parts = []
    for prop, verdict in (coverage.get("properties") or {}).items():
        gaps = verdict.get("gaps") or []
        parts.append(f"{prop}: {verdict.get('status')}"
                     + (f" (gaps: concepts {', '.join(map(str, gaps))})" if gaps else ""))
    return {"grid_position": position,
            "governance_intensity": grid.get("intensity") or "",
            "property_coverage": "; ".join(parts)}


__all__ = ["committee_context"]
