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
    open_tab,
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


def test_risk_heatmap_reflects_materiality_and_complexity(page: Page, base_url: str):
    """W4a: setting Materiality + Complexity places the model on the heatmap."""
    open_app(page, base_url)
    register_model(page, "MKM-E2E-HM-01", "Heatmap Model")
    open_model(page, "MKM-E2E-HM-01")
    edit_model_field(page, "materiality", "High", choice=True)
    expect(page.locator("#row-materiality")).to_contain_text("High")
    edit_model_field(page, "complexity", "Low", choice=True)
    expect(page.locator("#row-complexity")).to_contain_text("Low")
    page.click("[data-dtab='risk']")
    # High Materiality × Low Complexity → Amber per the config lookup.
    banner = page.locator("#dt-content .riskbanner")
    expect(banner).to_contain_text("Amber")
    expect(banner).to_contain_text("High")
    expect(banner).to_contain_text("Low")
    # The events counter renders (zero for a fresh model).
    expect(page.locator("#dt-content")).to_contain_text("Events (past 365 days)")


def test_risk_composite_breakdown_renders(page: Page, base_url: str):
    """The 5-component composite breakdown surfaces on the Risk Rating tab."""
    open_app(page, base_url)
    register_model(page, "MKM-X1-RC-01", "Composite Model")
    open_model(page, "MKM-X1-RC-01")
    page.click("[data-dtab='risk']")
    body = page.locator("#dt-content")
    expect(body).to_contain_text("Composite Score")
    expect(body).to_contain_text("Validation Coverage")
    expect(body).to_contain_text("Remediation Health")
    expect(body).to_contain_text("Review Currency")
    expect(body).to_contain_text("Assumption Risk")
    expect(body).to_contain_text("Limitation Risk")


def test_events_counter_reflects_recent_event(page: Page, base_url: str):
    """Adding an event bumps the past-year counter on the Risk Rating tab."""
    open_app(page, base_url)
    register_model(page, "MKM-X1-EV-01", "Events Counter Model")
    open_model(page, "MKM-X1-EV-01")
    page.click("[data-dtab='risk']")
    expect(page.locator("#dt-content")).to_contain_text("Events (past 365 days)")
    # Add a recent event, then re-open the Risk tab.
    page.click("[data-dtab='operational_failure_events']")
    from tests.e2e._flows import add_collection_item
    add_collection_item(
        page, "operational_failure_events",
        {"date": "2026-06-01", "description": "Recent incident"},
    )
    page.click("[data-dtab='risk']")
    events_card = page.locator(".scard", has_text="Events (past 365 days)")
    expect(events_card).to_contain_text("1")


def test_signoff_history_renders_on_risk_tab(page: Page, base_url: str):
    """Approved sign-offs surface as a chronological table on the Risk tab (W4c)."""
    open_app(page, base_url)
    register_model(page, "MKM-X1-SO-01", "Signoff History Model")
    # Schedule + request + approve a sign-off; check history appears.
    open_tab(page, "mrc")
    page.fill("#sc-meeting_id", "MRC-X1-SO")
    page.fill("#sc-title", "Signoff Meeting")
    page.fill("#sc-date", "2026-11-11")
    page.click("#mt-schedule")
    confirm(page)
    open_tab(page, "inventory")
    open_model(page, "MKM-X1-SO-01")
    edit_model_field(page, "materiality", "High", choice=True)
    expect(page.locator("#row-materiality")).to_contain_text("High")
    edit_model_field(page, "complexity", "Low", choice=True)  # -> Amber cell
    expect(page.locator("#row-complexity")).to_contain_text("Low")
    page.click("[data-dtab='risk']")
    page.click("#req-signoff")
    page.select_option("#signoff-meeting-pick", "MRC-X1-SO")
    page.click("#signoff-submit")
    confirm(page)
    # MRC approves.
    open_tab(page, "mrc")
    page.dblclick("tr.clickable[data-id='MRC-X1-SO']")
    page.click("[data-mtab='agenda']")
    page.get_by_text("Approve sign-off").first.click()
    confirm(page)
    # Back to the model — Risk tab now shows the history table.
    open_tab(page, "inventory")
    open_model(page, "MKM-X1-SO-01")
    page.click("[data-dtab='risk']")
    body = page.locator("#dt-content")
    expect(body).to_contain_text("Sign-off history")
    expect(body).to_contain_text("MRC-X1-SO")
    expect(body).to_contain_text("Amber")  # the "To" column of the history row


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


# --- X2 coverage: retired read-only, org-scope filter, per-model audit ------

def test_retired_model_hides_edit_and_danger_zone(page: Page, base_url: str):
    """Once retired, edit pencils vanish and the Danger Zone is suppressed."""
    open_app(page, base_url)
    register_model(page, "MKM-X2-RET", "Legacy Model")
    open_model(page, "MKM-X2-RET")
    page.click("#d-retire")
    confirm(page)
    open_model(page, "MKM-X2-RET")  # reopen after list re-render
    # No danger zone.
    expect(page.locator(".danger-zone")).to_have_count(0)
    # No edit pencils on any Overview row.
    expect(page.locator("[data-edit]")).to_have_count(0)
    # "Read only" badge is shown somewhere in the detail.
    expect(page.locator("#m-detail")).to_contain_text("retired")


def test_org_scope_header_filters_inventory(page: Page, base_url: str):
    """Setting the header Company filter narrows the inventory list."""
    # Seed reference data + models directly via the API — the UI paths are
    # already covered by test_company_create and test_register_with_company_assignment.
    # Here we're isolating the header-scope filter.
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    for value in ("Alpha Bank", "Beta Bank"):
        page.request.post(
            base_url + "/api/reference/collections/company",
            data={"fields": {"value": value}, "confirmed": True}, headers=headers,
        )
    for model_id, company in [("MKM-X2-FA", "Alpha Bank"), ("MKM-X2-FB", "Beta Bank")]:
        page.request.post(
            base_url + "/api/models",
            data={"model_id": model_id, "name": model_id + " Model",
                  "fields": {"company": company}, "confirmed": True},
            headers=headers,
        )
    open_app(page, base_url)
    # Both visible under "All companies".
    expect(page.locator("tr.clickable[data-id='MKM-X2-FA']")).to_be_visible()
    expect(page.locator("tr.clickable[data-id='MKM-X2-FB']")).to_be_visible()
    # Narrow to Alpha Bank — only MKM-X2-FA remains.
    page.select_option("#scope-company", "Alpha Bank")
    expect(page.locator("tr.clickable[data-id='MKM-X2-FA']")).to_be_visible()
    expect(page.locator("tr.clickable[data-id='MKM-X2-FB']")).to_have_count(0)


def test_per_model_audit_tab_shows_recorded_events(page: Page, base_url: str):
    """The model's Audit dtab renders the events recorded against it."""
    open_app(page, base_url)
    register_model(page, "MKM-X2-AUD", "Audit Model")
    open_model(page, "MKM-X2-AUD")
    edit_model_field(page, "owner", "Priya Anand")
    expect(page.locator("#row-owner")).to_contain_text("Priya Anand")
    page.click("[data-dtab='audit']")
    body = page.locator("#dt-content")
    # Register + field-update events should both appear as event-type rows.
    expect(body).to_contain_text("ModelRegistered")
    expect(body).to_contain_text("ModelFieldUpdated")
    # Actor stamped on each row (dev@localhost is the fallback SSO identity).
    expect(body).to_contain_text("dev@localhost")
