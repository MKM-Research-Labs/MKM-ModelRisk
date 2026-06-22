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

"""Coverage expansion tests for lineage.py — part 1.

Counterparty trace, secondary gauge trace paths, and sequence_gauge fallbacks."""

import json

import pytest


# ======================================================================
# Counterparty trace (lines 289-300)
# ======================================================================


class TestCounterpartyTrace:
    """Exercise the data_type == 'counterparty' branch."""

    def test_counterparty_trace_finds_master_record(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "counterparty", "CTPY-FULL01")
        steps = [r["step"] for r in result]
        assert "counterparties" in steps

    def test_counterparty_trace_finds_prs_trades(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "counterparty", "CTPY-FULL01")
        consumed = [r for r in result if r["role"] == "consumed"]
        assert len(consumed) >= 1

    def test_counterparty_not_found_returns_empty(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "counterparty", "CTPY-ZZZZZ")
        assert result == []


# ======================================================================
# Gauge trace -- secondary data sources (lines 184-186, 199-209,
# 224-225, 230-231)
# ======================================================================


class TestGaugeTraceSecondaryPaths:
    """Exercise gaugehd, sequence_gauge, classifier summary, market_state paths."""

    def test_gauge_trace_includes_gaugehd(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        steps = [r["step"] for r in result]
        assert "gaugehd" in steps

    def test_gauge_trace_includes_sequence_gauge(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        stressm_steps = [r for r in result if r["step"] == "stressm"]
        # Should have gaugets + sequence_gauge
        assert len(stressm_steps) >= 2

    def test_gauge_trace_includes_classifier_summary(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        clf_steps = [r for r in result if r["step"] == "classifiers"]
        # .joblib + training_summary.json
        assert len(clf_steps) >= 2

    def test_gauge_trace_includes_market_state(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        blotter_steps = [r for r in result if r["step"] == "blotter"]
        # market_state + PRS trade
        assert len(blotter_steps) >= 2


class TestGaugeTraceSequenceGaugeFallbacks:
    """Exercise sequence_gauge _index.json and legacy fallbacks."""

    def test_sequence_gauge_index_fallback(self, tmp_path, monkeypatch):
        """When per-gauge file doesn't exist, falls back to _index.json."""
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

        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-IDX01"}}}
            ]}, f)

        # sequence_gauge/ with _index.json referencing gauge but no per-gauge file
        sg_dir = input_dir / "sequence_gauge"
        sg_dir.mkdir()
        with open(sg_dir / "_index.json", "w") as f:
            json.dump({"gauge_ids": ["GAUGE-IDX01"]}, f)

        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-IDX01")
        stressm_steps = [r for r in result if r["step"] == "stressm"]
        assert any("_index.json" in r["file"] for r in stressm_steps)

    def test_sequence_gauge_legacy_fallback(self, tmp_path, monkeypatch):
        """When sequence_gauge/ dir doesn't exist, falls back to legacy file."""
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

        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-LEG01"}}}
            ]}, f)

        # Legacy monolithic file instead of split dir
        with open(input_dir / "sequence_gauge_summary.json", "w") as f:
            json.dump({"gauges": {"GAUGE-LEG01": {"peaks": [3.2]}}}, f)

        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-LEG01")
        stressm_steps = [r for r in result if r["step"] == "stressm"]
        assert any("sequence_gauge_summary" in r["file"] for r in stressm_steps)
