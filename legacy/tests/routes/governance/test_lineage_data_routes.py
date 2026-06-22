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

"""Tests for governance data lineage and trace routes."""

from tests.routes.governance.lineage_shared import (
    SAMPLE_LINEAGE,
    create_fresh_file,
    create_stale_file,
    write_lineage,
)


# ══════════════════════════════════════════════════════════════════
# GET /governance/data-lineage route
# ══════════════════════════════════════════════════════════════════


class TestGetDataLineage:

    def test_with_no_manifest(self, lineage_env, lineage_client):
        """When lineage file does not exist, manifest is None but route succeeds."""
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        r = lineage_client.get("/api/v1/governance/data-lineage")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["manifest"] is None
        assert data["summary"]["missing"] == len(_PIPELINE_STEPS)
        assert data["summary"]["health"] == "unhealthy"

    def test_all_fresh(self, lineage_env, lineage_client):
        """All pipeline outputs exist and are fresh."""
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        tmp = lineage_env["tmp_path"]
        for step_def in _PIPELINE_STEPS:
            output = step_def["output"]
            if output.endswith("/"):
                create_fresh_file(tmp, f"{output}dummy.json")
            else:
                create_fresh_file(tmp, output)

        write_lineage(lineage_env, SAMPLE_LINEAGE)

        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert data["status"] == "success"
        assert data["summary"]["fresh"] == len(_PIPELINE_STEPS)
        assert data["summary"]["stale"] == 0
        assert data["summary"]["missing"] == 0
        assert data["summary"]["health"] == "healthy"
        assert data["manifest"] is not None

    def test_mixed_statuses(self, lineage_env, lineage_client):
        """Mix of fresh, stale, and missing."""
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        tmp = lineage_env["tmp_path"]
        create_fresh_file(tmp, "gauge.json")
        create_stale_file(tmp, "property.json", days_old=5)

        write_lineage(lineage_env, SAMPLE_LINEAGE)

        # gauge.json freshens any step whose representative output is gauge.json;
        # property.json staleness applies only to the properties step.
        fresh_count = sum(1 for s in _PIPELINE_STEPS if s["output"] == "gauge.json")
        stale_count = sum(1 for s in _PIPELINE_STEPS if s["output"] == "property.json")
        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert data["summary"]["fresh"] == fresh_count
        assert data["summary"]["stale"] == stale_count
        assert data["summary"]["missing"] == len(_PIPELINE_STEPS) - fresh_count - stale_count
        assert data["summary"]["health"] == "unhealthy"

    def test_degraded_health(self, lineage_env, lineage_client):
        """All present but some stale = degraded."""
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        tmp = lineage_env["tmp_path"]
        for step_def in _PIPELINE_STEPS:
            output = step_def["output"]
            if output.endswith("/"):
                create_fresh_file(tmp, f"{output}dummy.json")
            else:
                create_fresh_file(tmp, output)

        # Make one stale
        create_stale_file(tmp, "gauge.json", days_old=5)

        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert data["summary"]["missing"] == 0
        # gauge.json staleness applies to every step using it as representative output
        assert data["summary"]["stale"] == sum(
            1 for s in _PIPELINE_STEPS if s["output"] == "gauge.json"
        )
        assert data["summary"]["health"] == "degraded"

    def test_has_as_of(self, lineage_env, lineage_client):
        """Response includes as_of timestamp."""
        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert "as_of" in data


# ══════════════════════════════════════════════════════════════════
# GET /governance/data-lineage/trace
# ══════════════════════════════════════════════════════════════════


class TestTraceDataLineageRoute:

    def test_missing_params(self, lineage_env, lineage_client):
        """Missing data_type or data_id returns 400."""
        r = lineage_client.get("/api/v1/governance/data-lineage/trace")
        assert r.status_code == 400
        assert "required" in r.get_json()["message"]

    def test_missing_data_id(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/data-lineage/trace?data_type=gauge")
        assert r.status_code == 400

    def test_missing_data_type(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/data-lineage/trace?data_id=GAUGE-001")
        assert r.status_code == 400

    def test_whitespace_only_params(self, lineage_env, lineage_client):
        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=%20&data_id=%20"
        )
        assert r.status_code == 400

    def test_valid_trace(self, lineage_env, lineage_client):
        import json as _json
        from pathlib import Path

        write_lineage(lineage_env, SAMPLE_LINEAGE)

        # Create gauge.json with GAUGE-001 so file-scan trace finds it
        tmp = lineage_env["tmp_path"]
        gauge_data = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}]}
        (tmp / "gauge.json").write_text(_json.dumps(gauge_data))
        # Create gaugehc.json referencing GAUGE-001
        hc_data = {"hazard_curves": {"GAUGE-001": {"annual_flood_prob_alert": 0.1}}}
        (tmp / "gaugehc.json").write_text(_json.dumps(hc_data))

        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-001"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["found"] is True
        assert len(data["trace"]) >= 1
        assert data["data_type"] == "gauge"
        assert data["data_id"] == "GAUGE-001"

    def test_trace_not_found(self, lineage_env, lineage_client):
        write_lineage(lineage_env, SAMPLE_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-999"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is False
        assert data["trace"] == []

    def test_trace_no_manifest(self, lineage_env, lineage_client):
        """No lineage file => found=False, empty trace."""
        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-001"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is False

    def test_trace_fallback_scan(self, lineage_env, lineage_client):
        """Fallback scan when no direct traces key matches."""
        lineage = {
            "steps": {
                "gauges": {"outputs": ["GAUGE-XYZ.json"]},
            },
        }
        write_lineage(lineage_env, lineage)

        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=storm&data_id=GAUGE-XYZ"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is True
        assert len(data["trace"]) == 1
