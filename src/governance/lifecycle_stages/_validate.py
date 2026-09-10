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
"""Validation of a record's lifecycle stage against its division's ratified list.

Shared by the three registers that carry the field -- the model inventory, ML
Applications and AI Systems. Held here rather than in each aggregate's rules because
the allowed values are a division's ratified policy resolved against the institution's
catalogue, so this is that policy's business and not the inventory's. Three copies would
drift the moment one of them learned something the others did not, which is what
happened to the four ``/fields`` handlers before ``grouped_field_specs`` gathered them.
"""
from __future__ import annotations

from typing import Any

from config.governance import LIFECYCLE_STAGE_FIELD
from src.governance.errors import DomainError
from src.governance.lifecycle_stages._store import stage_labels, stages_for


def reject_unknown_lifecycle_stage(value: Any, division: Any, config=None) -> None:
    """Refuse a stage this division's committee has not agreed to use.

    **Blank passes.** A record must be able to hold no stage at all: a model registers
    without one deliberately, because the platform has no word it could safely put
    there, and the completeness audit is what asks for it later.

    The refusal names the stages by their LABELS, because a person reads it and a list
    of stored values is not what their screen shows them.
    """
    if not str(value or "").strip():
        return
    labels = stage_labels(division or "", config)
    if not labels:
        raise DomainError(
            f"{division or 'this division'} has no lifecycle stages available -- its "
            "MRC has to ratify a list, or the institution a catalogue, before a record "
            "can be put in one")
    if value not in labels:
        offered = ", ".join(label if label == value else f"{label} ({value})"
                            for value, label in labels.items())
        raise DomainError(f"lifecycle stage must be one of: {offered}")


def reject_division_move_out_of_stage(fields: dict, new_division: Any,
                                      config=None) -> None:
    """Refuse to move a record into a division that does not use its stage.

    Divisions choose from one firm-wide catalogue, so a stage does not become a
    different stage on the way across -- which is why this is a check and not, as it is
    for a functional group, a flat refusal to travel at all. The record would simply be
    in a stage its new division's committee has not agreed to use, and nothing on the
    screen would say so: it would be counted, filtered and reported under a stage that
    division does not recognise.

    A record with no stage moves freely, as does one whose stage the target division
    already uses.
    """
    held = str((fields or {}).get(LIFECYCLE_STAGE_FIELD) or "").strip()
    if not held or (fields or {}).get("division") == new_division:
        return
    if held in stages_for(new_division or "", config):
        return
    raise DomainError(
        f"{new_division or 'that division'} does not use the lifecycle stage this "
        f"record is in ({held}) -- move it to a stage they do use, or clear it, "
        "before moving the record")
