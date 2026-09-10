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
"""Backfill: carry the curated lifecycle stages into the catalogue the committee owns.

The stages moved from a flat admin list (Admin > Vocabulary) to a firm-wide catalogue
the Company MRC ratifies -- see docs/design/lifecycle-stages.md. A new ratified policy
seeds a vacuum and never reaches an existing estate, so without this an institution that
had already renamed "Production" to "Live", or added a stage of its own, would find the
catalogue running on the five words the platform ships and its own edits nowhere.

So this builds the first catalogue from **the reference list as it actually stands**,
not from the shipped tuple, and ratifies it:

    python -m scripts.backfill_lifecycle_catalogue            # show the plan
    python -m scripts.backfill_lifecycle_catalogue --apply    # write it

**It ratifies without a meeting, deliberately.** What it carries over is the vocabulary
already in force across the estate -- every record is in one of these stages today.
Asking a committee to ratify the status quo before the feature would work at all is
ceremony, and the event records the backfill as its author so the trail says plainly
that no sitting agreed it. What the committee ratifies is the FIRST CHANGE after this.

Idempotent, and quiet when there is nothing to do:

- A catalogue already approved, or a draft outstanding, is left alone.
- A reference list that still matches the shipped five is left alone: the catalogue's
  own default is those five, so ratifying them would add an event and change nothing.
- An unseeded reference list is left alone for the same reason.

**A stage the estate holds is carried in even if the list no longer offers it.** An
administrator who deleted "Retired" from the list did not delete it from the records
still in it, and a catalogue without it could not be proposed at all (the domain refuses
to drop a stage records hold). Those are reported, so nobody is surprised by a stage
reappearing.

No read model to rebuild: a ratified policy is folded from its own event stream.
"""
from __future__ import annotations

import sys

from config.governance import (DEFAULT_LIFECYCLE_STAGES, LIFECYCLE_STAGE_LIST,
                               default_lifecycle_stages)
from src.governance.lifecycle_stage_catalogue import (approve_lifecycle_catalogue,
                                                      load,
                                                      propose_lifecycle_catalogue,
                                                      stages_in_use)
from src.governance.reference import get_reference_lists

ACTOR = "backfill_lifecycle_catalogue"
REASON = ("Backfill: the lifecycle stages already in force, carried from the admin "
          "list into the catalogue")

# What the platform said each of its own words meant, so a stage that survives from the
# shipped five keeps its description instead of arriving blank.
_SHIPPED_DESCRIPTIONS = {value: description for value, description in DEFAULT_LIFECYCLE_STAGES}


def _from_reference_list(config=None) -> list[dict]:
    """The admin list as catalogue entries, in the order the list is held in.

    Order is what every dropdown offers and is part of what the committee will ratify,
    so it is preserved exactly rather than sorted.
    """
    out: list[dict] = []
    for item in get_reference_lists(config).get(LIFECYCLE_STAGE_LIST, ()):
        value = str(item.get("value") or "").strip()
        if not value:
            continue
        out.append({"value": value,
                    "label": str(item.get("label") or "").strip() or value,
                    "description": _SHIPPED_DESCRIPTIONS.get(value, "")})
    return out


def _carry_in_stages_the_estate_holds(stages: list[dict], config=None) -> list[dict]:
    """Append any stage records are in that the list no longer offers.

    Returned appended rather than merged in place, so they land at the end where a
    reader of the plan sees them as the additions they are.
    """
    known = {stage["value"] for stage in stages}
    for value in sorted(set(stages_in_use(config)) - known):
        stages.append({"value": value,
                       "label": value,
                       "description": _SHIPPED_DESCRIPTIONS.get(value, "")})
    return stages


def _same_as_default(stages: list[dict]) -> bool:
    """Would ratifying this change anything the catalogue does not already say?"""
    default = default_lifecycle_stages()
    return ([(s["value"], s["label"]) for s in stages]
            == [(s["value"], s["label"]) for s in default])


def plan(config=None) -> dict:
    """What the backfill would do, without doing any of it."""
    state = load(config)
    listed = _from_reference_list(config)
    stages = _carry_in_stages_the_estate_holds(list(listed), config)
    carried = [s["value"] for s in stages[len(listed):]]
    if state["state"] == "approved":
        verdict, why = "skip", "a catalogue has already been ratified"
    elif state["draft"] is not None:
        verdict, why = "skip", "a draft is outstanding; decide it before backfilling"
    elif not listed:
        verdict, why = "skip", ("the admin list has never been seeded, so there is "
                                "nothing curated to carry over")
    elif _same_as_default(stages):
        verdict, why = "skip", ("the admin list still matches the words the catalogue "
                                "already defaults to")
    else:
        verdict, why = "ratify", f"{len(stages)} stage(s) carried from the admin list"
    return {"verdict": verdict, "why": why, "stages": stages, "carried": carried,
            "state": state["state"]}


def backfill(*, actor: str = ACTOR, apply: bool = False, config=None) -> dict:
    """Ratify the first catalogue. Writes only when ``apply``; returns the plan either way."""
    result = plan(config)
    if not apply or result["verdict"] != "ratify":
        return result
    propose_lifecycle_catalogue(stages=result["stages"], actor=actor, reason=REASON,
                                config=config)
    approve_lifecycle_catalogue(actor=actor, reason=REASON, config=config)
    result["state"] = load(config)["state"]
    return result


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    apply = "--apply" in argv
    actor = argv[argv.index("--actor") + 1] if "--actor" in argv else ACTOR

    # Which database this actually resolved to, before anything is written. The event
    # log is append-only, so a backfill aimed at the wrong one cannot be undone -- only
    # retired through a committee (coding rule R9).
    from config.database import DatabaseConfig
    print(f"database: {DatabaseConfig.from_env().name}\n")

    result = backfill(actor=actor, apply=apply)
    for stage in result["stages"]:
        mark = "+" if stage["value"] in result["carried"] else " "
        print(f" {mark} {stage['value']:22} shown as {stage['label']}")
    if result["carried"]:
        print(f"\n+ = carried in because records are in it, though the admin list no "
              f"longer offers it: {', '.join(result['carried'])}")
    print(f"\n{result['verdict'].upper()}: {result['why']}")
    if result["verdict"] == "ratify" and not apply:
        print("Nothing written. Re-run with --apply to ratify this catalogue.")
    elif result["verdict"] == "ratify":
        print(f"Ratified. The catalogue is now {result['state']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
