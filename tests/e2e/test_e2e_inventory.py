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
"""Inventory e2e: register a model, open it, edit a field through confirm-to-amend."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_model, register_model

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
