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
"""Admin > MRC committee e2e — the coverage that replaces the retired singleton
MRC settings tests (phase MRC-2 moved chair/cadence onto individual committees).

Committees are entities, not a plain inline-edit table: each row opens a
Model-style detail with per-field edits, a Remove control and a per-committee
Terms of Reference upload. All mutations flow through confirm-to-amend except
the ToR upload, which is a direct multipart POST (see mrc_committee.js).
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_admin_subtab, open_app

pytestmark = pytest.mark.e2e


def _open_mrc_admin(page: Page, base_url: str) -> None:
    open_app(page, base_url)
    open_admin_subtab(page, "mrc")


def _add_committee(page: Page, fields: dict[str, str]) -> str:
    """Fill the committee add form and commit it through confirm-to-amend.

    Returns the new committee's ``item_id`` read from its rendered row (rows are
    keyed by ``data-cid`` and located by the unique MRC ID in ``value``).
    """
    for key, value in fields.items():
        selector = f"#cadd-{key}"
        if page.locator(selector).evaluate("el => el.tagName") == "SELECT":
            page.select_option(selector, value)
        else:
            page.fill(selector, value)
    page.click("#cadd")
    confirm(page)
    row = page.locator("tr.clickable", has_text=fields["value"]).first
    expect(row).to_be_visible()
    return row.get_attribute("data-cid")


def _open_detail(page: Page, item_id: str) -> None:
    page.click(f"tr.clickable[data-cid='{item_id}']")
    expect(page.locator("#committee-detail .card")).to_be_visible()


def _edit_field(page: Page, key: str, value: str, *, choice: bool = False) -> None:
    page.click(f"[data-ced='{key}']")
    if choice:
        page.select_option("#ced-input", value)
    else:
        page.fill("#ced-input", value)
    page.click("#ced-save")
    confirm(page)


_COMPANY_MRC = {
    "value": "MRC-EMEA",
    "name": "EMEA Model Risk Committee",
    "level": "Company",
    "frequency": "Quarterly",
}


def test_committee_create(page: Page, base_url: str):
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, _COMPANY_MRC)
    expect(page.locator(f"tr.clickable[data-cid='{item_id}']")).to_contain_text("EMEA Model Risk Committee")


def test_committee_detail_opens_with_tor_section(page: Page, base_url: str):
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, _COMPANY_MRC)
    _open_detail(page, item_id)
    detail = page.locator("#committee-detail")
    expect(detail).to_contain_text("EMEA Model Risk Committee")
    expect(detail).to_contain_text("Terms of Reference")
    expect(detail).to_contain_text("No Terms of Reference uploaded.")


def test_committee_edit_chair(page: Page, base_url: str):
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, _COMPANY_MRC)
    _open_detail(page, item_id)
    _edit_field(page, "chair", "David Kerr Kelly")
    expect(page.locator("#crow-chair .v")).to_contain_text("David Kerr Kelly")


def test_committee_edit_frequency_choice(page: Page, base_url: str):
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, _COMPANY_MRC)
    _open_detail(page, item_id)
    _edit_field(page, "frequency", "Annual", choice=True)
    expect(page.locator("#crow-frequency .v")).to_contain_text("Annual")


def test_committee_scoped_to_department(page: Page, base_url: str):
    """A Department-level committee keeps its org anchor (level + scope) on the row."""
    # Seed the org tree (Division + Department) via API so the scope picker has
    # options; the Committee admin drives its scope select from those lists.
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    page.request.post(base_url + "/api/reference/collections/division",
                      data={"fields": {"value": "Markets"}, "confirmed": True}, headers=headers)
    page.request.post(base_url + "/api/reference/collections/department",
                      data={"fields": {"value": "Rates Trading", "division": "Markets"},
                            "confirmed": True}, headers=headers)
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, {
        "value": "MRC-DEPT-RATES",
        "name": "Rates MRC",
        "level": "Department",
        "scope_value": "Rates Trading",
        "frequency": "Monthly",
    })
    row = page.locator(f"tr.clickable[data-cid='{item_id}']")
    expect(row).to_contain_text("Department")
    expect(row).to_contain_text("Rates Trading")


def test_committee_archive(page: Page, base_url: str):
    """Committees are archived, never deleted — the row stays in the list but
    is marked ``muted`` and gains an "Archived" badge."""
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, _COMPANY_MRC)
    _open_detail(page, item_id)
    page.click("#carch")
    confirm(page)
    row = page.locator(f"tr.clickable[data-cid='{item_id}']")
    expect(row).to_be_visible()
    expect(row).to_have_class("clickable muted")
    expect(row).to_contain_text("Archived")


def test_committee_tor_upload(page: Page, base_url: str, tmp_path):
    """Uploading a Terms of Reference file surfaces its download link on the detail."""
    _open_mrc_admin(page, base_url)
    item_id = _add_committee(page, _COMPANY_MRC)
    _open_detail(page, item_id)
    tor = tmp_path / "terms.txt"
    tor.write_text("Terms of Reference for the EMEA MRC.")
    page.set_input_files("#ctor-file", str(tor))
    page.click("#ctor-upload")
    link = page.locator(f"#committee-detail a[href*='/collections/mrc/{item_id}/tor']")
    expect(link).to_be_visible()
