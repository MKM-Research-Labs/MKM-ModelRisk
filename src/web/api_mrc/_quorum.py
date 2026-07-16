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
"""The meeting quorum rule — the single server-side gate shared by the actions
that may only happen once a meeting is quorate (closing it, and signing off /
rejecting a risk-rating request). Mirrors the participants-panel rule in the JS."""
from __future__ import annotations

from typing import Any


def is_quorate(d: dict[str, Any]) -> bool:
    """Is the meeting quorate? Chair + Secretary + N voting members marked
    Attended, per the committee's quorum rule carried onto the meeting
    (non-voting members do not count). Requirements default to Chair + Secretary
    + 2 voting; a committee may relax any of them."""
    parts = {p.get("name"): p for p in (d.get("participants") or [])}
    roster = []
    if d.get("chair"):
        roster.append((d["chair"], "Chair"))
    if d.get("secretary"):
        roster.append((d["secretary"], "Secretary"))
    for n in d.get("voting_members") or []:
        roster.append((n, "Voting"))
    attended: list[str] = []
    seen = set()
    for name, role in roster:
        seen.add(name)
        if ((parts.get(name) or {}).get("status") or "Invited") == "Attended":
            attended.append(role)
    for name, p in parts.items():
        if name not in seen and (p.get("status") or "Invited") == "Attended":
            attended.append(p.get("role") or "Guest")
    req_chair = (d.get("quorum_require_chair") or "Yes") != "No"
    req_sec = (d.get("quorum_require_secretary") or "Yes") != "No"
    try:
        min_voting = int(d.get("quorum_min_voting") or 2)
    except (TypeError, ValueError):
        min_voting = 2
    if req_chair and "Chair" not in attended:
        return False
    if req_sec and "Secretary" not in attended:
        return False
    return attended.count("Voting") >= min_voting
