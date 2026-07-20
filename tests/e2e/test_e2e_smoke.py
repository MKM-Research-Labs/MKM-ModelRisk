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
"""Smoke tests: the console loads and every top-level tab renders."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import open_app, open_tab

pytestmark = pytest.mark.e2e

TABS = ["inventory", "product", "mrc", "documents", "audit", "reports", "reference"]


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
