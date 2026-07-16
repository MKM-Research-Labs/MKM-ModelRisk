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
"""Product e2e: register a Product against a live model, rebind a component, edit
status, add to its registers and upload a document, retire."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import add_collection_item, confirm, open_app, open_tab, register_model

pytestmark = pytest.mark.e2e


def _register_product(page: Page, product_id: str, product: str, analytics: str,
                      market_data: str) -> None:
    open_tab(page, "product")
    page.click("#product-register")
    page.fill("#preg-product_id", product_id)
    page.fill("#preg-product", product)
    page.select_option("#preg-analytics_model", analytics)
    page.select_option("#preg-market_data_model", market_data)   # a Market Data Model inventory id
    page.fill("#preg-calculating_agent", "Murex")
    page.click("#product-reg-submit")
    confirm(page)


def test_register_product_shows_derived_identifier(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN1", "Analytics Engine")
    register_model(page, "MKM-E2E-MD1", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-001", "Government Bond", "MKM-E2E-AN1", "MKM-E2E-MD1")
    row = page.locator("tr.clickable[data-id='Product-E2E-001']")
    expect(row).to_contain_text("MKM-E2E-AN1.MKM-E2E-MD1.Murex")
    expect(row).to_contain_text("Government Bond")


def test_product_detail_tabs_and_rebind(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN2", "Analytics Engine")
    register_model(page, "MKM-E2E-MD2", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-002", "Swaption", "MKM-E2E-AN2", "MKM-E2E-MD2")
    page.click("tr.clickable[data-id='Product-E2E-002']")
    expect(page.locator(".dtabs")).to_contain_text("Limitations")
    expect(page.locator(".dtabs")).to_contain_text("Audit")
    page.click("[data-rebind='calculating_agent']")
    page.fill("#ped-input", "Calypso")
    page.click("#ped-save")
    confirm(page)
    expect(page.locator("#row-calculating_agent")).to_contain_text("Calypso")


def test_product_edit_status_field(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN3", "Analytics Engine")
    register_model(page, "MKM-E2E-MD3", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-003", "Equity Option", "MKM-E2E-AN3", "MKM-E2E-MD3")
    page.click("tr.clickable[data-id='Product-E2E-003']")
    page.click("[data-edit='status']")
    page.select_option("#ped-input", "Active")
    page.click("#ped-save")
    confirm(page)
    expect(page.locator("#row-status")).to_contain_text("Active")


def test_product_governance_tabs_and_rag(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN4", "Analytics Engine")
    register_model(page, "MKM-E2E-MD4", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-004", "Government Bond", "MKM-E2E-AN4", "MKM-E2E-MD4")
    page.click("tr.clickable[data-id='Product-E2E-004']")
    expect(page.locator(".dtabs")).to_contain_text("Remediation")
    expect(page.locator(".dtabs")).to_contain_text("Docs")
    page.click("[data-edit='rag_rating']")
    page.select_option("#ped-input", "Green")
    page.click("#ped-save")
    confirm(page)
    expect(page.locator("#row-rag_rating")).to_contain_text("Green")


def test_product_add_assumption(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN5", "Analytics Engine")
    register_model(page, "MKM-E2E-MD5", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-005", "Swap", "MKM-E2E-AN5", "MKM-E2E-MD5")
    page.click("tr.clickable[data-id='Product-E2E-005']")
    page.click("[data-ptab='assumptions']")
    add_collection_item(page, "assumptions", {"description": "Flat vol surface", "impact": "Low"})
    expect(page.locator("#pt-content")).to_contain_text("Flat vol surface")


def test_product_add_remediation_step(page: Page, base_url: str):
    """Remediation is edited fully in place — no data-ed/data-rm buttons. Drive
    the add form directly rather than the shared helper (which looks for them)."""
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN6", "Analytics Engine")
    register_model(page, "MKM-E2E-MD6", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-006", "Cap", "MKM-E2E-AN6", "MKM-E2E-MD6")
    page.click("tr.clickable[data-id='Product-E2E-006']")
    page.click("[data-ptab='remediation_steps']")
    page.fill("#add-remediation_steps-description", "Re-bootstrap curve")
    page.click("[data-add='remediation_steps']")
    confirm(page)
    expect(page.locator("#pt-content")).to_contain_text("Re-bootstrap curve")


def test_product_upload_supporting_document(page: Page, base_url: str, tmp_path):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN7", "Analytics Engine")
    register_model(page, "MKM-E2E-MD7", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-007", "Floor", "MKM-E2E-AN7", "MKM-E2E-MD7")
    page.click("tr.clickable[data-id='Product-E2E-007']")
    page.click("[data-ptab='docs']")
    pdf = tmp_path / "product_spec.pdf"
    pdf.write_bytes(b"%PDF-1.4\n% e2e fixture\n")
    page.set_input_files("#doc-file", str(pdf))
    page.fill("#doc-desc", "Product specification")
    page.click("#doc-upload")
    expect(page.locator("#pt-content")).to_contain_text("product_spec.pdf")


def test_product_retire(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-AN8", "Analytics Engine")
    register_model(page, "MKM-E2E-MD8", "Vol Surface", model_type="Market Data Model")
    _register_product(page, "Product-E2E-008", "Inflation Swap", "MKM-E2E-AN8", "MKM-E2E-MD8")
    page.click("tr.clickable[data-id='Product-E2E-008']")
    page.click("[data-ptab='danger']")          # Retire now lives on the Danger tab
    page.click("#product-retire")
    confirm(page)
    expect(page.locator("tr.clickable[data-id='Product-E2E-008']")).to_contain_text("retired")
