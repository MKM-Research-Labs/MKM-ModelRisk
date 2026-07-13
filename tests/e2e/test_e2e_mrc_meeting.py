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
"""MRC meeting-detail e2e: the Models tab (presenter + analysis upload) and the
Participants tab (committee roster + guests)."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_tab, register_model

pytestmark = pytest.mark.e2e

_HEADERS = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}


def _schedule(page: Page, base_url: str, meeting_id: str, title: str) -> None:
    """Seed a Company-level committee (quorum requirements off, so meetings are
    quorate with no attendance) and schedule a meeting bound to it."""
    page.request.post(base_url + "/api/reference/collections/mrc",
                      data={"fields": {"value": "MRC-DEFAULT", "name": "Default MRC",
                                       "level": "Company", "quorum_require_chair": "No",
                                       "quorum_require_secretary": "No", "quorum_min_voting": "0",
                                       "quorum_min_non_voting": "0"}, "confirmed": True},
                      headers=_HEADERS)
    # Seeded via the API — drop MrcNav's cached reference data so the MRC tab
    # sees the new committee and renders the schedule form.
    page.evaluate("typeof MrcNav !== 'undefined' && MrcNav.invalidate()")
    open_tab(page, "mrc")
    page.fill("#sc-meeting_id", meeting_id)
    page.fill("#sc-title", title)
    page.fill("#sc-date", "2026-09-15")
    page.click("#mt-schedule")
    confirm(page)


def test_model_analysis_upload_on_models_tab(page: Page, base_url: str, tmp_path):
    """The Models tab's Analysis column lets you upload a per-model analysis
    document for an in-scope model, and pick a presenter."""
    page.request.post(base_url + "/api/reference/collections/people",
                      data={"fields": {"name": "Pat Presenter"}, "confirmed": True}, headers=_HEADERS)
    open_app(page, base_url)
    register_model(page, "MKM-AN-01", "Analysis Model")
    _schedule(page, base_url, "MRC-AN", "Analysis Meeting")
    page.click("tr.clickable[data-id='MRC-AN']")
    page.click("[data-mtab='models_in_scope']")
    expect(page.locator("#mtd-content")).to_contain_text("Analysis")
    expect(page.locator("#mtd-content")).to_contain_text("Presenter")
    # Put the model in scope so it can carry a presenter + analysis file.
    page.check("[data-mscope='MKM-AN-01']")
    page.click("#mt-save-models")
    confirm(page)
    # Assign a presenter (dropdown of people).
    page.select_option("[data-presenter='MKM-AN-01']", "Pat Presenter")
    confirm(page)
    expect(page.locator("[data-presenter='MKM-AN-01']")).to_have_value("Pat Presenter")
    # Upload the analysis document.
    analysis = tmp_path / "analysis.pdf"
    analysis.write_bytes(b"%PDF-1.4 analysis")
    page.set_input_files("#an-file-MKM-AN-01", str(analysis))
    expect(page.locator("#mtd-content")).to_contain_text("analysis.pdf")


def test_meeting_participants_roster_and_guests(page: Page, base_url: str):
    """A meeting lists its committee's roster (in the persistent left panel) and
    lets you add a guest — a person from the register who is not a member."""
    for name in ("David Kelly", "Sofia Castro", "Greg Guest"):
        page.request.post(base_url + "/api/reference/collections/people",
                          data={"fields": {"name": name}, "confirmed": True}, headers=_HEADERS)
    page.request.post(base_url + "/api/reference/collections/mrc",
                      data={"fields": {"value": "MRC-P", "name": "Participants MRC",
                                       "level": "Company"}, "confirmed": True}, headers=_HEADERS)
    ref = page.request.get(base_url + "/api/reference").json()
    cid = next(c["item_id"] for c in ref["data"]["mrc"] if c["value"] == "MRC-P")
    page.request.post(base_url + "/api/reference/collections/mrc/" + cid,
                      data={"fields": {"chair": "David Kelly", "voting_members": ["Sofia Castro"]},
                            "confirmed": True}, headers=_HEADERS)
    page.request.post(base_url + "/api/meetings",
                      data={"meeting_id": "MTG-P", "title": "Participants Meeting",
                            "date": "2026-10-01", "fields": {"mrc": "MRC-P"},
                            "confirmed": True}, headers=_HEADERS)
    open_app(page, base_url)
    open_tab(page, "mrc")
    page.click("tr.clickable[data-id='MTG-P']")
    # Participants are shown in the persistent left panel, not a tab.
    panel = page.locator(".mtd-left")
    expect(panel).to_contain_text("David Kelly")
    expect(panel).to_contain_text("Chair")
    expect(panel).to_contain_text("Sofia Castro")
    expect(panel).to_contain_text("Voting")
    # Add a non-member as a guest.
    page.select_option("#guest-pick", "Greg Guest")
    page.click("#guest-add")
    confirm(page)
    expect(page.locator(".mtd-left")).to_contain_text("Greg Guest")
