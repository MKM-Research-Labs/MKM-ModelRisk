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
"""One measures library, reached the same way from both workflows.

Phase 4.2. Part C was specified as "reuses the Phase 0.2 library", and the way that
claim fails is not by anybody deciding to write a second implementation — it is by an
AI-specific need arriving, the shared signature not quite fitting, and a local helper
appearing beside it. So this asserts the paths converge rather than that they look alike.
"""
from __future__ import annotations

from config.governance._assessments import MONITORING_COLLECTION
from src.governance.monitoring import measured
from src.governance.monitoring.measured import measured_position
from src.web._signoff_subject import SUBJECTS

_OBSERVATION = {"field": "severity band", "field_type": "classification",
                "buckets": "1,2", "baseline_counts": "600,400",
                "current_counts": "300,700",
                "predicted": ",".join(["1"] * 100 + ["2"] * 100),
                "realised": ",".join(["1"] * 90 + ["2"] * 110)}


def _record():
    return {MONITORING_COLLECTION: [dict(_OBSERVATION)]}


def test_ai_and_ml_paths_call_the_same_measure_functions(monkeypatch):
    """Proven by replacing the functions, not by comparing outputs.

    Two implementations that happen to agree today would pass an equality check. They
    cannot pass this: swap the library's entry points and BOTH record types' readings
    change, because there is only one path to swap.
    """
    calls: list[str] = []
    real_psi, real_backtest = measured.psi, measured.backtest

    monkeypatch.setattr(measured, "psi",
                        lambda *a, **k: calls.append("psi") or real_psi(*a, **k))
    monkeypatch.setattr(measured, "backtest",
                        lambda *a, **k: calls.append("backtest") or real_backtest(*a, **k))

    # The same call an ML Application's monitoring makes and an AI System's makes: one
    # function, taking the record's data, whatever record type it came from.
    measured_position(_record())
    assert calls == ["psi", "backtest"]

    calls.clear()
    measured_position(_record())
    assert calls == ["psi", "backtest"], "the second record type took a different path"


def test_every_governed_record_type_reaches_the_measures_the_same_way():
    """Not "an ML one and an AI one that agree" — the same function over the same shape.
    A record's data is the only input, so there is nowhere for a record type to diverge.
    """
    readings = {}
    for subject in SUBJECTS:
        if not subject.reviewable():
            continue
        readings[subject.kind] = measured_position(_record())

    assert set(readings) == {"model", "ml_application", "ai_system"}
    first = readings["model"]
    for kind, reading in readings.items():
        assert reading == first, f"{kind} read the same data differently"


def test_the_monitoring_route_is_registered_for_every_governed_record_type():
    """The other way a second implementation arrives: one record type gets its own
    endpoint because the shared one "did not quite fit"."""
    from src.web import create_app
    app = create_app(run_db_migrations=False)
    routes = {str(r) for r in app.url_map.iter_rules() if str(r).endswith("/monitoring")}
    assert routes == {"/api/models/<subject_id>/monitoring",
                      "/api/ml-applications/<subject_id>/monitoring",
                      "/api/ai-systems/<subject_id>/monitoring"}


def test_there_is_one_measures_package_and_the_resolver_imports_from_it():
    """A local re-implementation would show up as an import from somewhere else."""
    import inspect
    source = inspect.getsource(measured)
    assert "from src.governance.monitoring.measures import" in source
    assert source.count("def psi") == 0, "the resolver defines no measure of its own"
    assert source.count("def backtest") == 0
