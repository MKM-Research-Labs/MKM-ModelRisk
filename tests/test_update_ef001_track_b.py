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

"""The Track B update to MKM-EF-001 (``scripts.update_ef001_track_b``).

The record was registered at v1.0.0 before Track B existed. This brings it up to
date: a minor version bump and the assumptions, limitations and weakness the
loss layer, non-stationary term structure and decoupled wind carry. The two
properties worth protecting are that the update lands on top of the existing
registration without disturbing it, and that a re-run is a no-op.
"""
from __future__ import annotations

import pytest

from scripts import register_ef001, update_ef001_track_b
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view


def _register_ef001():
    """Register MKM-EF-001 (and its chain neighbours) at v1.0.0, as Stage 5 did."""
    for model_id, name in (("MKM-GH-001", "GEV Hazard"), ("MKM-PR-001", "PRS Pricing")):
        register_model(model_id=model_id, name=name, actor="test")
    rebuild_inventory_view()
    register_ef001.register()


def _data():
    return get_model("MKM-EF-001")["data"]


def test_it_bumps_the_version_and_adds_the_track_b_governance():
    _register_ef001()
    before = _data()
    assert before["version"] == "1.0.0"

    summary = update_ef001_track_b.apply()

    after = _data()
    assert after["version"] == "1.1.0"
    assert summary["version_bumped"] is True
    # The four originals plus the Track B additions.
    assert len(after["assumptions"]) == len(before["assumptions"]) + 1
    assert len(after["limitations"]) == len(before["limitations"]) + 2
    assert len(after["model_weaknesses"]) == len(before["model_weaknesses"]) + 1


def test_the_methodology_records_track_b_without_losing_the_original():
    _register_ef001()
    original = _data()["methodology"]
    update_ef001_track_b.apply()
    updated = _data()["methodology"]
    assert original in updated          # the v1.0.0 description is preserved
    assert "Track B" in updated         # and the extension is described


def test_the_reprices_off_limitation_is_recorded():
    """The governance fact that matters most about Track B — the two reprices
    ship switched off — must be in the limitations register."""
    _register_ef001()
    update_ef001_track_b.apply()
    limitations = " ".join(
        item["description"] for item in _data()["limitations"])
    assert "switched off behind empty registries" in limitations


def test_it_is_idempotent():
    _register_ef001()
    update_ef001_track_b.apply()
    after_first = _data()

    again = update_ef001_track_b.apply()

    assert again == {"version_bumped": False, "assumptions": 0,
                     "limitations": 0, "weaknesses": 0}
    # Nothing was duplicated on the second run.
    assert len(_data()["limitations"]) == len(after_first["limitations"])
    assert len(_data()["assumptions"]) == len(after_first["assumptions"])


def test_it_refuses_when_the_model_is_absent():
    """No silent creation — the update presupposes the registration."""
    with pytest.raises(RuntimeError, match="not registered"):
        update_ef001_track_b.apply()


def test_main_runs_and_reports(capsys):
    _register_ef001()
    assert update_ef001_track_b.main() == 0
    out = capsys.readouterr().out
    assert "MKM-EF-001 -> v1.1.0" in out
