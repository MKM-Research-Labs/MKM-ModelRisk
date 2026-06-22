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

"""Tests for governance field lineage routes (registry and lookup)."""

from tests.routes.governance.lineage_shared import (
    SAMPLE_FIELD_LINEAGE,
    write_field_lineage,
)


# ══════════════════════════════════════════════════════════════════
# GET /governance/field-lineage
# ══════════════════════════════════════════════════════════════════


class TestGetFieldLineage:

    def test_no_registry_404(self, lineage_env, lineage_client):
        """No field lineage file returns 404."""
        r = lineage_client.get("/api/v1/governance/field-lineage")
        assert r.status_code == 404
        data = r.get_json()
        assert "not found" in data["message"].lower()

    def test_full_registry(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get("/api/v1/governance/field-lineage")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["version"] == "1.0.0"
        assert data["total_reports"] == 2
        # flood_risk has 2 sections with 2+1=3 fields, prs_pricing has 1 section with 1 field
        assert data["total_fields"] == 4
        assert len(data["summary"]) == 2

    def test_filter_by_report(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get("/api/v1/governance/field-lineage?report=flood_risk")
        assert r.status_code == 200
        data = r.get_json()
        assert data["total_reports"] == 1
        assert "flood_risk" in data["reports"]
        assert "prs_pricing" not in data["reports"]
        assert data["total_fields"] == 3

    def test_filter_unknown_report_404(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get("/api/v1/governance/field-lineage?report=nonexistent")
        assert r.status_code == 404
        data = r.get_json()
        assert "available_reports" in data

    def test_summary_contents(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get("/api/v1/governance/field-lineage")
        data = r.get_json()
        fr_summary = next(s for s in data["summary"] if s["report"] == "flood_risk")
        assert fr_summary["label"] == "Flood Risk Report"
        assert fr_summary["section_count"] == 2
        assert fr_summary["field_count"] == 3


# ══════════════════════════════════════════════════════════════════
# GET /governance/field-lineage/lookup
# ══════════════════════════════════════════════════════════════════


class TestFieldLineageLookup:

    def test_no_registry_404(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/field-lineage/lookup?search=x")
        assert r.status_code == 404

    def test_no_params_400(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get("/api/v1/governance/field-lineage/lookup")
        assert r.status_code == 400
        assert "Provide" in r.get_json()["message"]

    def test_exact_lookup_found(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup"
            "?report=flood_risk&section=summary&field=gauge_id"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["field"] == "gauge_id"
        assert data["lineage"]["label"] == "Gauge ID"

    def test_exact_lookup_not_found(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup"
            "?report=flood_risk&section=summary&field=nonexistent"
        )
        assert r.status_code == 404
        assert "Field not found" in r.get_json()["message"]

    def test_exact_lookup_wrong_section(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup"
            "?report=flood_risk&section=wrong&field=gauge_id"
        )
        assert r.status_code == 404

    def test_exact_lookup_wrong_report(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup"
            "?report=wrong&section=summary&field=gauge_id"
        )
        assert r.status_code == 404

    def test_search_finds_matches(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?search=GEV"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] >= 1
        # "GEV" appears in flood_depth computation and return_period computation
        fields_found = {res["field"] for res in data["results"]}
        assert "flood_depth" in fields_found or "return_period" in fields_found

    def test_search_case_insensitive(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?search=gev"
        )
        data = r.get_json()
        assert data["count"] >= 1

    def test_search_no_results(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?search=zzzznotfound"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_search_by_source_field(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?search=spread_bps"
        )
        data = r.get_json()
        assert data["count"] == 1
        assert data["results"][0]["field"] == "spread"
        assert data["results"][0]["report"] == "prs_pricing"

    def test_search_by_cdm_path(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?search=gauge.gauge_id"
        )
        data = r.get_json()
        assert data["count"] >= 1

    def test_search_result_structure(self, lineage_env, lineage_client):
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?search=spread"
        )
        data = r.get_json()
        assert data["count"] >= 1
        result = data["results"][0]
        assert "report" in result
        assert "report_label" in result
        assert "section" in result
        assert "field" in result
        assert "lineage" in result

    def test_search_takes_priority_over_partial_exact(self, lineage_env, lineage_client):
        """If only report and search are given (not all 3 exact keys), search is used."""
        write_field_lineage(lineage_env, SAMPLE_FIELD_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/field-lineage/lookup?report=flood_risk&search=depth"
        )
        data = r.get_json()
        # search is used (exact requires all 3: report+section+field)
        assert data["count"] >= 1
