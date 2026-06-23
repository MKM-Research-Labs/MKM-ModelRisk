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
"""MRC e2e: schedule a meeting and open its detail by double-clicking the row."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_tab

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
    expect(page.locator("#mt-detail")).to_contain_text("MRC-2026-Q4")
