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
"""Configuration snapshots: a read model of what the configuration WAS, version by
version.

Projected into its own view rather than read off the AI System's record, because the
questions asked of it are different ones: the record answers "what is the configuration
now", and this answers "what was it in March, and what moved between March and June".
A screen showing a history out of the record would have to pull the whole record to
show one line of it.
"""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.governance.ai_system._state import (EVENT_ENVELOPE_RECORDED,
                                             EVENT_SNAPSHOT_TAKEN)
from src.governance.ai_system.commands import AGGREGATE_TYPE

_VIEW = "configuration_snapshot_view"
_ENVELOPE_VIEW = "variability_envelope_view"
_COLUMNS = ("snapshot_id", "ai_system_id", "config_version", "data", "taken_at")
_ENVELOPE_COLUMNS = ("envelope_id", "ai_system_id", "config_version", "data",
                     "measured_at")


def snapshot_id(ai_system_id: str, config_version: int) -> str:
    """The pair that identifies a snapshot, as one key."""
    return f"{ai_system_id}#{config_version}"


def rebuild_configuration_snapshot_view(config=None) -> int:
    """Rebuild the read model from the event log; return the snapshot count."""
    rows = []
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE or event.event_type != EVENT_SNAPSHOT_TAKEN:
            continue
        payload = event.payload or {}
        version = int(payload.get("config_version") or 0)
        rows.append((snapshot_id(event.aggregate_id, version), event.aggregate_id,
                     version, payload, str(payload.get("taken_at") or "")))
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def list_snapshots(ai_system_id: str, config=None) -> list[dict[str, Any]]:
    """Every snapshot of one system, oldest first."""
    rows = read_view(_VIEW, _COLUMNS, where="ai_system_id", value=ai_system_id,
                     config=config)
    return sorted(rows, key=lambda r: r["config_version"])


def get_snapshot(ai_system_id: str, config_version: int, config=None) -> dict[str, Any] | None:
    rows = read_view(_VIEW, _COLUMNS, where="snapshot_id",
                     value=snapshot_id(ai_system_id, config_version), config=config)
    return rows[0] if rows else None


__all__ = ["current_config_version", "get_snapshot", "latest_envelope",
           "list_snapshots", "rebuild_configuration_snapshot_view",
           "rebuild_variability_envelope_view", "snapshot_id"]


def rebuild_variability_envelope_view(config=None) -> int:
    """Rebuild the envelope read model from the event log; return the count."""
    rows, seen = [], {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE or event.event_type != EVENT_ENVELOPE_RECORDED:
            continue
        payload = event.payload or {}
        # One envelope per system per configuration: re-measuring under the same
        # configuration supersedes rather than accumulates, because two envelopes for
        # one configuration is a question nobody can answer.
        key = (event.aggregate_id, int(payload.get("config_version") or 0))
        seen[key] = payload
    for (ai_system_id, version), payload in seen.items():
        rows.append((f"{ai_system_id}#{version}", ai_system_id, version, payload,
                     str(payload.get("measured_at") or "")))
    return replace_view(_ENVELOPE_VIEW, _ENVELOPE_COLUMNS, rows, config=config)


def latest_envelope(ai_system_id: str, config=None) -> dict[str, Any] | None:
    """The most recently measured envelope for a system, whatever configuration it was
    measured under — its staleness is a question for ``envelope_status``, not a reason
    to hide it."""
    rows = read_view(_ENVELOPE_VIEW, _ENVELOPE_COLUMNS, where="ai_system_id",
                     value=ai_system_id, config=config)
    if not rows:
        return None
    return sorted(rows, key=lambda r: r["config_version"])[-1]["data"]


def current_config_version(ai_system_id: str, config=None) -> int | None:
    taken = list_snapshots(ai_system_id, config=config)
    return taken[-1]["config_version"] if taken else None
