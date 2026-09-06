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
"""Segregation of duties: a record's reviewer is not its own owner.

One rule, one implementation, every record type a review can be signed off on. It
lived in ``model_inventory/_rules.py`` and applied to models alone, so an ML
Application or an AI System could be registered with the owner named as its own
reviewer and nothing refused it — while the completeness audit reported the same
arrangement as a finding on all three. The audit was right and the write path was
not.

Checked on BOTH fields rather than only on ``peer_reviewer``: a record with a
distinct reviewer is put in breach just as easily by moving the ownership onto them,
and a rule enforced on one side of a pair is not enforced.

Only the write that CREATES the breach is refused. A record already in breach stays
editable in every other respect — the audit reports it, and locking the record would
leave its owner unable to correct anything else about it, including the thing the
finding asks them to correct.
"""
from __future__ import annotations

from typing import Any

# Imported from the submodule rather than the package aggregate: that file is a
# line under the R2 gate, and thirty-one modules under src/ already reach into
# config.governance._* for a constant only they use.
from config.governance._review import INDEPENDENT_OF
from config.permissions import ENFORCE_REVIEWER_INDEPENDENCE
from src.governance.errors import DomainError
from src.identity import same_person


def validate_independence(field: str, value: Any, held: dict[str, Any],
                          noun: str = "record") -> None:
    """Refuse a write that would make ``noun``'s reviewer its own owner.

    ``noun`` is how the record type reads in the refusal a person is shown — the
    same reason ``Subject`` carries one. "the ai_system's own owner" is what
    string-munging a machine key into an error message gets you.
    """
    if ENFORCE_REVIEWER_INDEPENDENCE == "never" or field not in INDEPENDENT_OF:
        return
    other_field = INDEPENDENT_OF[field]
    counterpart = held.get(other_field)
    if same_person(value, counterpart):
        # Name the role on the OTHER side, not "owner" both ways round. Setting the
        # owner to the reviewer's name used to be refused with "must not be the
        # record's own owner", which is true of nothing and reads as a bug.
        role = "reviewer" if other_field == "peer_reviewer" else "owner"
        raise DomainError(
            f"{field} must not be the {noun}'s own {role}: a review by the owner is "
            f"not an independent one. Name somebody other than {counterpart}.")


__all__ = ["validate_independence"]
