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
"""The lifecycle stages an institution recognises: the catalogue, and who owns it.

A stage says where a record has got to -- proposed, being built, under validation, in
use, hibernated. The words were hardcoded until 2026-09-09, and hardcoded in two places
that disagreed: the console offered whatever an administrator had curated in Admin and
the domain accepted only the five the platform shipped, so a stage an adopter added was
offered on every screen and refused on save. See docs/design/lifecycle-stages.md.

**Two layers, and the split is the whole design.**

The CATALOGUE here is firm-wide and the Company-level MRC ratifies it: it is the
institution's stage vocabulary, and additions to it are that committee's to agree. A
DIVISION then ratifies which of those stages it uses and in what order (see
``src/governance/lifecycle_stages``). A division cannot coin a stage alone -- which is
exactly what a free per-division vocabulary would have allowed, and how two divisions
come to have "Decommissioning" and "Decommissioned" for the same thing while an
estate-wide count shows them as two stages.

**A record stores the ``value``; every screen shows the ``label``.** That is the
2026-08-10 decision recorded in docs/design/adopter-configurable-vocabulary.md, and it
is what makes this free of migration: the value is seeded to the word records already
carry, so ``"Production"`` is both what is stored today and the label it starts with.
Renaming edits the label and moves nothing in the estate. The value is immutable once
the entry exists, because records already carry it.

The label is deliberately NOT per division. One firm-wide word per stage is most of the
point of having a catalogue: a division that relabelled "Production" would defeat
cross-division reporting at the display layer while appearing not to.
"""
from __future__ import annotations

# The aggregate the catalogue is stored under, and the noun its refusals use. Stored as
# a singleton -- one document for the institution -- under the same ``global`` id
# ``MRCSettings`` and ``ReferenceData`` already use.
LIFECYCLE_CATALOGUE_AGGREGATE = "LifecycleStageCatalogue"
LIFECYCLE_CATALOGUE_NOUN = "lifecycle stage catalogue"
LIFECYCLE_CATALOGUE_SCOPE = "global"

# The field every register carries, named here so no module spells it as a literal.
LIFECYCLE_STAGE_FIELD = "lifecycle_stage"

# --- The second layer: which of the catalogue a division actually uses -------------
#
# Per division, ratified by that division's own MRC. It holds an ordered list of
# catalogue VALUES -- not a second copy of the words, which would be two places to
# rename a stage and one of them would go stale.
#
# The default is EMPTY, and empty means "the whole catalogue, in catalogue order". That
# is what makes this free of migration in its turn: a division that has ratified nothing
# offers every stage, which is exactly how the estate behaves today, so the layer can
# ship before a single committee has met. An empty list is refused at propose time for
# the same reason -- ratifying "no stages" would be indistinguishable from having
# ratified nothing, and it would leave a division unable to file anything.
DIVISION_STAGES_AGGREGATE = "DivisionLifecycleStages"
DIVISION_STAGES_NOUN = "division lifecycle stage list"


def default_division_stages() -> list[str]:
    """What a division that has ratified nothing has chosen: nothing, which is read
    as the whole catalogue (see ``lifecycle_stages.stages_for``)."""
    return []


# The keys a catalogue entry may carry. Closed, because the catalogue is a small
# document a committee ratifies: a mistyped key that silently dropped its value would
# be approved without anybody having seen what was lost.
LIFECYCLE_STAGE_KEYS = ("value", "label", "description")

# What the institution starts with, and what a division that has ratified nothing runs
# on. NOT empty, unlike the functional groups: every record in the estate already
# carries one of these words, so an empty default would orphan the lot. These are the
# five the platform has always shipped, in the order every dropdown has always offered
# them, which is what makes adopting the catalogue free of migration.
#
# The descriptions are the platform's account of the words IT shipped, not a claim
# about what they mean in any adopter's estate. A committee rewrites them; that is what
# the field is for, and there was nowhere to record any of this before.
DEFAULT_LIFECYCLE_STAGES = (
    # Where a model sits once it is proposed but not yet started -- a submitted bid, an
    # approved business case awaiting kickoff. First because the list is read in order
    # and the order is what every dropdown offers.
    ("Pre Development", "Proposed, and not yet started: a submitted bid, or an approved "
                        "business case awaiting kickoff."),
    ("Development", "Being built. Its methodology and code are still moving."),
    ("Validation", "Built, and under independent review before it may be used."),
    ("Production", "In use. Results from it reach decisions, reports or customers."),
    ("Retired", "Hibernated: out of use and out of the active estate, but kept as a "
                "record. Retiring is the committee's decision, not the owner's."),
)


# The stages as a bare tuple, derived rather than written a second time. This is the
# vocabulary the whole platform used to be built on, and it lived in ``_inventory``
# beside the field it served -- which stopped making sense once the stages became a
# ratified policy of their own and that module was two subjects rather than one.
# Re-exported from ``_inventory`` so every existing import goes on working.
VALID_LIFECYCLE_STAGES = tuple(value for value, _description in DEFAULT_LIFECYCLE_STAGES)

# The admin list the stages used to be held in. Superseded by the catalogue and kept
# only until the backfill has carried an institution's curated words across; named here
# now rather than in ``_inventory``, beside everything else about the stages.
LIFECYCLE_STAGE_LIST = "lifecycle_stage"


def default_lifecycle_stages() -> list[dict]:
    """The catalogue an institution that has ratified nothing runs on.

    Built fresh on each call rather than shared: callers hold on to what they are given,
    and one shared list would let an edit made in one place reach every other reader of
    the default.

    ``label`` is seeded to the ``value`` -- the same word -- because that is the whole
    of the migration-free guarantee: nothing in the estate has to move for the catalogue
    to become live, and a rename afterwards touches only the label.
    """
    return [{"value": value, "label": value, "description": description}
            for value, description in DEFAULT_LIFECYCLE_STAGES]


__all__ = [
    "DEFAULT_LIFECYCLE_STAGES",
    "LIFECYCLE_STAGE_LIST",
    "VALID_LIFECYCLE_STAGES",
    "DIVISION_STAGES_AGGREGATE",
    "DIVISION_STAGES_NOUN",
    "LIFECYCLE_STAGE_FIELD",
    "LIFECYCLE_CATALOGUE_AGGREGATE",
    "LIFECYCLE_CATALOGUE_NOUN",
    "LIFECYCLE_CATALOGUE_SCOPE",
    "LIFECYCLE_STAGE_KEYS",
    "default_division_stages",
    "default_lifecycle_stages",
]
