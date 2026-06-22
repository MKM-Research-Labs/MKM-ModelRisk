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

"""Tests for routes/governance/test_report.py (part 2).

TestStreamProc, TestRunAndSave, TestRunTestReport.
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
# TestStreamProc
# ---------------------------------------------------------------------------

class TestStreamProc:
    def test_reads_stdout_into_buffer(self):
        """_stream_proc should push each line from proc.stdout into _output_lines."""
        from unittest.mock import MagicMock
        with tr_mod._output_lock:
            tr_mod._output_lines.clear()

        proc = MagicMock()
        proc.stdout = ["line one\n", "line two\n", "line three\n"]
        proc.wait = MagicMock()

        tr_mod._stream_proc(proc)

        with tr_mod._output_lock:
            lines = list(tr_mod._output_lines)

        assert "line one" in lines
        assert "line two" in lines
        assert "line three" in lines

    def test_strips_newlines(self):
        from unittest.mock import MagicMock
        with tr_mod._output_lock:
            tr_mod._output_lines.clear()

        proc = MagicMock()
        proc.stdout = ["stripped\n"]
        proc.wait = MagicMock()

        tr_mod._stream_proc(proc)

        with tr_mod._output_lock:
            lines = list(tr_mod._output_lines)

        assert "stripped" in lines
        assert "stripped\n" not in lines

    def test_calls_proc_wait(self):
        from unittest.mock import MagicMock
        proc = MagicMock()
        proc.stdout = []
        proc.wait = MagicMock()

        tr_mod._stream_proc(proc)

        proc.wait.assert_called_once()


# ---------------------------------------------------------------------------
# TestRunAndSave
# ---------------------------------------------------------------------------

class TestRunAndSave:
    def test_sets_running_false_on_completion(self, tmp_path, monkeypatch):
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(tr_mod, "_REPORT_FILE", str(tmp_path / "report.json"))
        monkeypatch.setattr(tr_mod, "_LOG_FILE", str(tmp_path / "run.log"))

        fake_proc = MagicMock()
        fake_proc.stdout = []
        fake_proc.wait = MagicMock()

        tr_mod._running = True

        with patch("routes.governance.test_report.AUDIT_REPORTS_DIR", str(tmp_path)), \
             patch("routes.governance.test_report.subprocess.Popen", return_value=fake_proc):
            tr_mod._run_and_save()

        assert tr_mod._running is False

    def test_appends_started_header(self, tmp_path, monkeypatch):
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(tr_mod, "_REPORT_FILE", str(tmp_path / "report.json"))
        monkeypatch.setattr(tr_mod, "_LOG_FILE", str(tmp_path / "run.log"))

        fake_proc = MagicMock()
        fake_proc.stdout = []
        fake_proc.wait = MagicMock()

        tr_mod._running = True

        with tr_mod._output_lock:
            tr_mod._output_lines.clear()

        with patch("routes.governance.test_report.AUDIT_REPORTS_DIR", str(tmp_path)), \
             patch("routes.governance.test_report.subprocess.Popen", return_value=fake_proc):
            tr_mod._run_and_save()

        with tr_mod._output_lock:
            lines = list(tr_mod._output_lines)

        assert any("=" * 10 in ln for ln in lines)
        assert any("Audit run complete" in ln for ln in lines)

    def test_handles_exception_gracefully(self, tmp_path, monkeypatch):
        from unittest.mock import patch

        monkeypatch.setattr(tr_mod, "_REPORT_FILE", str(tmp_path / "report.json"))
        monkeypatch.setattr(tr_mod, "_LOG_FILE", str(tmp_path / "run.log"))

        tr_mod._running = True

        with patch("routes.governance.test_report.AUDIT_REPORTS_DIR", str(tmp_path)), \
             patch("routes.governance.test_report.subprocess.Popen",
                   side_effect=OSError("popen failed")):
            tr_mod._run_and_save()

        assert tr_mod._running is False

    def test_error_line_appended_on_exception(self, tmp_path, monkeypatch):
        from unittest.mock import patch

        monkeypatch.setattr(tr_mod, "_REPORT_FILE", str(tmp_path / "report.json"))
        monkeypatch.setattr(tr_mod, "_LOG_FILE", str(tmp_path / "run.log"))

        tr_mod._running = True

        with tr_mod._output_lock:
            tr_mod._output_lines.clear()

        with patch("routes.governance.test_report.AUDIT_REPORTS_DIR", str(tmp_path)), \
             patch("routes.governance.test_report.subprocess.Popen",
                   side_effect=OSError("boom")):
            tr_mod._run_and_save()

        with tr_mod._output_lock:
            lines = list(tr_mod._output_lines)

        assert any("ERROR" in ln for ln in lines)


# ---------------------------------------------------------------------------
# TestRunTestReport
# ---------------------------------------------------------------------------

class TestRunTestReport:
    def test_starts_run_returns_202(self, gov_client):
        from unittest.mock import patch, MagicMock
        with patch("routes.governance.test_report.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            tr_mod._running = False
            resp = gov_client.post("/api/v1/governance/test-report/run")
        assert resp.status_code == 202

    def test_response_has_started_status(self, gov_client):
        from unittest.mock import patch, MagicMock
        with patch("routes.governance.test_report.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            tr_mod._running = False
            resp = gov_client.post("/api/v1/governance/test-report/run")
        data = resp.get_json()
        assert data["status"] == "started"

    def test_already_running_returns_202(self, gov_client):
        tr_mod._running = True
        resp = gov_client.post("/api/v1/governance/test-report/run")
        assert resp.status_code == 202

    def test_already_running_message(self, gov_client):
        tr_mod._running = True
        resp = gov_client.post("/api/v1/governance/test-report/run")
        data = resp.get_json()
        assert data["status"] == "running"
        assert "message" in data
        assert len(data["message"]) > 0
