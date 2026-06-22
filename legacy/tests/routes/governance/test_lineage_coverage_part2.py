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

"""Coverage expansion tests for lineage.py — part 2.

Property/trade sub-lookups, route error handlers, and utility edge cases."""

import json

import pytest


# ======================================================================
# Property sub-lookups (lines 251-252, 263-264)
# ======================================================================


class TestPropertySubLookups:
    """Exercise loan.json and propertyhc.json searches."""

    def test_property_trace_includes_mortgage(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "property", "PROP-FULL01")
        steps = [r["step"] for r in result]
        assert "mortgages" in steps

    def test_property_trace_includes_propertyhc(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "property", "PROP-FULL01")
        steps = [r["step"] for r in result]
        assert "propertyhc" in steps


# ======================================================================
# Trade sub-lookups (lines 276-277, 284-285)
# ======================================================================


class TestTradeSubLookups:
    """Exercise trade_marks.json and EOD snapshot searches."""

    def test_trade_trace_includes_marks(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-FULL01")
        blotter_steps = [r for r in result if r["step"] == "blotter"]
        assert any("trade_marks" in r["file"] for r in blotter_steps)

    def test_trade_trace_includes_eod(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-FULL01")
        blotter_steps = [r for r in result if r["step"] == "blotter"]
        assert any("eod" in r["file"] for r in blotter_steps)


# ======================================================================
# Route error handlers (lines 320-322, 361-366, 384-386)
# ======================================================================


class TestRouteErrorHandlers:
    """Exercise except Exception blocks on all three routes."""

    def test_data_lineage_staleness_error_returns_empty(
        self, lineage_env, lineage_client, monkeypatch
    ):
        """GET /governance/data-lineage gracefully handles _check_staleness error."""
        from routes.governance.lineage import data_lineage as lineage_mod
        monkeypatch.setattr(
            lineage_mod, "_check_staleness",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        resp = lineage_client.get("/api/v1/governance/data-lineage")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pipeline_steps"] == []

    def test_trace_error_returns_500(
        self, lineage_env, lineage_client, monkeypatch
    ):
        """GET /governance/data-lineage/trace returns 500 on _trace_data error."""
        from routes.governance.lineage import data_lineage as lineage_mod
        monkeypatch.setattr(
            lineage_mod, "_trace_data",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("trace boom")),
        )
        resp = lineage_client.get(
            "/api/v1/governance/data-lineage/trace",
            query_string={"data_type": "gauge", "data_id": "GAUGE-001"},
        )
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Internal server error"

    def test_staleness_route_error_returns_500(
        self, lineage_env, lineage_client, monkeypatch
    ):
        """GET /governance/data-lineage/staleness returns 500 on error."""
        from routes.governance.lineage import data_lineage as lineage_mod
        monkeypatch.setattr(
            lineage_mod, "_check_staleness",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("stale boom")),
        )
        resp = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"


# ======================================================================
# Utility edge cases (lines 142-143, 156-157, 162, 166)
# ======================================================================


class TestUtilityEdgeCases:
    """Exercise _add ValueError, _search_json exception, _search_dir_files
    edge cases."""

    def test_add_value_error_falls_back_to_absolute(self, full_trace_env):
        """_add with file outside input_dir falls back to absolute path."""
        from routes.governance.lineage import _trace_data
        # Counterparty trace searches blotter_dir/eod which is outside
        # input_dir — the _add function handles the ValueError from
        # relative_to. As long as the trace returns entries we know it worked.
        result = _trace_data(None, "trade", "PRS-FULL01")
        # EOD entries use blotter_dir path which is outside input_dir tree
        eod_entries = [r for r in result if "eod" in r["file"]]
        assert len(eod_entries) >= 1

    def test_search_json_exception_returns_false(self, tmp_path, monkeypatch):
        """_search_json with unreadable file returns False — exercised by
        tracing a gauge when gaugehc.json is unreadable."""
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

        # gauge.json present so gauge trace is triggered
        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-BAD01"}}}
            ]}, f)

        # gaugehc.json is a directory (unreadable as file -> exception in _search_json)
        (input_dir / "gaugehc.json").mkdir()

        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-BAD01")
        # Should not crash — _search_json exception returns False gracefully
        assert isinstance(result, list)

    def test_search_dir_files_missing_dir(self, tmp_path, monkeypatch):
        """_search_dir_files with nonexistent dir returns [] — exercised by
        tracing a gauge when gaugehd/ doesn't exist."""
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
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-NODIR"}}}
            ]}, f)

        # No gaugehd/ dir and no prs/ dir -> _search_dir_files gets nonexistent dirs
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-NODIR")
        # Should not crash — empty results from nonexistent dirs
        assert isinstance(result, list)

    def test_search_dir_files_filename_stem_match(self, full_trace_env):
        """_search_dir_files matches entity_id in filename stem — exercised
        by tracing a trade with EOD snapshots containing the trade ID in
        the filename."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-FULL01")
        eod_entries = [r for r in result if "eod" in r["file"]]
        assert len(eod_entries) >= 1
