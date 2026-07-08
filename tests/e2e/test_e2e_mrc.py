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
"""MRC e2e: schedule a meeting, bulk-add minutes, multi-select models in scope,
project meeting decisions / actions onto the model detail."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_model, open_tab, register_model

pytestmark = pytest.mark.e2e


def _seed_default_mrc(page: Page, base_url: str) -> None:
    """Seed a Company-level MRC committee via API. mrc.js hides the schedule
    form until at least one committee exists (Phase MRC-5)."""
    page.request.post(
        base_url + "/api/reference/collections/mrc",
        data={"fields": {"value": "MRC-DEFAULT", "name": "Default MRC", "level": "Company"},
              "confirmed": True},
        headers={"X-Auth-Request-User": "e2e", "Content-Type": "application/json"},
    )


def _schedule(page: Page, base_url: str, meeting_id: str, title: str):
    """Seed a default committee, open the MRC tab, fill the schedule form."""
    _seed_default_mrc(page, base_url)
    open_tab(page, "mrc")
    page.fill("#sc-meeting_id", meeting_id)
    page.fill("#sc-title", title)
    page.fill("#sc-date", "2026-09-15")
    page.click("#mt-schedule")
    confirm(page)


def test_schedule_meeting_appears(page: Page, base_url: str):
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-2026-Q3", "Q3 Model Risk Committee")
    expect(page.locator("tr.clickable[data-id='MRC-2026-Q3']")).to_contain_text("Q3 Model Risk Committee")


def test_double_click_opens_meeting_detail(page: Page, base_url: str):
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-2026-Q4", "Q4 Model Risk Committee")
    page.dblclick("tr.clickable[data-id='MRC-2026-Q4']")
    detail = page.locator("#mt-detail")
    expect(detail).to_contain_text("Q4 Model Risk Committee")
    expect(detail).to_contain_text("Agenda")
    expect(detail).to_contain_text("Meeting Pack PDF")


def test_bulk_add_minutes(page: Page, base_url: str):
    """Fill three of the five minutes rows and save them in one go."""
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-2026-BLK", "Bulk Minutes")
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

    _schedule(page, base_url, "MRC-MS", "Multi-select")
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


def test_meeting_pack_pdf_downloads(page: Page, base_url: str):
    """The Meeting Pack PDF endpoint returns an application/pdf response."""
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-PACK", "Pack Meeting")
    response = page.request.get(f"{base_url}/api/meetings/MRC-PACK/pack.pdf")
    if response.status != 200:
        # tectonic not installed on this machine — record the skip cleanly.
        assert "tectonic" in response.text().lower() or response.status == 500
        pytest.skip("tectonic not installed (optional)")
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.body()[:5] == b"%PDF-"


def _edit_meeting_field(page: Page, key: str, value: str) -> None:
    """Edit a scalar meeting field via the chip's inline editor."""
    page.click(f"[data-minfo='{key}']")
    selector = "#mf-input"
    if page.locator(selector).evaluate("el => el.tagName") == "SELECT":
        page.select_option(selector, value)
    else:
        page.fill(selector, value)
    page.click("#mf-save")
    confirm(page)


# chair is no longer a scalar meeting field — it's derived from the meeting's
# bound MRC. See test_derive_org_scope_* in tests/governance/test_mrc_projection.


def test_edit_meeting_location(page: Page, base_url: str):
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-EDIT-2", "Editable Meeting")
    page.dblclick("tr.clickable[data-id='MRC-EDIT-2']")
    _edit_meeting_field(page, "location", "Room 204, 1 Lombard Court")
    expect(page.locator("#minfo-location")).to_contain_text("Room 204")


def test_edit_meeting_status_choice(page: Page, base_url: str):
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-EDIT-3", "Editable Meeting")
    page.dblclick("tr.clickable[data-id='MRC-EDIT-3']")
    _edit_meeting_field(page, "status", "Completed")
    expect(page.locator("#minfo-status")).to_contain_text("Completed")


# --- X2 coverage: bulk-add for the other three collection tabs --------------

def test_add_agenda_items(page: Page, base_url: str):
    """Agenda uses a bespoke card-per-item renderer (per-item approve/escalate),
    not the shared Collections bulk-add — add items one at a time."""
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-BULK-AG", "Bulk Agenda")
    page.dblclick("tr.clickable[data-id='MRC-BULK-AG']")
    page.click("[data-mtab='agenda']")
    for i, title in enumerate(("Item A", "Item B"), start=1):
        page.fill("#ag-add-title", title)
        page.click("#ag-add")
        confirm(page)
        expect(page.locator("[data-mtab='agenda']")).to_contain_text(f"({i})")
    expect(page.locator("#agenda-list")).to_contain_text("Item A")
    expect(page.locator("#agenda-list")).to_contain_text("Item B")


def test_bulk_add_decisions(page: Page, base_url: str):
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-BULK-DC", "Bulk Decisions")
    page.dblclick("tr.clickable[data-id='MRC-BULK-DC']")
    page.click("[data-mtab='decisions']")
    page.fill("#badd-decisions-0-description", "Decision one")
    page.fill("#badd-decisions-1-description", "Decision two")
    page.fill("#badd-decisions-2-description", "Decision three")
    page.click("[data-bulk-add='decisions']")
    confirm(page)
    expect(page.locator("[data-mtab='decisions']")).to_contain_text("(3)")


def test_bulk_add_actions(page: Page, base_url: str):
    open_app(page, base_url)
    _schedule(page, base_url, "MRC-BULK-AC", "Bulk Actions")
    page.dblclick("tr.clickable[data-id='MRC-BULK-AC']")
    page.click("[data-mtab='actions']")
    page.fill("#badd-actions-0-description", "Follow up with Priya")
    page.fill("#badd-actions-1-description", "Schedule validation review")
    page.click("[data-bulk-add='actions']")
    confirm(page)
    expect(page.locator("[data-mtab='actions']")).to_contain_text("(2)")


def _bulk_add_decision(page: Page, description: str, model_id: str):
    """Use the bulk-add form on the Decisions tab to add a single linked item."""
    page.click("[data-mtab='decisions']")
    page.fill("#badd-decisions-0-description", description)
    page.select_option("#badd-decisions-0-model_id", model_id)
    page.click("[data-bulk-add='decisions']")
    confirm(page)


def test_signoff_workflow_owner_requests_and_mrc_approves(page: Page, base_url: str):
    """W4c end-to-end: owner requests sign-off; MRC approves; model RAG snaps."""
    open_app(page, base_url)
    register_model(page, "MKM-SO-01", "Sign-off Model")
    # Schedule a meeting so the request modal has a target.
    _schedule(page, base_url, "MRC-SO", "Sign-off Meeting")
    # Set materiality + complexity to place it on the heatmap (Amber cell).
    open_tab(page, "inventory")
    open_model(page, "MKM-SO-01")
    from tests.e2e._flows import edit_model_field
    edit_model_field(page, "materiality", "High", choice=True)
    expect(page.locator("#row-materiality")).to_contain_text("High")
    edit_model_field(page, "complexity", "Low", choice=True)
    expect(page.locator("#row-complexity")).to_contain_text("Low")
    # Risk Rating tab → Request sign-off.
    page.click("[data-dtab='risk']")
    expect(page.locator("#req-signoff")).to_be_visible()
    page.click("#req-signoff")
    page.select_option("#signoff-meeting-pick", "MRC-SO")
    page.click("#signoff-submit")
    confirm(page)
    # Pending-signoff panel shows on the model.
    expect(page.locator("#dt-content")).to_contain_text("Pending MRC sign-off")
    expect(page.locator("#dt-content")).to_contain_text("MRC-SO")
    # MRC approves via the agenda tab.
    open_tab(page, "mrc")
    page.dblclick("tr.clickable[data-id='MRC-SO']")
    page.click("[data-mtab='agenda']")
    approve = page.locator("[data-agapprove]").first
    expect(approve).to_be_visible()
    approve.click()
    confirm(page)
    # Model's approved rag_rating is now Amber (the heatmap value).
    open_tab(page, "inventory")
    row = page.locator("tr.clickable[data-id='MKM-SO-01']")
    expect(row).to_contain_text("Amber")


def test_decision_linked_to_model_appears_on_model_detail(page: Page, base_url: str):
    """A linked decision projects onto the model's read-only Decisions tab."""
    open_app(page, base_url)
    register_model(page, "MKM-LINK-001", "Linked Model")

    _schedule(page, base_url, "MRC-LINK", "Linked Meeting")
    page.dblclick("tr.clickable[data-id='MRC-LINK']")
    _bulk_add_decision(page, "Approve recalibration", "MKM-LINK-001")

    # Back to the inventory, open the model, switch to Decisions tab.
    open_tab(page, "inventory")
    open_model(page, "MKM-LINK-001")
    page.click("[data-dtab='decisions']")
    box = page.locator("#dt-content")
    expect(box).to_contain_text("Approve recalibration")
    expect(box).to_contain_text("Linked Meeting")
    expect(box).to_contain_text("MRC-LINK")
    expect(page.locator("[data-dtab='decisions']")).to_contain_text("(1)")


def test_meeting_models_tab_scoped_to_department_mrc(page: Page, base_url: str):
    """Phase MRC-3: a Department-level MRC's meeting only lists models in that
    department; the "Show all" toggle escapes.

    Seeds everything via the API — the UI paths for reference lists and model
    registration are already covered elsewhere; this test is about the filter.
    """
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    # Org tree — Phase MRC-5: the single institution is implicit; only the
    # Division/Department tiers are stored as reference lists.
    page.request.post(base_url + "/api/reference/collections/division",
                      data={"fields": {"value": "Markets"}, "confirmed": True}, headers=headers)
    for name, division in (("Rates Trading", "Markets"), ("Equity Derivatives", "Markets")):
        page.request.post(base_url + "/api/reference/collections/department",
                          data={"fields": {"value": name, "division": division},
                                "confirmed": True}, headers=headers)
    # A Department-level MRC anchored to Rates Trading.
    page.request.post(base_url + "/api/reference/collections/mrc",
                      data={"fields": {"value": "MRC-DEPT-RATES", "name": "Rates MRC",
                                       "level": "Department", "scope_value": "Rates Trading"},
                            "confirmed": True}, headers=headers)
    # Two models, one in Rates Trading, one in Equity Derivatives.
    for model_id, dept in (("MRC-M-RATES", "Rates Trading"),
                           ("MRC-M-EQD", "Equity Derivatives")):
        page.request.post(base_url + "/api/models",
                          data={"model_id": model_id, "name": model_id,
                                "fields": {"division": "Markets", "department": dept},
                                "confirmed": True}, headers=headers)
    # Schedule a meeting bound to the Department MRC.
    page.request.post(base_url + "/api/meetings",
                      data={"meeting_id": "MRC-M3", "title": "Rates review",
                            "date": "2026-08-01", "fields": {"mrc": "MRC-DEPT-RATES"},
                            "confirmed": True}, headers=headers)

    open_app(page, base_url)
    open_tab(page, "mrc")
    page.dblclick("tr.clickable[data-id='MRC-M3']")
    page.click("[data-mtab='models_in_scope']")
    # Only the Rates Trading model is a candidate; the Equity Derivatives one is hidden.
    expect(page.locator("[data-mscope='MRC-M-RATES']")).to_be_visible()
    expect(page.locator("[data-mscope='MRC-M-EQD']")).to_have_count(0)
    # Toggle "Show all" — both appear.
    page.check("#mt-show-all")
    expect(page.locator("[data-mscope='MRC-M-EQD']")).to_be_visible()


def test_escalate_signoff_moves_it_to_parent_meeting(page: Page, base_url: str):
    """Phase MRC-4: the chair escalates a sign-off to a higher-tier meeting."""
    # Seed the model, two MRC committees + two Scheduled meetings via API.
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    page.request.post(base_url + "/api/models",
                      data={"model_id": "MKM-ESC-01", "name": "Escalation Model",
                            "confirmed": True}, headers=headers)
    for value, name, level in (("MRC-ESC-CO", "Company MRC", "Company"),
                                ("MRC-ESC-DEPT", "Dept MRC", "Company")):
        page.request.post(base_url + "/api/reference/collections/mrc",
                          data={"fields": {"value": value, "name": name, "level": level},
                                "confirmed": True}, headers=headers)
    for meeting_id, mrc in (("MRC-DEPT-ESC", "MRC-ESC-DEPT"),
                             ("MRC-DIV-ESC", "MRC-ESC-CO")):
        page.request.post(base_url + "/api/meetings",
                          data={"meeting_id": meeting_id, "title": meeting_id,
                                "date": "2026-11-01", "fields": {"mrc": mrc},
                                "confirmed": True}, headers=headers)
    open_app(page, base_url)
    open_model(page, "MKM-ESC-01")
    from tests.e2e._flows import edit_model_field
    edit_model_field(page, "materiality", "High", choice=True)
    expect(page.locator("#row-materiality")).to_contain_text("High")
    edit_model_field(page, "complexity", "Low", choice=True)
    expect(page.locator("#row-complexity")).to_contain_text("Low")
    page.click("[data-dtab='risk']")
    page.click("#req-signoff")
    page.select_option("#signoff-meeting-pick", "MRC-DEPT-ESC")
    page.click("#signoff-submit")
    confirm(page)
    # The mrc.js meeting list is filtered by the currently-selected committee
    # (top-of-page tabs). Switch to the Department committee first.
    open_tab(page, "mrc")
    page.click("[data-mrc='MRC-ESC-DEPT']")
    page.dblclick("tr.clickable[data-id='MRC-DEPT-ESC']")
    page.click("[data-mtab='agenda']")
    page.locator("[data-agescalate]").first.click()
    expect(page.locator("#signoff-overlay")).to_be_visible()
    expect(page.locator("#signoff-meeting-pick option", has_text="MRC-DIV-ESC")).to_have_count(1)
    page.select_option("#signoff-meeting-pick", "MRC-DIV-ESC")
    page.click("#signoff-submit")
    confirm(page)
    # Switch to the parent committee and open its meeting.
    open_tab(page, "mrc")
    page.click("[data-mrc='MRC-ESC-CO']")
    page.dblclick("tr.clickable[data-id='MRC-DIV-ESC']")
    page.click("[data-mtab='agenda']")
    expect(page.locator("#mtd-content")).to_contain_text("[Escalated]")
    expect(page.locator("#mtd-content")).to_contain_text("MKM-ESC-01")
