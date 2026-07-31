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

"""Interim holding documents (``scripts.file_holding_docs``).

The markdown builders must read as honest interim documents — the approach and the
evidence *types*, never fabricated results — and the filing must be idempotent.
Rendering is stubbed so the tests do not need pandoc/tectonic.
"""
from __future__ import annotations

from scripts import file_holding_docs as holding
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

SAMPLE = {
    "name": "Spatial Interpolation Model",
    "description": "IDW interpolation mapping gauge observations to properties.",
    "validation_questions": [
        {"item_id": "VQ-001", "short_label": "Ronseal Test", "status": "Addressed"},
        {"item_id": "VQ-002", "short_label": "Accuracy & Stability", "status": "Partially Addressed"},
        {"item_id": "VQ-005", "short_label": "Data Quality", "status": "Not Addressed"},
        {"item_id": "VQ-008", "short_label": "Benchmarking", "status": "Not Addressed"},
        {"item_id": "VQ-009", "short_label": "Independent Validation", "status": "Not Addressed"},
    ],
}


class TestMonitoringMarkdown:
    def test_is_flagged_interim_with_no_results(self):
        md = holding.build_monitoring_md(SAMPLE)
        assert "interim holding document" in md.lower()
        assert "no monitoring results" in md.lower()
        assert SAMPLE["name"] in md

    def test_describes_approach_not_numbers(self):
        md = holding.build_monitoring_md(SAMPLE)
        # It describes cadence and escalation (approach), not a measured result.
        assert "cadence" in md.lower()
        assert "escalation" in md.lower()


class TestRemediationMarkdown:
    def test_is_flagged_interim_with_no_evidence(self):
        md = holding.build_remediation_md(SAMPLE)
        assert "interim holding document" in md.lower()
        assert "no evidence" in md.lower()

    def test_lists_only_the_open_findings_with_evidence_types(self):
        md = holding.build_remediation_md(SAMPLE)
        # Open findings get an evidence section...
        assert "Data quality" in md
        assert "Benchmarking" in md
        assert "Independent validation" in md
        assert "Back-testing" in md            # VQ-002 partial -> accuracy section
        # ...addressed ones do not appear as findings to remediate.
        assert "Ronseal" not in md

    def test_handles_a_model_with_no_open_questions(self):
        clean = {"name": "X", "description": "d", "validation_questions": [
            {"item_id": "VQ-001", "short_label": "Ronseal", "status": "Addressed"}]}
        md = holding.build_remediation_md(clean)
        assert "No open validation questions" in md


def _register(mid, name):
    register_model(model_id=mid, name=name, actor="test")
    rebuild_inventory_view()


def _stub_render(title, subtitle, body_md, settings):
    return b"%PDF-1.5 holding\n%%EOF"


def test_apply_files_both_holding_docs_and_is_idempotent(monkeypatch):
    monkeypatch.setattr(holding, "get_settings", lambda: {"fields": {"org_name": "MKM"}})
    _register("MKM-SP-001", "Spatial Interpolation Model")
    ids = ["MKM-SP-001"]
    first = holding.apply(render=_stub_render, monitoring_ids=ids, remediation_ids=ids)
    assert first == {"monitoring": ["MKM-SP-001"], "remediation": ["MKM-SP-001"]}
    cats = {d["category"] for d in get_model("MKM-SP-001")["data"]["documents"]}
    assert "Monitoring" in cats
    assert "Remediation Evidence" in cats
    again = holding.apply(render=_stub_render, monitoring_ids=ids, remediation_ids=ids)
    assert again == {"monitoring": [], "remediation": []}
