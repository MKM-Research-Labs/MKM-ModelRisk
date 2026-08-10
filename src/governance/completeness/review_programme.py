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
"""How far the estate has got through its reviews.

Reviewing every model is a programme with its own timetable, not something an owner
can finish this afternoon. Scored as completeness it would mark the whole estate
incomplete on the day the workflow shipped and hold it there for months — a new bar
applied backwards, which reads as decay rather than as the backlog it is.

So the review is reported here instead: how many models have a review under way,
how far each has got, how many stages have been agreed, how many are signed off,
and what is standing in the way. "None started yet" is then a plan with a number
against it rather than a failure with a number against it.
"""
from __future__ import annotations

from config.governance import CHALLENGE_OPEN, REVIEW_STAGES, SIGNED_OFF_REVIEW_STATUS

REVIEW_PROGRESS = "review_progress"
REVIEW_SIGNOFFS = "review_signoffs"
REVIEW_NOTES = "review_notes"
CYCLE_START = "cycle-start"


def _stages_agreed(data: dict) -> set:
    """The stages agreed in the CURRENT cycle — progress reads forward from the
    marker a new review writes, so last year's approvals do not flatter this one."""
    rows = data.get(REVIEW_PROGRESS) or []
    last_marker = -1
    for index, row in enumerate(rows):
        if row.get("stage") == CYCLE_START:
            last_marker = index
    return {row.get("stage") for row in rows[last_marker + 1:]
            if row.get("stage") and row.get("stage") != CYCLE_START}


def _open_challenges(data: dict) -> int:
    notes = data.get(REVIEW_NOTES) or []
    answered = {n.get("resolves") for n in notes if n.get("resolves")}
    return sum(1 for n in notes
               if n.get("kind") == "Challenge" and n.get("item_id") not in answered)


def model_state(model: dict) -> dict:
    """One model's position in the programme."""
    data = model.get("data") or {}
    agreed = _stages_agreed(data)
    signoffs = data.get(REVIEW_SIGNOFFS) or []
    started = bool(data.get(REVIEW_PROGRESS) or signoffs)
    return {
        "entity_id": model["model_id"],
        "entity_name": (data.get("name") or ""),
        "reviewer": data.get("peer_reviewer") or "",
        "trigger": data.get("review_trigger") or "",
        "started": started,
        "stages_agreed": len(agreed),
        "stages_total": len(REVIEW_STAGES),
        "signed_off": bool(signoffs),
        "signed_off_at": (signoffs[-1].get("signed_at") or "")[:10] if signoffs else "",
        "open_challenges": _open_challenges(data),
        "status": data.get("review_status") or "",
    }


def programme(models: list) -> dict:
    """The estate's review programme: a headline, and a row per model under way.

    Models that have not started are counted, not listed — a list of everything
    not yet begun is the inventory, which the reader already has.
    """
    states = [model_state(m) for m in models]
    under_way = [s for s in states if s["started"] and not s["signed_off"]]
    signed = [s for s in states if s["signed_off"]]
    return {
        "records": len(states),
        "not_started": sum(1 for s in states if not s["started"]),
        "under_way": len(under_way),
        "signed_off": len(signed),
        "stages_agreed": sum(s["stages_agreed"] for s in states),
        "stages_possible": len(states) * len(REVIEW_STAGES),
        "open_challenges": sum(s["open_challenges"] for s in states),
        "rows": sorted(under_way + signed,
                       key=lambda s: (-s["signed_off"], -s["stages_agreed"], s["entity_id"])),
    }


__all__ = ["model_state", "programme", "SIGNED_OFF_REVIEW_STATUS"]
