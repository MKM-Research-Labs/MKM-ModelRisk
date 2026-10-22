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
"""Validation of record fields against the admin reference lists.

Shared by every aggregate that has ``strict_reference`` fields -- the model
inventory's ``type`` and ``vendor``, and an ML Application's ``estimator``. Held
here rather than in one aggregate because the allowed values are rows in the
reference store, so this is the reference package's business and not the
inventory's; a second copy in each aggregate would drift the moment one of them
learned something the other did not.
"""
from __future__ import annotations

from typing import Any

from config.governance import REFERENCE_SPECS
from src.governance.errors import DomainError


def reject_unknown_references(
    specs: dict[str, dict[str, Any]], fields: dict[str, Any], config=None,
) -> None:
    """Reject a value not on the admin list for any ``strict_reference`` field.

    ``specs`` maps a field key to its spec; only fields flagged strict are
    checked -- the others are deliberately open, because they hold names that
    predate the lists and rejecting those would block every edit to an existing
    record.

    An empty list is not enforced: on a fresh database, before the defaults are
    seeded, there is nothing to validate against, and rejecting everything would
    make the field unusable rather than safe.
    """
    from src.governance.reference._store import get_reference_lists

    strict = {key: spec["reference"] for key, spec in specs.items()
              if spec.get("strict_reference") and key in fields
              and str(fields[key] or "").strip()}
    if not strict:
        return
    lists = get_reference_lists(config)
    for key, list_name in strict.items():
        spec = REFERENCE_SPECS[list_name]
        allowed = [item.get(spec.get("display", "value"))
                   for item in lists.get(list_name, ())]
        if allowed and fields[key] not in allowed:
            raise DomainError(
                f"{key} must be one of: {', '.join(str(a) for a in allowed)}")


def _closed_multichoice(field: dict[str, Any]) -> bool:
    """A multi-pick from a vocabulary (an event's Informed roles). Checked here; a
    multi-pick from a register (an action's owners) stays open, as it always was."""
    return (field.get("type") == "multichoice"
            and bool(REFERENCE_SPECS.get(field["reference"], {}).get("value_key")))


def reject_unknown_values(specs: dict[str, Any], collection: str,
                          fields: dict[str, Any], config=None) -> None:
    """Reject a collection-item value that is not on its field's admin list.

    The sibling of ``reject_unknown_references`` for collection items. ``collections``
    is pure and so cannot read the reference store; it therefore skips reference-backed
    choices and they are checked here, against the vocabulary as it actually stands
    rather than against the words that shipped.

    An empty list is not enforced, exactly as above: before the defaults are seeded
    there is nothing to validate against, and rejecting everything would make the
    field unusable rather than safe.
    """
    from src.governance.reference._store import get_reference_lists

    spec = (specs or {}).get(collection) or {}
    checkable = [f for f in spec.get("fields", ())
                 if f.get("reference") and f["key"] in fields and fields[f["key"]]
                 and (f.get("type") == "choice" or _closed_multichoice(f))]
    if not checkable:
        return
    lists = get_reference_lists(config)
    for field in checkable:
        list_name = field["reference"]
        list_spec = REFERENCE_SPECS.get(list_name, {})
        key = list_spec.get("value_key") or list_spec.get("display", "value")
        allowed = [item.get(key) for item in lists.get(list_name, ())]
        held = fields[field["key"]]
        picked = held if isinstance(held, list) else [held]
        if allowed and any(str(v).strip() and v not in allowed for v in picked):
            raise DomainError(
                f"{field['label']} must be one of: "
                f"{', '.join(str(a) for a in allowed)}")


def live_choice_values(spec: dict[str, Any], config=None) -> tuple:
    """What a choice field may actually hold, as its admin list stands today.

    The scalar sibling of ``reject_unknown_values``, and the mirror of the console's
    ``resolve_field``: a field whose ``reference`` names a list with entries takes its
    allowed values from that list, and keeps the options it shipped with only while the
    list is empty. Both sides now decide by ONE rule.

    They decided by two until 2026-09-09, and the two disagreed. ``resolve_field``
    promoted a field's options to the admin list's values, so the dropdown offered
    whatever an institution had curated; validation read ``FIELD_CHOICES``, derived from
    the tuple the platform shipped. A lifecycle stage an adopter added was therefore
    offered on every screen and refused on save -- the failure the comment above
    ``VALID_LIFECYCLE_STAGES`` predicted and nothing closed.

    A status vocabulary stores its ``value`` and shows its ``label``, so values are read
    under ``value_key`` where the spec names one; every other list stores what it shows.

    An empty list falls back to the shipped options rather than to "anything goes". That
    is what ``resolve_field`` does on the console, and it keeps the vocabulary closed on
    a database whose lists have never been seeded -- which is exactly how an estate
    acquires "Production", "production" and "Prod".
    """
    from src.governance.reference._store import get_reference_lists

    options = tuple(spec.get("options") or ())
    reference = spec.get("reference")
    if not reference:
        return options
    ref_spec = REFERENCE_SPECS.get(reference) or {}
    key = ref_spec.get("value_key") or ref_spec.get("display", "value")
    values = tuple(item[key] for item in get_reference_lists(config).get(reference, ())
                   if item.get(key))
    return values or options
