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
"""MRC e2e: schedule a meeting, bulk-add minutes, multi-select models in scope."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_tab, register_model

pytestmark = pytest.mark.e2e


def _schedule(page: Page, meeting_id: str, title: str):
    page.fill("#sc-meeting_id", meeting_id)
    page.fill("#sc-title", title)
    page.fill("#sc-date", "2026-09-15")
    page.click("#mt-schedule")
    confirm(page)


def test_schedule_meeting_appears(page: Page, base_url: str):
    open_app(page, base_url)
    open_tab(page, "mrc")
    _schedule(page, "MRC-2026-Q3", "Q3 Model Risk Committee")
    expect(page.locator("tr.clickable[data-id='MRC-2026-Q3']")).to_contain_text("Q3 Model Risk Committee")


def test_double_click_opens_meeting_detail(page: Page, base_url: str):
    open_app(page, base_url)
    open_tab(page, "mrc")
    _schedule(page, "MRC-2026-Q4", "Q4 Model Risk Committee")
    page.dblclick("tr.clickable[data-id='MRC-2026-Q4']")
    detail = page.locator("#mt-detail")
    expect(detail).to_contain_text("Q4 Model Risk Committee")
    expect(detail).to_contain_text("Agenda")
    expect(detail).to_contain_text("Meeting Pack PDF")


def test_bulk_add_minutes(page: Page, base_url: str):
    """Fill three of the five minutes rows and save them in one go."""
    open_app(page, base_url)
    open_tab(page, "mrc")
    _schedule(page, "MRC-2026-BLK", "Bulk Minutes")
    page.dblclick("tr.clickable[data-id='MRC-2026-BLK']")
    page.click("[data-mtab='minutes']")
    expect(page.locator("[data-bulk-add='minutes']")).to_be_visible()

    page.fill("#badd-minutes-0-title", "Welcome")
    page.fill("#badd-minutes-1-title", "Approvals")
    page.fill("#badd-minutes-1-text", "Two models approved.")
    page.fill("#badd-minutes-2-title", "AOB")

    page.click("[data-bulk-add='minutes']")
    confirm(page)

    expect(page.locator("[data-mtab='minutes']")).to_contain_text("(3)")
    # First tbody is the existing items; the second is the empty bulk-add form.
    body = page.locator("#mtd-content tbody").first
    expect(body).to_contain_text("Welcome")
    expect(body).to_contain_text("Approvals")
    expect(body).to_contain_text("AOB")


def test_models_multi_select_saves_selection(page: Page, base_url: str):
    """Pick two of three models via checkboxes; the in-scope count updates."""
    open_app(page, base_url)
    register_model(page, "MKM-MS-001", "Credit Loss")
    register_model(page, "MKM-MS-002", "Market Risk")
    register_model(page, "MKM-MS-003", "Liquidity")

    open_tab(page, "mrc")
    _schedule(page, "MRC-MS", "Multi-select")
    page.dblclick("tr.clickable[data-id='MRC-MS']")
    page.click("[data-mtab='models_in_scope']")

    # No org scope on the meeting, so all inventory models are candidates.
    expect(page.locator("[data-mscope='MKM-MS-001']")).to_be_visible()
    expect(page.locator("[data-mscope='MKM-MS-002']")).to_be_visible()
    expect(page.locator("[data-mscope='MKM-MS-003']")).to_be_visible()

    page.check("[data-mscope='MKM-MS-001']")
    page.check("[data-mscope='MKM-MS-003']")
    page.click("#mt-save-models")
    confirm(page)

    expect(page.locator("[data-mtab='models_in_scope']")).to_contain_text("(2)")
    expect(page.locator("#mt-models-summary")).to_contain_text("2 models")
    # Both selected boxes remain ticked after refresh.
    expect(page.locator("[data-mscope='MKM-MS-001']")).to_be_checked()
    expect(page.locator("[data-mscope='MKM-MS-003']")).to_be_checked()
    expect(page.locator("[data-mscope='MKM-MS-002']")).not_to_be_checked()
