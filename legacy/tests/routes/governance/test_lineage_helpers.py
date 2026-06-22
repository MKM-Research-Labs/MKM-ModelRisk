# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Unit tests for governance lineage helper functions (_check_staleness, _trace_data)."""

import pathlib

import pytest

from tests.routes.governance.lineage_shared import (
    SAMPLE_LINEAGE,
    create_fresh_file,
    create_stale_file,
)


# ══════════════════════════════════════════════════════════════════
# _check_staleness helper tests
# ══════════════════════════════════════════════════════════════════


class TestCheckStaleness:
    """Unit tests for _check_staleness helper."""

    def test_all_missing(self, lineage_env, monkeypatch):
        """All pipeline steps missing produces 'missing' statuses."""
        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(lineage_env["tmp_path"]))
        from routes.governance.lineage import _check_staleness
        from routes.governance.lineage._trace import _PIPELINE_STEPS

        results = _check_staleness(None)
        assert len(results) == len(_PIPELINE_STEPS)
        for r in results:
            assert r["status"] == "missing"
            assert "Output not found on disk" in r["issues"]
            assert r["last_run"] is None

    def test_fresh_file(self, lineage_env, monkeypatch):
        """A recently modified file is reported as 'fresh'."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_fresh_file(tmp, "gauge.json")
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        gauge_step = next(r for r in results if r["step"] == "gauges")
        assert gauge_step["status"] == "fresh"
        assert gauge_step["last_run"] is not None
        assert gauge_step["issues"] == []

    def test_stale_file(self, lineage_env, monkeypatch):
        """A file older than 72 hours is reported as 'stale'."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_stale_file(tmp, "property.json", days_old=5)
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        prop_step = next(r for r in results if r["step"] == "properties")
        assert prop_step["status"] == "stale"
        assert len(prop_step["issues"]) == 1
        assert "ago" in prop_step["issues"][0]

    def test_directory_step_fresh(self, lineage_env, monkeypatch):
        """A directory step checks most recent file mtime."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        # gaugehd/ is a directory step
        create_fresh_file(tmp, "gaugehd/GAUGE-001.json")
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        assert ghd_step["status"] == "fresh"

    def test_directory_step_stale(self, lineage_env, monkeypatch):
        """A directory with only old files is stale."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_stale_file(tmp, "gaugehd/GAUGE-001.json", days_old=10)
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        assert ghd_step["status"] == "stale"

    def test_empty_directory_is_missing(self, lineage_env, monkeypatch):
        """An empty directory counts as missing."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        (tmp / "gaugehd").mkdir()
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        assert ghd_step["status"] == "missing"

    def test_manifest_last_run_used(self, lineage_env, monkeypatch):
        """If lineage manifest has last_run, it is carried through."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        lineage = {
            "steps": {
                "gauges": {"last_run": "2026-03-01T12:00:00"},
            }
        }
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(lineage)
        gauge_step = next(r for r in results if r["step"] == "gauges")
        assert gauge_step["last_run"] == "2026-03-01T12:00:00"

    def test_manifest_last_run_not_overwritten_by_mtime(self, lineage_env, monkeypatch):
        """If manifest has last_run AND file exists, manifest last_run is kept."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_fresh_file(tmp, "gauge.json")
        lineage = {"steps": {"gauges": {"last_run": "2026-01-01T00:00:00"}}}
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(lineage)
        gauge_step = next(r for r in results if r["step"] == "gauges")
        # Manifest last_run is preserved (not overridden by filesystem mtime)
        assert gauge_step["last_run"] == "2026-01-01T00:00:00"

    def test_hidden_files_ignored_in_directory(self, lineage_env, monkeypatch):
        """Dotfiles in directories are ignored."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        ghd = tmp / "gaugehd"
        ghd.mkdir()
        (ghd / ".DS_Store").write_text("")
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        # Only hidden files = effectively empty
        assert ghd_step["status"] == "missing"


# ══════════════════════════════════════════════════════════════════
# _trace_data helper tests
# ══════════════════════════════════════════════════════════════════


class TestTraceData:
    """Unit tests for _trace_data helper.

    The trace function now searches actual data files on disk, so these
    tests use tmp_path + monkeypatch to provide isolated test data.
    """

    @pytest.fixture
    def trace_env(self, tmp_path, monkeypatch):
        """Create a minimal data directory for trace testing."""
        import json
        from config import config

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        classifiers_dir = tmp_path / "classifiers"
        classifiers_dir.mkdir()
        blotter_dir = tmp_path / "blotter"
        blotter_dir.mkdir()
        (blotter_dir / "eod").mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
        monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
        monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

        # gauge.json with one gauge
        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-TEST01"}}}
            ]}, f)

        # gaugehc.json referencing the gauge
        with open(input_dir / "gaugehc.json", "w") as f:
            json.dump({"hazard_curves": {"GAUGE-TEST01": {"gev": {}}}}, f)

        # gaugets/ per-gauge file
        (input_dir / "gaugets").mkdir()
        with open(input_dir / "gaugets" / "GAUGE-TEST01.json", "w") as f:
            json.dump({"gauge_id": "GAUGE-TEST01"}, f)

        # classifier .joblib
        (classifiers_dir / "GAUGE-TEST01.joblib").write_bytes(b"fake")

        # property.json
        with open(input_dir / "property.json", "w") as f:
            json.dump({"properties": [
                {"PropertyHeader": {"Header": {"PropertyID": "PROP-TEST01"}}}
            ]}, f)

        # propertyts/
        (input_dir / "propertyts").mkdir()
        with open(input_dir / "propertyts" / "PROP-TEST01.json", "w") as f:
            json.dump({"property_id": "PROP-TEST01"}, f)

        # prs/ trade
        (input_dir / "prs").mkdir()
        with open(input_dir / "prs" / "PRS-TEST01.json", "w") as f:
            json.dump({"PhysicalSwap": {
                "Header": {"SwapID": "PRS-TEST01"},
                "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-TEST01"}]},
            }}, f)

        return {"input_dir": input_dir}

    def test_none_lineage_returns_empty(self, trace_env):
        """None lineage with no matching files returns empty."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-NONEXISTENT")
        assert result == []

    def test_gauge_trace_finds_multiple_steps(self, trace_env):
        """Gauge trace should find origin + derived + consumed steps."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-TEST01")
        assert len(result) >= 3, f"Expected >=3 steps, got {len(result)}"
        steps = [r["step"] for r in result]
        assert "gauges" in steps, "Missing gauges origin step"
        assert "hazard" in steps, "Missing hazard derived step"

    def test_gauge_trace_has_context(self, trace_env):
        """Each trace entry should have a context description."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-TEST01")
        for r in result:
            assert r.get("context"), f"Missing context for step {r['step']}"

    def test_property_trace_finds_steps(self, trace_env):
        """Property trace should find origin and derived steps."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "property", "PROP-TEST01")
        assert len(result) >= 2
        steps = [r["step"] for r in result]
        assert "properties" in steps

    def test_trade_trace_finds_origin(self, trace_env):
        """Trade trace should find the PRS file as origin."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-TEST01")
        assert len(result) >= 1
        assert result[0]["role"] == "origin"

    def test_nonexistent_gauge_returns_empty(self, trace_env):
        """Non-existent gauge returns empty trace."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-ZZZZZZZ")
        assert result == []

    def test_gauge_trace_includes_classifier(self, trace_env):
        """Gauge with trained classifier should show classifiers step."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-TEST01")
        steps = [r["step"] for r in result]
        assert "classifiers" in steps

    def test_gauge_trace_includes_prs_trades(self, trace_env):
        """Gauge referenced in PRS trades should show blotter step."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-TEST01")
        consumed = [r for r in result if r["role"] == "consumed"]
        assert len(consumed) >= 1, "No consumed (trade) entries found"
