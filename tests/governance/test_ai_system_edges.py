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
"""The AI System's edges: the refusals, and the readers that answer nothing.

Every branch here is one a reviewer meets on a bad day rather than a good one -- a
record that is not there, a threshold set on something that is not a property, a
release with no name, an envelope built from three runs where one reported a score
of "n/a". They were the last uncovered lines in the aggregate, and they are worth
covering rather than excusing: a guard nothing exercises is a guard nobody has
checked reads the way it claims to.
"""
from __future__ import annotations

import pytest

from config.governance._ai_baseline import ENVELOPE_OK, ENVELOPE_STALE
from src.governance.ai_system import (get_snapshot, latest_envelope,
                                      reactivate_ai_system, register_ai_system,
                                      retire_ai_system)
from src.governance.ai_system.commands import (add_collection_item,
                                                seal_release_manifest,
                                                set_trigger_threshold,
                                                update_ai_system_field)
from src.governance.ai_system.envelope import (compute_envelope, envelope_status,
                                               percentile)
from src.governance.ai_system.registers import all_failure_modes
from src.governance.ai_system.trajectory import score_trajectory
from src.governance.errors import DomainError

_MINIMUM = {"name": "Client mail summariser", "division": "Risk",
            "owner": "David K Kelly",
            "use_case": "Summarises inbound client correspondence for the desk.",
            "deployment_pattern": "Agentic (tool-using)"}


def _register(ai_system_id="AIS-0001", **overrides):
    register_ai_system(ai_system_id=ai_system_id, fields={**_MINIMUM, **overrides},
                       actor="admin")
    return ai_system_id


# --- Reactivation ------------------------------------------------------------

def test_reactivating_something_that_was_never_registered_is_refused():
    with pytest.raises(DomainError, match="does not exist"):
        reactivate_ai_system(ai_system_id="AIS-NOPE", actor="admin")


def test_reactivating_a_live_ai_system_is_refused():
    # Not a no-op: "reactivate" on a system already in the estate means somebody has
    # misread its state, and answering OK would confirm the misreading.
    _register()
    with pytest.raises(DomainError, match="is not retired"):
        reactivate_ai_system(ai_system_id="AIS-0001", actor="admin")


def test_a_retired_ai_system_comes_back():
    _register()
    retire_ai_system(ai_system_id="AIS-0001", actor="admin")
    reactivate_ai_system(ai_system_id="AIS-0001", actor="admin")
    # And having come back it can be retired again -- the guard is on state, not on
    # having been retired once.
    retire_ai_system(ai_system_id="AIS-0001", actor="admin")


# --- Percentile and the envelope ---------------------------------------------

def test_a_single_run_is_its_own_percentile():
    # One value has no interval to interpolate across, and every percentile of it is
    # that value. The envelope refuses this few runs separately; percentile itself
    # must not divide by zero on the way there.
    assert percentile([0.42], 5) == 0.42
    assert percentile([0.42], 95) == 0.42


def test_percentile_interpolates_between_the_two_values_either_side():
    assert percentile([0.0, 1.0], 50) == 0.5
    assert percentile([0.0, 10.0, 20.0], 25) == 5.0


def test_an_envelope_that_is_not_OK_is_returned_untouched():
    # Staleness is only a question for an envelope that measured something. One that
    # never had enough runs is already reporting the more serious problem, and
    # relabelling it stale would hide that.
    refused = {"status": "too few runs", "runs": 2, "config_version": 1}
    assert envelope_status(refused, 7) == refused


def test_an_OK_envelope_measured_under_another_configuration_goes_stale():
    ok = {"status": ENVELOPE_OK, "config_version": 1, "low": 0.1, "high": 0.9}
    assert envelope_status(ok, 1)["status"] == ENVELOPE_OK
    assert envelope_status(ok, 2)["status"] == ENVELOPE_STALE


# --- Readers with nothing to return ------------------------------------------

def test_a_snapshot_that_was_never_taken_reads_as_None():
    _register()
    assert get_snapshot("AIS-0001", 99) is None


def test_an_ai_system_with_no_envelope_reads_as_None():
    _register()
    assert latest_envelope("AIS-0001") is None


def test_the_failure_mode_register_can_be_read_whole():
    # The by-risk reader answers "what can go wrong with THIS", and the register
    # screen needs "what can go wrong at all". Both read the same view.
    every = all_failure_modes()
    assert isinstance(every, list)
    assert all("entry_id" in row for row in every)


# --- Trajectory ---------------------------------------------------------------

def test_an_agentic_system_with_no_trajectory_either_way_says_so():
    # Neither observed nor expected: applicable, because the system is agentic, but
    # with nothing to compare. "No data" and "matches perfectly" must not read alike.
    verdict = score_trajectory({"deployment_pattern": "Agentic (tool-using)"}, [], [])
    assert verdict["applies"] is True
    assert verdict["status"] == "no data"
    assert verdict["distance"] is None
    assert verdict["similarity"] is None


# --- Guards on a record that is not there, or a value that is not one ----------

def test_editing_a_field_on_something_unregistered_is_refused():
    # The shared editable guard. Every command routes through it, so this is the one
    # place the "does not exist" refusal has to read correctly.
    with pytest.raises(DomainError, match="does not exist"):
        update_ai_system_field(ai_system_id="AIS-NOPE", field="owner",
                               value="Someone", actor="admin")


def test_filing_a_signoff_item_against_nothing_is_refused():
    # Sign-off collections are reachable on a retired system -- ratifying the
    # retirement is itself a sign-off -- so they skip the editable guard and check
    # existence on their own. That separate check needs its own test.
    with pytest.raises(DomainError, match="does not exist"):
        add_collection_item(ai_system_id="AIS-NOPE", collection="signoff_requests",
                            fields={"kind": "owner"}, actor="admin")


def test_a_threshold_on_something_that_is_not_a_trigger_property_is_refused():
    # "tone" is a dimension the ACE scores, not a property a trigger fires on. Setting
    # a number against it would look configured and never fire.
    _register()
    with pytest.raises(DomainError, match="not a trigger property: tone"):
        set_trigger_threshold(ai_system_id="AIS-0001", property_name="tone",
                              threshold=0.5, fallback="Refuse and escalate",
                              actor="admin")


def test_a_release_manifest_needs_a_name():
    _register()
    with pytest.raises(DomainError, match="a release needs a name"):
        seal_release_manifest(ai_system_id="AIS-0001", release="   ",
                              change_class="Bounded", actor="admin")


def test_a_score_that_is_not_a_number_is_skipped_rather_than_fatal():
    # A run that reported "n/a" is a missing measurement, not a corrupt batch. It is
    # dropped and the remaining runs are counted -- and the run count that results is
    # what the minimum-runs refusal is judged against, so the drop is visible.
    envelope = compute_envelope([0.1, "n/a", 0.5, None, 0.9], config_version=1)
    assert envelope["runs"] == 3
