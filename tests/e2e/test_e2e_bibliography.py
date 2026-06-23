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
"""Bibliography e2e: add a reference, filter by category, export BibTeX."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_tab

pytestmark = pytest.mark.e2e


def _add_reference(page: Page):
    page.fill("#bib-authors", "Kelly, D. K.")
    page.fill("#bib-title", "Handbook of Model Risk")
    page.fill("#bib-year", "2025")
    page.fill("#bib-category", "Governance")
    page.click("#bib-save")
    confirm(page)


def test_add_reference(page: Page, base_url: str):
    open_app(page, base_url)
    open_tab(page, "bibliography")
    _add_reference(page)
    row = page.locator("#bib-rows tr", has_text="Handbook of Model Risk")
    expect(row).to_contain_text("Kelly, D. K.")
    expect(row).to_contain_text("Governance")


def test_category_filter(page: Page, base_url: str):
    open_app(page, base_url)
    open_tab(page, "bibliography")
    _add_reference(page)
    page.select_option("#bib-cat", "Governance")
    expect(page.locator("#bib-rows tr", has_text="Handbook of Model Risk")).to_be_visible()


def test_export_bibtex_link(page: Page, base_url: str):
    open_app(page, base_url)
    open_tab(page, "bibliography")
    _add_reference(page)
    response = page.request.get(base_url + "/api/bibliography/export.bib")
    assert response.ok
    assert "@misc{" in response.text()
