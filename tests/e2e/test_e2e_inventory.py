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
"""Inventory e2e: register, open, edit scalar fields of every type, retire."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import (
    confirm,
    edit_model_field,
    open_app,
    open_model,
    register_model,
)

pytestmark = pytest.mark.e2e


def test_register_model_appears_in_inventory(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-001", "Retail Credit Scoring")
    row = page.locator("tr.clickable[data-id='MKM-E2E-001']")
    expect(row).to_contain_text("Retail Credit Scoring")


def test_open_model_shows_detail_tabs(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-002", "Storm Intensity")
    open_model(page, "MKM-E2E-002")
    expect(page.locator(".dtabs")).to_contain_text("Risk Rating")
    expect(page.locator(".dtabs")).to_contain_text("Validation")


def test_edit_field_records_amendment(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-003", "Depth Damage")
    open_model(page, "MKM-E2E-003")
    page.click("[data-edit='owner']")
    page.fill("#ed-input", "Jane Modeller")
    page.click("#ed-save")
    confirm(page)
    expect(page.locator("#row-owner")).to_contain_text("Jane Modeller")


def test_edit_lifecycle_stage_choice(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-004", "PD Model")
    open_model(page, "MKM-E2E-004")
    edit_model_field(page, "lifecycle_stage", "Production", choice=True)
    expect(page.locator("#row-lifecycle_stage")).to_contain_text("Production")


def test_edit_next_review_date(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-005", "LGD Model")
    open_model(page, "MKM-E2E-005")
    edit_model_field(page, "next_review_date", "2026-12-31")
    expect(page.locator("#row-next_review_date")).to_contain_text("2026-12-31")


def test_edit_materiality_choice(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-006", "EAD Model")
    open_model(page, "MKM-E2E-006")
    edit_model_field(page, "materiality", "High", choice=True)
    expect(page.locator("#row-materiality")).to_contain_text("High")


def test_edit_rag_rating_choice(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-007", "VaR Model")
    open_model(page, "MKM-E2E-007")
    edit_model_field(page, "rag_rating", "Amber", choice=True)
    expect(page.locator("#row-rag_rating")).to_contain_text("Amber")


def test_retire_model(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-008", "Legacy Model")
    open_model(page, "MKM-E2E-008")
    page.click("#d-retire")
    confirm(page)
    expect(page.locator("tr.clickable[data-id='MKM-E2E-008']")).to_contain_text("retired")


def test_register_with_company_assignment(page: Page, base_url: str):
    """Once a Company exists, registration captures it and the model is stamped."""
    open_app(page, base_url)
    # Seed a Company so the form has something to pick.
    from tests.e2e._flows import add_collection_item, open_admin_subtab
    open_admin_subtab(page, "company")
    add_collection_item(page, "company", {"value": "Sterling Bank plc"})
    # Back to inventory, register with the new Company.
    page.click(".tab[data-tab='inventory']")
    page.click("#m-register")
    page.fill("#reg-model_id", "MKM-E2E-CO-001")
    page.fill("#reg-name", "Companied Model")
    page.select_option("#reg-company", "Sterling Bank plc")
    page.click("#reg-submit")
    confirm(page)
    # The inventory list row carries a Company column.
    row = page.locator("tr.clickable[data-id='MKM-E2E-CO-001']")
    expect(row).to_contain_text("Sterling Bank plc")
