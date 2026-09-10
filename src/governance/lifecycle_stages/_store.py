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
"""Which of the catalogue's stages a division uses, as its MRC last ratified it.

The second of the two layers (see ``config/governance/_lifecycle_stages``). The
catalogue says what words the institution recognises; this says which of them a
division's records may be in, and in what order its dropdowns offer them.

**Empty means the whole catalogue.** A division that has ratified nothing offers every
stage, which is exactly how the estate behaved before either layer existed -- so this
ships without a per-division backfill and without a committee having met. It is also
why ``propose`` refuses an empty list: "we have chosen no stages" and "we have chosen
nothing" would be the same document, and the first would leave a division unable to
file anything.

**The chosen list is intersected with the live catalogue on every read.** That is what
makes a stage dropped from the catalogue disappear from every division at once, rather
than leaving a division naming a word the institution no longer defines. Order is the
division's where it has ratified one, because a committee that arranged its list
arranged it for a reason.
"""
from __future__ import annotations

from config.governance import (DIVISION_STAGES_AGGREGATE, DIVISION_STAGES_NOUN,
                               default_division_stages)
from src.governance.lifecycle_stage_catalogue import catalogue_labels, catalogue_values
from src.governance.ratified_policy import RatifiedPolicy

POLICY = RatifiedPolicy(aggregate_type=DIVISION_STAGES_AGGREGATE,
                        noun=DIVISION_STAGES_NOUN,
                        default=default_division_stages)

AGGREGATE_TYPE = DIVISION_STAGES_AGGREGATE


def load(division: str, config=None) -> dict:
    """Fold a division's stream into ``{live, draft, state, approved, version}``."""
    return POLICY.load(division, config)


def chosen_stages(division: str, config=None) -> list[str]:
    """What the division has RATIFIED, before the catalogue is applied to it.

    Read by the Admin editor, which has to show a committee what it chose rather than
    what that choice currently resolves to. Empty where nothing has been ratified.
    """
    return list(POLICY.live(division, config) or ())


def chosen_stages_draft(division: str, config=None) -> list[str] | None:
    """The division's proposal awaiting MRC sign-off, or ``None``.

    It drives nothing: a record cannot be put in a stage that is only proposed.
    """
    draft = POLICY.draft(division, config)
    return None if draft is None else list(draft)


def stages_for(division: str, config=None) -> tuple[str, ...]:
    """The stages a record in ``division`` may actually be in, in the order offered.

    The whole catalogue where the division has ratified nothing; otherwise its own
    ratified order, intersected with the catalogue so a stage the institution has since
    dropped cannot survive here.
    """
    catalogue = catalogue_values(config)
    chosen = chosen_stages(division or "", config)
    if not chosen:
        return catalogue
    live = set(catalogue)
    return tuple(value for value in chosen if value in live)


def stage_labels(division: str, config=None) -> dict[str, str]:
    """``{value: label}`` for the stages this division offers.

    The labels are the CATALOGUE's -- a division chooses its stages, not what they are
    called, so one firm-wide word per stage survives across every division's screens.
    """
    labels = catalogue_labels(config)
    return {value: labels.get(value, value) for value in stages_for(division, config)}
