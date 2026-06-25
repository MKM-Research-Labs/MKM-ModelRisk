# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Tests for the audit-reports API (list, generate, serve)."""
from __future__ import annotations

import audit.__main__ as audit_main
import src.web.api_audit_reports as mod
from src.governance.mrc import pack
from tests.web.conftest import HEADERS


def _stub_pdf(tex, assets=None):
    return b"%PDF-1.4 stub"


def test_list_empty_when_no_output_dir(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports").get_json() == []


def test_generate_then_list_and_view(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    monkeypatch.setattr(pack, "compile_tex", _stub_pdf)             # no tectonic
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})  # no jscpd

    generated = client.post("/api/audit-reports/generate", headers=HEADERS)
    assert generated.status_code == 200
    names = {r["filename"] for r in generated.get_json()}
    assert {"coding_rule_audit.pdf", "model_risk_report.pdf"} <= names

    catalogue = client.get("/api/audit-reports").get_json()
    assert any(r["label"] == "Coding-Rule Audit" for r in catalogue)
    assert all(r["size"] > 0 and r["modified"] for r in catalogue)

    served = client.get("/api/audit-reports/coding_rule_audit.pdf")
    assert served.status_code == 200 and served.data.startswith(b"%PDF")


def test_serve_missing_dir_is_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports/anything.pdf").status_code == 404


def test_serve_unknown_file_is_404(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    out.mkdir()
    monkeypatch.setattr(mod, "OUTPUT_DIR", out)
    assert client.get("/api/audit-reports/nope.pdf").status_code == 404
