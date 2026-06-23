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
"""Smoke tests: the console loads and every top-level tab renders."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import open_app, open_tab

pytestmark = pytest.mark.e2e

TABS = ["inventory", "mrc", "documents", "bibliography", "audit", "reference"]


def test_app_loads(page: Page, base_url: str):
    open_app(page, base_url)
    expect(page.locator("header")).to_contain_text("Model Risk Governance")
    for tab in TABS:
        expect(page.locator(f".tab[data-tab='{tab}']")).to_be_visible()


@pytest.mark.parametrize("tab", TABS)
def test_each_tab_opens(page: Page, base_url: str, tab: str):
    open_app(page, base_url)
    open_tab(page, tab)
    expect(page.locator(f"#tab-{tab} .card, #tab-{tab} .summary")).not_to_have_count(0)
