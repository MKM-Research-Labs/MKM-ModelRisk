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
"""PVM e2e: register a PVM against a live model, rebind a component, edit status."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_tab, register_model

pytestmark = pytest.mark.e2e


def _register_pvm(page: Page, pvm_id: str, product: str, analytics: str) -> None:
    open_tab(page, "pvm")
    page.click("#pvm-register")
    page.fill("#preg-pvm_id", pvm_id)
    page.fill("#preg-product", product)
    page.select_option("#preg-analytics_model", analytics)
    page.fill("#preg-market_data_model", "NSS curve")
    page.fill("#preg-calculating_agent", "Murex")
    page.click("#pvm-reg-submit")
    confirm(page)


def test_register_pvm_shows_derived_identifier(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN1", "Analytics Engine")
    _register_pvm(page, "PVM-E2E-001", "Government Bond", "MKM-E2E-AN1")
    row = page.locator("tr.clickable[data-id='PVM-E2E-001']")
    expect(row).to_contain_text("MKM-E2E-AN1.NSS curve.Murex")
    expect(row).to_contain_text("Government Bond")


def test_pvm_detail_tabs_and_rebind(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN2", "Analytics Engine")
    _register_pvm(page, "PVM-E2E-002", "Swaption", "MKM-E2E-AN2")
    page.click("tr.clickable[data-id='PVM-E2E-002']")
    expect(page.locator(".dtabs")).to_contain_text("Limitations")
    expect(page.locator(".dtabs")).to_contain_text("Audit")
    page.click("[data-rebind='calculating_agent']")
    page.fill("#ped-input", "Calypso")
    page.click("#ped-save")
    confirm(page)
    expect(page.locator("#row-calculating_agent")).to_contain_text("Calypso")


def test_pvm_edit_status_field(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN3", "Analytics Engine")
    _register_pvm(page, "PVM-E2E-003", "Equity Option", "MKM-E2E-AN3")
    page.click("tr.clickable[data-id='PVM-E2E-003']")
    page.click("[data-edit='status']")
    page.select_option("#ped-input", "Active")
    page.click("#ped-save")
    confirm(page)
    expect(page.locator("#row-status")).to_contain_text("Active")
