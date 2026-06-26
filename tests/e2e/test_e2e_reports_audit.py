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
"""Reporting + audit e2e: the Model Risk Report PDF and the audit trail."""
from __future__ import annotations

import shutil

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import open_app, open_tab, register_model

pytestmark = pytest.mark.e2e


@pytest.mark.skipif(shutil.which("tectonic") is None, reason="tectonic not installed (optional)")
def test_model_risk_report_is_pdf(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-020", "Valuation Model")
    response = page.request.get(base_url + "/api/models/risk-report.pdf")
    assert response.ok
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.body()[:5] == b"%PDF-"


def test_audit_trail_records_registration(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-021", "Hazard Curve")
    open_tab(page, "audit")
    expect(page.locator("#tab-audit")).to_contain_text("MKM-E2E-021")
