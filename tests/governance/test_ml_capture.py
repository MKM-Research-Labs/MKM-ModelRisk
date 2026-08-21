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
"""A fit reporting itself into the register.

Everything a run knows about itself is a fact rather than a judgement, so a human
retyping it adds nothing but the chance of a typo. What the owner must still write --
why the split does not leak, what the model is for, what it may not be used for --
is refused on purpose: an argument is not captured, it is made.
"""
from __future__ import annotations

import pytest

from config.governance import TRAINING_RUNS_COLLECTION
from config.governance._ml_training import CAPTURABLE_FIELDS, CAPTURED_FIELD
from src.governance.errors import DomainError
from src.governance.ml_application import (get_ml_application,
                                           rebuild_ml_application_view,
                                           register_ml_application)
from src.governance.ml_application.capture import record_train

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
            "estimator": "GradientBoostingClassifier", "use_case": "Ranks applicants."}


def _registered(ml_application_id="MLA-1"):
    register_ml_application(ml_application_id=ml_application_id, fields=_MINIMUM,
                            actor="admin")
    rebuild_ml_application_view()
    return ml_application_id


def _trains(ml_application_id="MLA-1"):
    rebuild_ml_application_view()
    return (get_ml_application(ml_application_id)["data"] or {})[TRAINING_RUNS_COLLECTION]


def test_a_run_reports_itself_and_becomes_a_train():
    _registered()
    record_train(ml_application_id="MLA-1", fit_id="2026-03-03-v1.2",
                 fields={"snapshot_id": "sha256:ab", "metric_test": "0.9557",
                         "random_seed": "20260303"}, actor="ingest:capture")
    train = _trains()[0]
    assert train["fit_id"] == "2026-03-03-v1.2"
    assert train["snapshot_id"] == "sha256:ab"
    assert train["metric_test"] == "0.9557"


def test_reporting_the_same_fit_again_updates_it():
    """A long fit reports as it progresses, and a run that crashes after reporting
    must be able to report again. Neither may leave two trains behind."""
    _registered()
    record_train(ml_application_id="MLA-1", fit_id="f1",
                 fields={"snapshot_id": "sha256:ab"}, actor="ingest:capture")
    record_train(ml_application_id="MLA-1", fit_id="f1",
                 fields={"metric_test": "0.96"}, actor="ingest:capture")
    trains = _trains()
    assert len(trains) == 1
    assert trains[0]["snapshot_id"] == "sha256:ab" and trains[0]["metric_test"] == "0.96"


def test_captured_fields_are_recorded_as_captured_and_accumulate():
    """So a screen can show them read-only and a reviewer can tell a captured value
    from a typed one. A field captured on the first report is still captured after a
    second report that did not mention it."""
    _registered()
    record_train(ml_application_id="MLA-1", fit_id="f1",
                 fields={"snapshot_id": "sha256:ab"}, actor="ingest:capture")
    record_train(ml_application_id="MLA-1", fit_id="f1",
                 fields={"metric_test": "0.96"}, actor="ingest:capture")
    captured = set(_trains()[0][CAPTURED_FIELD].split(","))
    assert {"snapshot_id", "metric_test"} <= captured


def test_the_owners_judgement_is_refused_by_name():
    """A producer that believes it recorded the split rationale, and did not, has been
    told something false about its own evidence. So it is refused, not dropped."""
    _registered()
    with pytest.raises(DomainError, match="the owner's to write"):
        record_train(ml_application_id="MLA-1", fit_id="f1",
                     fields={"split_rationale": "Random, it was fine."},
                     actor="ingest:capture")


def test_a_field_that_is_not_a_training_field_is_refused_by_name():
    _registered()
    with pytest.raises(DomainError, match="not training fields: gpu_temperature"):
        record_train(ml_application_id="MLA-1", fit_id="f1",
                     fields={"gpu_temperature": "81C"}, actor="ingest:capture")


def test_a_train_cannot_arrive_for_an_unregistered_record():
    """A record nobody registered is a record nobody is accountable for."""
    with pytest.raises(DomainError, match="not registered"):
        record_train(ml_application_id="MLA-NOPE", fit_id="f1",
                     fields={"snapshot_id": "x"}, actor="ingest:capture")


def test_what_a_run_may_and_may_not_report():
    """The split is the design: facts about the fit, never the argument about it."""
    for fact in ("snapshot_id", "hyperparameters", "random_seed", "code_commit",
                 "environment", "metric_test", "run_duration"):
        assert fact in CAPTURABLE_FIELDS
    for judgement in ("target_definition", "intended_use", "excluded_use",
                      "split_rationale", "segment_performance", "worst_segment",
                      "attested_by", "reproduced_by"):
        assert judgement not in CAPTURABLE_FIELDS


def test_capture_moves_the_completeness_figure():
    _registered()
    before = (get_ml_application("MLA-1")["data"] or {})["training_completeness"]["filled"]
    record_train(ml_application_id="MLA-1", fit_id="f1",
                 fields={"snapshot_id": "sha256:ab", "row_count": "41200",
                         "metric_test": "0.9583"}, actor="ingest:capture")
    rebuild_ml_application_view()
    after = (get_ml_application("MLA-1")["data"] or {})["training_completeness"]["filled"]
    assert after > before
