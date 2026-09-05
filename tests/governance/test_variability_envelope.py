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
"""The variability envelope, and the two things it refuses to do.

A generative system gives different answers to the same input, and the governance
question is not whether it is deterministic but how much it moves and whether that is
within what was accepted.

The dangerous failure is the flattering one: three runs that happen to agree produce a
tight range that reads like a well-behaved system. So the envelope is REFUSED below the
minimum rather than narrowed, and it goes stale rather than quietly outliving the
configuration it was measured under.
"""
from __future__ import annotations

import pytest

from config.governance._ai_baseline import (ENVELOPE_NO_RUNS, ENVELOPE_OK,
                                            ENVELOPE_PERCENTILES, ENVELOPE_STALE,
                                            ENVELOPE_TOO_FEW_RUNS, MIN_ENVELOPE_RUNS)
from src.governance.ai_system import (latest_envelope, current_config_version,
                                      rebuild_ai_system_view,
                                      rebuild_configuration_snapshot_view,
                                      rebuild_variability_envelope_view,
                                      record_variability_envelope, register_ai_system,
                                      take_configuration_snapshot,
                                      update_ai_system_field)
from src.governance.ai_system.envelope import (compute_envelope, envelope_status,
                                               percentile)
from src.governance.errors import DomainError

_MINIMUM = {"name": "Claims triage agent", "division": "Risk", "owner": "A",
            "use_case": "Triages claims.", "deployment_pattern": "Direct prompting",
            "pinned_version": "claude-opus-4"}
_ENOUGH = [0.80 + (i % 5) / 100 for i in range(MIN_ENVELOPE_RUNS)]


def _register(ai_system_id="AIS-1"):
    register_ai_system(ai_system_id=ai_system_id, fields=dict(_MINIMUM), actor="admin")
    rebuild_ai_system_view()
    take_configuration_snapshot(ai_system_id=ai_system_id, actor="admin")
    rebuild_configuration_snapshot_view()
    return ai_system_id


def _record(ai_system_id="AIS-1", scores=None):
    record_variability_envelope(ai_system_id=ai_system_id,
                                scores=_ENOUGH if scores is None else scores,
                                actor="admin")
    rebuild_variability_envelope_view()


# --- The arithmetic -----------------------------------------------------------

def test_the_percentile_is_the_one_a_reviewer_would_compute_by_hand():
    """Ten values 1..10: the 50th sits between the 5th and 6th, so 5.5."""
    values = [float(i) for i in range(1, 11)]
    assert percentile(values, 50) == 5.5
    assert percentile(values, 10) == 1.9
    assert percentile(values, 90) == 9.1


def test_the_envelope_is_percentiles_not_the_extremes():
    """The extreme of twenty runs is one run's bad day, and an envelope somebody has to
    defend should not be set by it."""
    scores = [0.5] + [0.80] * (MIN_ENVELOPE_RUNS - 2) + [0.99]
    envelope = compute_envelope(scores, config_version=1)
    assert envelope["status"] == ENVELOPE_OK
    limits = envelope["limits"]
    assert min(limits.values()) > 0.5, "the low outlier did not set the floor"
    assert max(limits.values()) < 0.99, "the high outlier did not set the ceiling"
    assert set(limits) == {str(p) for p in ENVELOPE_PERCENTILES}


# --- Refusals -----------------------------------------------------------------

def test_too_few_runs_is_a_stated_refusal():
    """Not a silently narrow envelope. This is the dangerous failure the whole module
    exists to avoid."""
    envelope = compute_envelope([0.80, 0.80, 0.81], config_version=1)
    assert envelope["status"] == ENVELOPE_TOO_FEW_RUNS
    assert envelope["limits"] is None, "a refused envelope states no limits"
    assert str(MIN_ENVELOPE_RUNS) in envelope["detail"]
    assert "flattering" in envelope["detail"]


def test_recording_an_unsupported_envelope_is_refused_by_the_domain():
    _register()
    with pytest.raises(DomainError, match="required before an envelope"):
        record_variability_envelope(ai_system_id="AIS-1", scores=[0.8, 0.8, 0.8],
                                    actor="admin")


def test_no_runs_is_distinct_from_too_few():
    """"Nobody has measured this" and "somebody measured it three times" are different
    findings."""
    assert compute_envelope([], config_version=1)["status"] == ENVELOPE_NO_RUNS


def test_an_envelope_needs_a_configuration_to_have_been_measured_under():
    """Without a snapshot there is nothing to say what it was measured under, and the
    envelope would outlive any change silently."""
    register_ai_system(ai_system_id="AIS-2", fields=dict(_MINIMUM), actor="admin")
    rebuild_ai_system_view()
    with pytest.raises(DomainError, match="snapshot first"):
        record_variability_envelope(ai_system_id="AIS-2", scores=_ENOUGH, actor="admin")


# --- Bound to its configuration ------------------------------------------------

def test_envelope_is_bound_to_its_config_version():
    _register()
    _record()
    envelope = latest_envelope("AIS-1")
    assert envelope["config_version"] == current_config_version("AIS-1") == 1


def test_changing_configuration_invalidates_the_envelope():
    """Marked stale, not deleted: it is the record of what was measured, and deleting
    it would lose that. Stale is a finding; a gap is not."""
    _register()
    _record()
    update_ai_system_field(ai_system_id="AIS-1", field="pinned_version",
                           value="claude-opus-5", actor="admin")
    rebuild_ai_system_view()
    take_configuration_snapshot(ai_system_id="AIS-1", actor="admin")
    rebuild_configuration_snapshot_view()

    envelope = latest_envelope("AIS-1")
    against_now = envelope_status(envelope, current_config_version("AIS-1"))
    assert against_now["status"] == ENVELOPE_STALE
    assert "no longer in force" in against_now["detail"]
    assert against_now["limits"] == envelope["limits"], "the measurement is not erased"


def test_an_envelope_measured_under_the_current_configuration_is_not_stale():
    _register()
    _record()
    assert envelope_status(latest_envelope("AIS-1"),
                           current_config_version("AIS-1"))["status"] == ENVELOPE_OK


def test_remeasuring_under_one_configuration_supersedes_rather_than_accumulates():
    """Two envelopes for one configuration is a question nobody can answer."""
    _register()
    _record()
    _record(scores=[0.9] * MIN_ENVELOPE_RUNS)
    envelope = latest_envelope("AIS-1")
    assert envelope["limits"]["10"] == 0.9, "the later measurement stands"
