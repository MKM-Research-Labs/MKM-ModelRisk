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
"""Reporting + audit e2e: the Model Risk Report PDF and the audit trail."""
from __future__ import annotations

import shutil

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import open_app, open_tab, register_model

pytestmark = pytest.mark.e2e

# Rendering PDFs with tectonic is CPU-heavy and easily exceeds Playwright's 30s
# default request timeout on a busy dev machine (generating every audit report
# is slower still). Give these requests plenty of headroom so a slow render is
# not mistaken for a failure.
_PDF_TIMEOUT_MS = 120_000


@pytest.mark.skipif(shutil.which("tectonic") is None, reason="tectonic not installed (optional)")
def test_model_risk_report_is_pdf(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-020", "Valuation Model")
    response = page.request.get(
        base_url + "/api/models/risk-report.pdf", timeout=_PDF_TIMEOUT_MS
    )
    assert response.ok
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.body()[:5] == b"%PDF-"


def test_generate_audit_reports_never_500s(page: Page, base_url: str):
    # Regardless of whether tectonic is installed on the host, the "Generate
    # reports" action must degrade gracefully: 200 when the engine is present,
    # otherwise a clean 503 carrying an actionable message — never a raw 500.
    open_app(page, base_url)
    response = page.request.post(
        base_url + "/api/audit-reports/generate",
        headers={"X-Auth-Request-User": "risk@kerrshearer.co.uk"},
        timeout=_PDF_TIMEOUT_MS,
    )
    if shutil.which("tectonic") is None:
        assert response.status == 503
        assert "tectonic" in response.json()["error"]
    else:
        assert response.ok


def test_audit_trail_records_registration(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-021", "Hazard Curve")
    open_tab(page, "audit")
    expect(page.locator("#tab-audit")).to_contain_text("MKM-E2E-021")
