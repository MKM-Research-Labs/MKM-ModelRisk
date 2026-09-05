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
"""Baseline and release decisions for an AI System: snapshots, envelopes, thresholds,
manifests.

Split from ``_rules``, which holds what a record IS — registering it, editing a field,
retiring it, keeping its registers. What is here is what happens to it over time: the
configuration it ran under, how much it varied, the bars it has to clear, and what was
sealed at a release. The two grew apart as Phases 3 to 5 landed, and they are read by
different people: the first by whoever maintains the record, these by whoever has to
explain a release.

Pure, like ``_rules``: no I/O, and every refusal is a DomainError with the reason in it.
"""
from __future__ import annotations

from typing import Any

from config.governance._ai_system import CONFIGURATION_FIELDS
from src.governance.ai_system._state import (EVENT_ENVELOPE_RECORDED,
                                             EVENT_MANIFEST_SEALED,
                                             EVENT_SNAPSHOT_TAKEN,
                                             EVENT_THRESHOLD_SET, AISystemState)
from src.governance.errors import DomainError


def _require_editable(state: AISystemState) -> None:
    """Same guard the record's own rules apply, and deliberately not imported from
    them: a circular import between two halves of one aggregate's rules is a worse
    problem than four lines repeated."""
    if not state.exists:
        raise DomainError("AI System does not exist")
    if state.retired:
        raise DomainError("AI System is retired")


def decide_take_snapshot(
    state: AISystemState, *, taken_at: str
) -> tuple[str, dict[str, Any]]:
    """Record the configuration as it stands, as a numbered, immutable version.

    Takes the values from the RECORD rather than from the caller. A snapshot the caller
    supplied the contents of would be a claim about the configuration; this is a reading
    of it, and the two differ exactly when it matters.

    An unchanged configuration is still refused a new version. Two identical snapshots
    a month apart say the configuration did not move, which the absence of a snapshot
    says just as well and without inviting "which of these two is current".
    """
    _require_editable(state)
    values = {field: state.fields.get(field) for field in CONFIGURATION_FIELDS}
    if state.snapshots and state.snapshots[-1].get("values") == values:
        raise DomainError("the configuration has not changed since the last snapshot")
    return EVENT_SNAPSHOT_TAKEN, {
        "config_version": len(state.snapshots) + 1,
        "values": values,
        "taken_at": taken_at,
    }


def diff_snapshots(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    """What moved between two snapshots, field by field.

    Pure, and over the SNAPSHOTS rather than over the record: comparing a snapshot with
    the record's current values would answer a different question ("has it moved since")
    and the two get confused precisely when somebody is trying to explain a change.
    """
    old, new = before.get("values") or {}, after.get("values") or {}
    return [{"field": field, "before": old.get(field), "after": new.get(field)}
            for field in sorted(set(old) | set(new))
            if old.get(field) != new.get(field)]


def decide_record_envelope(
    state: AISystemState, *, scores, measured_at: str, note: str = "",
) -> tuple[str, dict[str, Any]]:
    """Record what N runs under the current configuration showed.

    Refuses where the runs do not support an envelope, rather than recording a narrow
    one — see ``compute_envelope``. The refusal is a DomainError because recording an
    unsupported envelope is not a lesser reading, it is a wrong one.

    Bound to the configuration in force, which is the latest snapshot. A system with no
    snapshot cannot have an envelope: there would be nothing to say what it was measured
    under, and the envelope would outlive any change silently.
    """
    from config.governance._ai_baseline import ENVELOPE_OK
    from src.governance.ai_system.envelope import compute_envelope

    _require_editable(state)
    if not state.snapshots:
        raise DomainError("take a configuration snapshot first: an envelope has to say "
                          "which configuration it was measured under")
    config_version = state.snapshots[-1].get("config_version")
    envelope = compute_envelope(scores, config_version=config_version)
    if envelope["status"] != ENVELOPE_OK:
        raise DomainError(envelope["detail"])
    return EVENT_ENVELOPE_RECORDED, {**envelope, "measured_at": measured_at,
                                     "note": note}


def decide_set_threshold(
    state: AISystemState, *, property_name: str, threshold, fallback: str,
    rationale: str = "", set_at: str,
) -> tuple[str, dict[str, Any]]:
    """Set the bar for ONE property, leaving the other three exactly where they were.

    One property per act, deliberately. The four are set by different arguments — a
    customer-facing system may warrant a tighter robustness bar than its predictability
    bar depending on where the exposure sits — and an interface that took all four at
    once would invite them to be moved together, which is the thing the spec is
    explicit about not wanting.
    """
    from config.governance._ai_triggers import FALLBACK_STATES, is_property

    _require_editable(state)
    if not is_property(property_name):
        raise DomainError(f"not a trigger property: {property_name}")
    try:
        value = float(threshold)
    except (TypeError, ValueError):
        raise DomainError("a threshold must be a number")
    if not 0 <= value <= 1:
        raise DomainError("a threshold is a proportion between 0 and 1")
    if fallback not in FALLBACK_STATES:
        raise DomainError(f"fallback must be one of: {', '.join(FALLBACK_STATES)}")
    return EVENT_THRESHOLD_SET, {
        "property": property_name, "threshold": value, "fallback": fallback,
        "rationale": rationale, "set_at": set_at,
    }


def manifest_digest(contents: dict[str, Any]) -> str:
    """A stable digest of what a manifest seals.

    Over a canonical rendering, so the same contents always hash the same however the
    dictionary was built. The digest is what makes tampering detectable: a manifest
    whose contents were edited no longer matches the digest recorded with it, and the
    log holds both.
    """
    import hashlib
    import json
    canonical = json.dumps(contents, sort_keys=True, separators=(",", ":"),
                           default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def decide_seal_manifest(
    state: AISystemState, *, release: str, change_class: str, sealed_at: str,
    note: str = "",
) -> tuple[str, dict[str, Any]]:
    """Seal what is being released: the configuration, the envelope, and the bars.

    **The four-tier classification is applied here as its primary use.** A release is a
    change, and the tier it was classified as is what says how much revalidation it
    needed — recording it on the manifest is what lets somebody later ask "this was a
    Material release; where is the evidence it was revalidated" without reconstructing
    the answer from three registers.

    Sealed against the CURRENT configuration snapshot, so a manifest always names a
    configuration that exists. Releasing without one is refused: a manifest that could
    not say what was configured would be a release note, not a manifest.
    """
    from config.governance._change import CHANGE_CLASSES

    _require_editable(state)
    if not (release or "").strip():
        raise DomainError("a release needs a name")
    if change_class not in CHANGE_CLASSES:
        raise DomainError(f"change class must be one of: {', '.join(CHANGE_CLASSES)}")
    if not state.snapshots:
        raise DomainError("take a configuration snapshot first: a manifest has to say "
                          "what configuration was released")
    if any(m.get("release") == release for m in state.manifests):
        raise DomainError(f"release {release} is already sealed")

    snapshot = state.snapshots[-1]
    envelope = state.envelopes[-1] if state.envelopes else None
    contents = {
        "config_version": snapshot.get("config_version"),
        "configuration": snapshot.get("values"),
        "envelope": envelope,
        "thresholds": {k: v.get("threshold") for k, v in state.thresholds.items()},
    }
    return EVENT_MANIFEST_SEALED, {
        "release": release, "change_class": change_class, "sealed_at": sealed_at,
        "note": note, "contents": contents, "digest": manifest_digest(contents),
    }


def manifest_intact(manifest: dict[str, Any]) -> bool:
    """Whether a manifest's contents still match the digest sealed with them."""
    return manifest_digest(manifest.get("contents") or {}) == manifest.get("digest")
