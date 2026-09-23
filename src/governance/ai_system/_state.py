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
"""Current-state fold for the AI System aggregate (pure, no I/O).

The event names are the one thing here that cannot be changed later: the log is
append-only, so a rename would leave every existing event unreadable by the fold.
Named for the concept rather than for whatever a screen currently calls it -- the
ML Application's display label moved once already and its event names did not have
to move with it.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll
from src.governance.model_class import with_model_class

EVENT_REGISTERED = "AISystemRegistered"
EVENT_FIELD_EDITED = "AISystemFieldEdited"
EVENT_RETIRED = "AISystemRetired"
# A configuration snapshot is APPENDED and never amended: there is no edit or
# remove command for one, and the fold only ever grows the list. That is the whole
# of its immutability — a snapshot somebody could correct afterwards would not be
# evidence of what the configuration was.
EVENT_SNAPSHOT_TAKEN = "ConfigurationSnapshotTaken"
# Appended like a snapshot and for the same reason: an envelope is the record of
# what was measured on a day, under a configuration. A later one does not correct
# it, it succeeds it.
EVENT_ENVELOPE_RECORDED = "VariabilityEnvelopeRecorded"
# One event per PROPERTY, never a set of four. Setting a threshold must move that
# threshold and no other — an event carrying all four would make "we tightened
# robustness" indistinguishable from "we restated the other three", and the four
# are set by different arguments at different times.
EVENT_THRESHOLD_SET = "TriggerThresholdSet"
# Sealed, not saved. A manifest is the statement of what was released, and the
# only thing that makes it worth anything is that it cannot be adjusted after
# somebody asks what was in the release.
EVENT_MANIFEST_SEALED = "ReleaseManifestSealed"
# Retirement is hibernation, not deletion: the committee that ratified the retire
# can ratify bringing the record back, so the flag flips both ways and both
# decisions stay in the log.
EVENT_REACTIVATED = "AISystemReactivated"


@dataclass(frozen=True)
class AISystemState:
    """The reconstructed current state of one AI System."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)
    # Oldest first, so ``config_version`` is the position in this tuple and the latest
    # snapshot is simply the last one.
    snapshots: tuple = ()
    envelopes: tuple = ()
    # property -> the threshold currently in force, folded last-write-wins so the
    # history stays in the log while the state is what applies now.
    thresholds: dict = field(default_factory=dict)
    manifests: tuple = ()


def initial_state() -> AISystemState:
    return AISystemState()


def record_data(state: AISystemState) -> dict[str, Any]:
    """A state as the flat record shape everything downstream reads."""
    data = dict(state.fields)
    with_model_class("AISystem", data)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    data["configuration_snapshots"] = [dict(s) for s in state.snapshots]
    data["variability_envelopes"] = [dict(e) for e in state.envelopes]
    data["trigger_thresholds"] = {k: dict(v) for k, v in state.thresholds.items()}
    data["release_manifests"] = [dict(m) for m in state.manifests]
    return data


def apply(state: AISystemState, event_type: str,
          payload: dict[str, Any]) -> AISystemState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_REGISTERED:
        return AISystemState(exists=True, retired=False, fields=dict(payload))
    if event_type == EVENT_FIELD_EDITED:
        updated = dict(state.fields)
        updated[payload["field"]] = payload["value"]
        return replace(state, fields=updated)
    if event_type == EVENT_SNAPSHOT_TAKEN:
        return replace(state, snapshots=state.snapshots + (dict(payload),))
    if event_type == EVENT_ENVELOPE_RECORDED:
        return replace(state, envelopes=state.envelopes + (dict(payload),))
    if event_type == EVENT_THRESHOLD_SET:
        updated = dict(state.thresholds)
        updated[payload["property"]] = dict(payload)
        return replace(state, thresholds=updated)
    if event_type == EVENT_MANIFEST_SEALED:
        return replace(state, manifests=state.manifests + (dict(payload),))
    if event_type == EVENT_RETIRED:
        # ``retired`` is the fact; the lifecycle stage is the institution's own
        # vocabulary and is not overwritten with a word we chose.
        return replace(state, retired=True)
    if event_type == EVENT_REACTIVATED:
        return replace(state, retired=False)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state


__all__ = ["AISystemState", "initial_state", "record_data", "apply",
           "EVENT_REGISTERED", "EVENT_FIELD_EDITED", "EVENT_RETIRED",
           "EVENT_SNAPSHOT_TAKEN", "EVENT_ENVELOPE_RECORDED",
           "EVENT_THRESHOLD_SET", "EVENT_MANIFEST_SEALED", "EVENT_REACTIVATED"]
