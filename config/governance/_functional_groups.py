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
"""Functional Groups: how a division carves its estate up by function.

A Functional Group says what a record is FOR -- "Storm Generation", "Flood
Simulation", "Instrument Pricer". That is a different question from what it IS,
which Type already answers and which the Product bindings branch on through a
type's ``binding_role``. Nothing branches on a functional group, and that is
precisely why it can be the institution's own vocabulary without the platform
caring what is in it.

The list is per division, because one division's functional carve-up does not
describe another's work, and it is ratified by that division's MRC. That is the
argument the risk policy and the ML review policy are already held to: a carve-up
an administrator can re-cut in the week before an inspection is not one anybody
stands behind. So the storage is ``RatifiedPolicy`` and not a reference list, and
this module holds only the shape.

**A record stores a group's ``id``; a screen shows its ``name``.** Every other
closed vocabulary here learned that the expensive way (see
``docs/design/adopter-configurable-vocabulary.md``): records carrying the
displayed word cannot be renamed without a migration. This field is new, so
nothing carries anything yet and the stable id costs nothing to adopt now. It
matters more here than elsewhere, because renaming a group takes a committee
sitting, and one that orphaned every record in the group would be a poor return on
a sitting.

**There is no default list.** An institution's functional groups are its own and
the platform has no defensible guess, so a division that has ratified nothing has
no groups and its records may hold none. That is also why the register field is a
plain ``choice`` with no static options rather than a reference-backed one: a
reference list falls back to a free-text box while it is empty, which is how an
estate acquires "Storm Generation", "Storm generation" and "Storm Gen" as three
groups.
"""
from __future__ import annotations

# The aggregate a division's list is stored under, and the noun its refusals use.
FUNCTIONAL_GROUPS_AGGREGATE = "FunctionalGroups"
FUNCTIONAL_GROUPS_NOUN = "functional group list"

# The prefix a group's id is minted under (FG-001). This is what records carry.
FUNCTIONAL_GROUP_ID_PREFIX = "FG"

# The field every register carries, named here so no module spells it as a literal.
FUNCTIONAL_GROUP_FIELD = "functional_group"

# The keys a group entry may carry. Closed, because a list is a small document a
# committee ratifies: a mistyped key that silently dropped its value would be
# approved without anybody having seen what was lost.
FUNCTIONAL_GROUP_KEYS = ("id", "name", "description")


def default_functional_groups() -> list[dict]:
    """A division that has ratified nothing has no groups.

    Built fresh on each call rather than shared: callers hold on to what they are
    given, and one shared list would let an edit made for one division reach every
    other division running on the default.
    """
    return []


__all__ = [
    "FUNCTIONAL_GROUPS_AGGREGATE",
    "FUNCTIONAL_GROUPS_NOUN",
    "FUNCTIONAL_GROUP_FIELD",
    "FUNCTIONAL_GROUP_ID_PREFIX",
    "FUNCTIONAL_GROUP_KEYS",
    "default_functional_groups",
]
