# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
