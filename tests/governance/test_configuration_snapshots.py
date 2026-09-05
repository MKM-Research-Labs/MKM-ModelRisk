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
"""Configuration snapshots: what the system was running, version by version.

The record says what the configuration is NOW. Without a history, "why did the answers
change in March" is unanswerable — the fields moved and nothing recorded what they moved
from. A snapshot is that record, and it is only worth anything if it cannot be edited
afterwards.
"""
from __future__ import annotations

import pytest

from config.governance._ai_system import CONFIGURATION_FIELDS
from src.governance.ai_system import (get_ai_system, list_snapshots,
                                      rebuild_ai_system_view,
                                      rebuild_configuration_snapshot_view,
                                      register_ai_system, retire_ai_system,
                                      take_configuration_snapshot,
                                      update_ai_system_field)
from src.governance.ai_system._rules import diff_snapshots
from src.governance.errors import DomainError

_MINIMUM = {"name": "Claims triage agent", "division": "Risk", "owner": "A",
            "use_case": "Triages claims.", "deployment_pattern": "Direct prompting",
            "pinned_version": "claude-opus-4", "sampling_params": "temperature=0.2"}


def _register(ai_system_id="AIS-1", **overrides):
    register_ai_system(ai_system_id=ai_system_id, fields={**_MINIMUM, **overrides},
                       actor="admin")
    rebuild_ai_system_view()
    return ai_system_id


def _snapshot(ai_system_id="AIS-1", **kw):
    take_configuration_snapshot(ai_system_id=ai_system_id, actor="admin", **kw)
    rebuild_configuration_snapshot_view()


def _versions(ai_system_id="AIS-1"):
    return [r["config_version"] for r in list_snapshots(ai_system_id)]


# --- Retrievable and diffable -------------------------------------------------

def test_two_snapshots_are_individually_retrievable_and_diffable():
    _register()
    _snapshot(taken_at="2026-03-01")
    update_ai_system_field(ai_system_id="AIS-1", field="pinned_version",
                           value="claude-opus-5", actor="admin")
    update_ai_system_field(ai_system_id="AIS-1", field="sampling_params",
                           value="temperature=0.7", actor="admin")
    rebuild_ai_system_view()
    _snapshot(taken_at="2026-06-01")

    rows = list_snapshots("AIS-1")
    assert [r["config_version"] for r in rows] == [1, 2]
    assert rows[0]["taken_at"] == "2026-03-01"

    moved = diff_snapshots(rows[0]["data"], rows[1]["data"])
    assert {d["field"] for d in moved} == {"pinned_version", "sampling_params"}
    pinned = next(d for d in moved if d["field"] == "pinned_version")
    assert (pinned["before"], pinned["after"]) == ("claude-opus-4", "claude-opus-5")


def test_a_snapshot_captures_the_whole_configuration_not_only_what_moved():
    """A snapshot is a reading of the configuration, so a later diff can be taken
    against any earlier one — not only against its immediate predecessor."""
    _register()
    _snapshot()
    values = list_snapshots("AIS-1")[0]["data"]["values"]
    assert set(values) == set(CONFIGURATION_FIELDS)


def test_the_snapshot_reads_the_record_rather_than_trusting_a_caller():
    """A snapshot whose contents the caller supplied would be a claim about the
    configuration. This is a reading of it, and the two differ exactly when it
    matters."""
    _register(pinned_version="claude-opus-4")
    _snapshot()
    assert list_snapshots("AIS-1")[0]["data"]["values"]["pinned_version"] \
        == "claude-opus-4"


# --- Immutable ----------------------------------------------------------------

def test_snapshot_is_immutable_once_written():
    """There is no command that edits or removes one. Later snapshots are appended and
    the earlier ones are untouched — a snapshot somebody could correct afterwards would
    not be evidence of what the configuration was."""
    _register()
    _snapshot(taken_at="2026-03-01")
    first = list_snapshots("AIS-1")[0]["data"]

    update_ai_system_field(ai_system_id="AIS-1", field="pinned_version",
                           value="claude-opus-5", actor="admin")
    rebuild_ai_system_view()
    _snapshot(taken_at="2026-06-01")

    unchanged = list_snapshots("AIS-1")[0]["data"]
    assert unchanged == first, "taking a new snapshot rewrote an earlier one"
    assert unchanged["values"]["pinned_version"] == "claude-opus-4"


def test_an_unchanged_configuration_is_refused_a_new_version():
    """Two identical snapshots a month apart say the configuration did not move, which
    the absence of a second snapshot says just as well and without inviting "which of
    these is current"."""
    _register()
    _snapshot()
    with pytest.raises(DomainError, match="has not changed"):
        take_configuration_snapshot(ai_system_id="AIS-1", actor="admin")


def test_a_retired_system_takes_no_further_snapshots():
    _register()
    retire_ai_system(ai_system_id="AIS-1", actor="admin")
    with pytest.raises(DomainError, match="retired"):
        take_configuration_snapshot(ai_system_id="AIS-1", actor="admin")


# --- The record and the history agree -----------------------------------------

def test_current_values_agree_with_the_latest_snapshot():
    _register()
    _snapshot()
    data = get_ai_system("AIS-1")["data"]
    latest = list_snapshots("AIS-1")[-1]["data"]["values"]
    for field in CONFIGURATION_FIELDS:
        assert latest[field] == data.get(field), field


def test_editing_the_record_leaves_the_latest_snapshot_behind():
    """Which is the point: the gap between the record and its last snapshot is exactly
    "what has changed since anybody wrote it down"."""
    _register()
    _snapshot()
    update_ai_system_field(ai_system_id="AIS-1", field="guardrails",
                           value="Output filter added", actor="admin")
    rebuild_ai_system_view()

    data = get_ai_system("AIS-1")["data"]
    latest = list_snapshots("AIS-1")[-1]["data"]["values"]
    assert latest["guardrails"] != data.get("guardrails")


def test_snapshots_belong_to_their_own_system():
    _register("AIS-1")
    _register("AIS-2")
    _snapshot("AIS-1")
    _snapshot("AIS-2")
    assert _versions("AIS-1") == [1] and _versions("AIS-2") == [1]
    assert list_snapshots("AIS-1")[0]["ai_system_id"] == "AIS-1"


def test_the_history_survives_a_rebuild_because_it_is_projected_from_the_log():
    _register()
    _snapshot()
    update_ai_system_field(ai_system_id="AIS-1", field="pinned_version", value="v2",
                           actor="admin")
    rebuild_ai_system_view()
    _snapshot()

    rebuild_configuration_snapshot_view()
    assert _versions() == [1, 2]
