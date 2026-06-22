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

"""Tests for routes/governance/test_report.py (part 1).

TestAppendOutput, TestTestReportOutput, TestTestReportSummary.
"""

import json
import pathlib

import pytest

import routes.governance.test_report as tr_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_module_state():
    """Restore module-level globals after every test."""
    original_running = tr_mod._running
    original_lines = list(tr_mod._output_lines)
    yield
    tr_mod._running = original_running
    with tr_mod._output_lock:
        tr_mod._output_lines.clear()
        tr_mod._output_lines.extend(original_lines)


@pytest.fixture
def gov_client(tmp_path, monkeypatch):
    """Flask test client with isolated governance environment."""
    import routes.governance._constants as gov_constants

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")
    with open(inv_path, "w") as f:
        json.dump({"metadata": {}, "models": [], "model_chain": {}, "tiering_matrix": {}, "audit_trail": []}, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)

    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(inv_path).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# TestAppendOutput
# ---------------------------------------------------------------------------

class TestAppendOutput:
    def test_appends_line(self):
        with tr_mod._output_lock:
            tr_mod._output_lines.clear()
        tr_mod._append_output("hello world")
        with tr_mod._output_lock:
            lines = list(tr_mod._output_lines)
        assert "hello world" in lines

    def test_trims_buffer_at_2000(self):
        with tr_mod._output_lock:
            tr_mod._output_lines.clear()
        for i in range(2100):
            tr_mod._append_output(f"line {i}")
        with tr_mod._output_lock:
            length = len(tr_mod._output_lines)
        assert length <= 2000

    def test_clear_then_append(self):
        with tr_mod._output_lock:
            tr_mod._output_lines.clear()
        tr_mod._append_output("fresh line")
        with tr_mod._output_lock:
            lines = list(tr_mod._output_lines)
        assert lines == ["fresh line"]


# ---------------------------------------------------------------------------
# TestTestReportOutput
# ---------------------------------------------------------------------------

class TestTestReportOutput:
    def test_returns_200(self, gov_client):
        resp = gov_client.get("/api/v1/governance/test-report/output")
        assert resp.status_code == 200

    def test_has_running_field(self, gov_client):
        resp = gov_client.get("/api/v1/governance/test-report/output")
        data = resp.get_json()
        assert "running" in data
        assert isinstance(data["running"], bool)

    def test_has_lines_field(self, gov_client):
        resp = gov_client.get("/api/v1/governance/test-report/output")
        data = resp.get_json()
        assert "lines" in data
        assert isinstance(data["lines"], list)

    def test_lines_includes_appended(self, gov_client):
        with tr_mod._output_lock:
            tr_mod._output_lines.clear()
        tr_mod._append_output("test line")
        resp = gov_client.get("/api/v1/governance/test-report/output")
        data = resp.get_json()
        assert "test line" in data["lines"]

    def test_not_running_initially(self, gov_client):
        tr_mod._running = False
        resp = gov_client.get("/api/v1/governance/test-report/output")
        data = resp.get_json()
        assert data["running"] is False


# ---------------------------------------------------------------------------
# TestTestReportSummary
# ---------------------------------------------------------------------------

class TestTestReportSummary:
    def test_returns_not_found_when_no_file(self, gov_client, monkeypatch, tmp_path):
        nonexistent = str(tmp_path / "nonexistent" / "test_failures_report.json")
        monkeypatch.setattr(tr_mod, "_REPORT_FILE", nonexistent)
        resp = gov_client.get("/api/v1/governance/test-report/summary")
        data = resp.get_json()
        assert data["status"] == "not_found"

    def test_returns_ok_when_file_exists(self, gov_client, monkeypatch, tmp_path):
        report_path = str(tmp_path / "test_failures_report.json")
        fake_report = {
            "generated_at": "2026-03-09T12:00:00",
            "summary": {"total": 10, "passed": 9, "failed": 1, "skipped": 0},
            "failures": [],
        }
        with open(report_path, "w") as f:
            json.dump(fake_report, f)
        monkeypatch.setattr(tr_mod, "_REPORT_FILE", report_path)
        resp = gov_client.get("/api/v1/governance/test-report/summary")
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_returns_summary_fields(self, gov_client, monkeypatch, tmp_path):
        report_path = str(tmp_path / "test_failures_report.json")
        fake_report = {
            "generated_at": "2026-03-09T12:00:00",
            "summary": {"total": 5, "passed": 4, "failed": 1, "skipped": 0},
            "failures": [{"nodeid": "test_foo.py::test_bar", "outcome": "failed"}],
        }
        with open(report_path, "w") as f:
            json.dump(fake_report, f)
        monkeypatch.setattr(tr_mod, "_REPORT_FILE", report_path)
        resp = gov_client.get("/api/v1/governance/test-report/summary")
        data = resp.get_json()
        assert "summary" in data
        assert "failures" in data
        assert "generated_at" in data
        assert data["summary"]["total"] == 5
        assert len(data["failures"]) == 1

    def test_running_field_is_bool(self, gov_client, monkeypatch, tmp_path):
        nonexistent = str(tmp_path / "no_such_file.json")
        monkeypatch.setattr(tr_mod, "_REPORT_FILE", nonexistent)
        resp = gov_client.get("/api/v1/governance/test-report/summary")
        data = resp.get_json()
        assert "running" in data
        assert isinstance(data["running"], bool)
