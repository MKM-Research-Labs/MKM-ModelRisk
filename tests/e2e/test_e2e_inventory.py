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
    # Edit a free-text field (owner is a people-reference dropdown now).
    page.click("[data-edit='methodology']")
    page.fill("#ed-input", "Regression")
    page.click("#ed-save")
    confirm(page)
    expect(page.locator("#row-methodology")).to_contain_text("Regression")


def test_edit_lifecycle_stage_choice(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-004", "PD Model")
    open_model(page, "MKM-E2E-004")
    edit_model_field(page, "lifecycle_stage", "Production", choice=True)
    expect(page.locator("#row-lifecycle_stage")).to_contain_text("Production")


def test_next_review_is_read_only(page: Page, base_url: str):
    # Next review is set by the MRC at sign-off, not edited by hand on the overview.
    open_app(page, base_url)
    register_model(page, "MKM-E2E-005", "LGD Model")
    open_model(page, "MKM-E2E-005")
    expect(page.locator("#row-next_review_date")).to_be_visible()
    expect(page.locator("[data-edit='next_review_date']")).to_have_count(0)


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
    page.click("[data-dtab='danger']")
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
    # Seed model + Company MRC + meeting via API (UI paths are covered elsewhere).
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    page.request.post(base_url + "/api/models",
                      data={"model_id": "MKM-X1-SO-01", "name": "Signoff History Model",
                            "confirmed": True}, headers=headers)
    page.request.post(base_url + "/api/reference/collections/mrc",
                      data={"fields": {"value": "MRC-X1-SO-CO", "name": "Company MRC",
                                       "level": "Company", "quorum_require_chair": "No",
                                       "quorum_require_secretary": "No", "quorum_min_voting": "0"},
                                      "confirmed": True}, headers=headers)
    page.request.post(base_url + "/api/meetings",
                      data={"meeting_id": "MRC-X1-SO", "title": "Signoff Meeting",
                            "date": "2026-11-11", "fields": {"mrc": "MRC-X1-SO-CO"},
                            "confirmed": True}, headers=headers)
    open_app(page, base_url)
    open_model(page, "MKM-X1-SO-01")
    edit_model_field(page, "materiality", "High", choice=True)
    expect(page.locator("#row-materiality")).to_contain_text("High")
    edit_model_field(page, "complexity", "Low", choice=True)  # -> Amber cell
    expect(page.locator("#row-complexity")).to_contain_text("Low")
    page.click("[data-dtab='risk']")
    # Auto-routes to the model's Company-level MRC and attaches to its meeting.
    page.click("#req-signoff")
    confirm(page)
    # MRC approves from the Models tab — sign-offs live under Models → Approvals
    # now (data-agapprove hook), and the committee is quorate (quorum off above).
    open_tab(page, "mrc")
    page.click("tr.clickable[data-id='MRC-X1-SO']")
    page.click("[data-mtab='models_in_scope']")
    page.locator("[data-agapprove]").first.click()
    confirm(page)
    # Back to the model — Risk tab now shows the history table.
    open_tab(page, "inventory")
    open_model(page, "MKM-X1-SO-01")
    page.click("[data-dtab='risk']")
    body = page.locator("#dt-content")
    expect(body).to_contain_text("Sign-off history")
    expect(body).to_contain_text("MRC-X1-SO")
    expect(body).to_contain_text("Amber")  # the "To" column of the history row


# test_register_with_company_assignment — retired.
# Phase MRC-5 removed the Company reference list and the Company field on the
# register modal. The instance IS a single institution now; every model is
# implicitly under it.


# --- X2 coverage: retired read-only, org-scope filter, per-model audit ------

def test_retired_model_hides_edit_and_danger_zone(page: Page, base_url: str):
    """Once retired, edit pencils vanish and the Danger tab shows a read-only note."""
    open_app(page, base_url)
    register_model(page, "MKM-X2-RET", "Legacy Model")
    open_model(page, "MKM-X2-RET")
    page.click("[data-dtab='danger']")
    page.click("#d-retire")
    confirm(page)
    open_model(page, "MKM-X2-RET")  # reopen after list re-render
    # Danger tab now shows the read-only note, not the retire card.
    page.click("[data-dtab='danger']")
    expect(page.locator("#dt-content")).to_contain_text("read-only")
    expect(page.locator(".danger-zone")).to_have_count(0)
    # No edit pencils on any Overview row.
    page.click("[data-dtab='overview']")
    expect(page.locator("[data-edit]")).to_have_count(0)
    # "Read only" badge is shown somewhere in the detail.
    expect(page.locator("#m-detail")).to_contain_text("retired")


# test_org_scope_header_filters_inventory — retired.
# Phase MRC-5 replaced the header Company dropdown with a static institution
# display. There is no filter to narrow — every inventory row belongs to the
# one institution.


def test_per_model_audit_tab_shows_recorded_events(page: Page, base_url: str):
    """The model's Audit dtab renders the events recorded against it."""
    open_app(page, base_url)
    register_model(page, "MKM-X2-AUD", "Audit Model")
    open_model(page, "MKM-X2-AUD")
    # Edit a free-text field (owner is a people-reference dropdown now).
    edit_model_field(page, "methodology", "Regression")
    expect(page.locator("#row-methodology")).to_contain_text("Regression")
    page.click("[data-dtab='audit']")
    body = page.locator("#dt-content")
    # Register + field-update events should both appear as event-type rows.
    expect(body).to_contain_text("ModelRegistered")
    expect(body).to_contain_text("ModelFieldUpdated")
    # Actor stamped on each row (dev@localhost is the fallback SSO identity).
    expect(body).to_contain_text("dev@localhost")


def test_model_actions_with_update_history(page: Page, base_url: str):
    """Actions are owned by the model: add one, then file a dated update — the
    update history grows and the action's target tracks the latest update."""
    open_app(page, base_url)
    register_model(page, "MKM-ACT-01", "Action Model")
    open_model(page, "MKM-ACT-01")
    page.click("[data-dtab='actions']")
    page.fill("#act-desc", "Revalidate the PD curve")
    page.fill("#act-target", "2026-09-30")
    page.click("#act-add")
    confirm(page)
    card = page.locator("#actions-list .card").first
    expect(card).to_contain_text("Revalidate the PD curve")
    # Seeded with one "Raised" update.
    expect(card.locator(".prow")).to_have_count(1)
    # File an update with a revised target.
    item_id = page.locator("[data-act-update]").first.get_attribute("data-act-update")
    page.fill(f"#upd-note-{item_id}", "Data delayed; revised")
    page.fill(f"#upd-target-{item_id}", "2026-11-30")
    page.click(f"[data-act-update='{item_id}']")
    confirm(page)
    card = page.locator("#actions-list .card").first
    expect(card.locator(".prow")).to_have_count(2)
    expect(card).to_contain_text("2026-11-30")


# --- Inventory UX: summary tiles, per-column filters, sortable table ---------


def test_inventory_summary_tiles_render(page: Page, base_url: str):
    """The stat tiles (total, per-tier, review buckets, assessed) all render."""
    open_app(page, base_url)
    register_model(page, "MKM-TILE-01", "Tile Model")
    summary = page.locator("#m-summary")
    for label in ["Total Models", "Tier 1", "Tier 2", "Tier 3",
                  "Overdue", "Due Soon", "Assessed"]:
        expect(summary).to_contain_text(label)


def test_inventory_sort_by_id_toggles(page: Page, base_url: str):
    """Clicking the ID header sorts, and clicking again reverses."""
    open_app(page, base_url)
    register_model(page, "MKM-SORT-A", "Alpha")
    register_model(page, "MKM-SORT-B", "Bravo")
    # Default: ascending by ID, so A is first.
    expect(page.locator("#m-table tbody tr").first).to_have_attribute("data-id", "MKM-SORT-A")
    page.click("#m-table th[data-sort='model_id']")   # reverse
    expect(page.locator("#m-table tbody tr").first).to_have_attribute("data-id", "MKM-SORT-B")


def test_inventory_search_filters_rows(page: Page, base_url: str):
    """The search box narrows the table; a non-match shows the empty state."""
    open_app(page, base_url)
    register_model(page, "MKM-FIND-01", "Findable")
    register_model(page, "MKM-HIDE-02", "Other")
    page.fill("#mf-q", "Findable")
    expect(page.locator("tr.clickable[data-id='MKM-FIND-01']")).to_have_count(1)
    expect(page.locator("tr.clickable[data-id='MKM-HIDE-02']")).to_have_count(0)
    page.fill("#mf-q", "zzzzz")
    expect(page.locator("#m-table")).to_contain_text("No models match")


def _set_field(page: Page, base_url: str, model_id: str, field: str, value) -> None:
    """Set one scalar field via the API.

    The list view is what's under test here, so drive the data straight in rather
    than through per-field detail editors (which differ by field: RAG has a
    bespoke owner/table control, tier its own picker).
    """
    page.request.post(
        f"{base_url}/api/models/{model_id}/field",
        data={"field": field, "value": value, "confirmed": True},
        headers={"X-Auth-Request-User": "e2e", "Content-Type": "application/json"},
    )


def _reload_list(page: Page, base_url: str, expected_rows: int) -> None:
    """Reload the console and wait for the list to settle before interacting.

    Mounting the list resets the filter state and rebuilds the filter controls,
    so acting before the mount completes can land on a control that is then
    replaced — and the change is lost with the detached node. Waiting on the row
    count pins the interaction to the final render.
    """
    open_app(page, base_url)
    expect(page.locator("#m-table tbody tr")).to_have_count(expected_rows)


def test_inventory_filter_by_rag(page: Page, base_url: str):
    """The RAG dropdown narrows the table to matching models."""
    open_app(page, base_url)
    register_model(page, "MKM-RAG-AM", "Amber One")
    register_model(page, "MKM-RAG-GR", "Green One")
    _set_field(page, base_url, "MKM-RAG-AM", "rag_rating", "Amber")
    _set_field(page, base_url, "MKM-RAG-GR", "rag_rating", "Green")
    _reload_list(page, base_url, 2)
    page.select_option("#mf-rag", "Amber")
    expect(page.locator("tr.clickable[data-id='MKM-RAG-AM']")).to_have_count(1)
    expect(page.locator("tr.clickable[data-id='MKM-RAG-GR']")).to_have_count(0)


def test_inventory_tier_tile_toggles_filter(page: Page, base_url: str):
    """Clicking a Tier tile filters the table to that tier and back."""
    open_app(page, base_url)
    register_model(page, "MKM-TIER-01", "Tiered Model")
    _set_field(page, base_url, "MKM-TIER-01", "tier", 2)  # tier is an int server-side
    _reload_list(page, base_url, 1)
    page.click("#m-summary [data-tile='tier=2']")
    expect(page.locator("#mf-tier")).to_have_value("2")
    expect(page.locator("tr.clickable[data-id='MKM-TIER-01']")).to_have_count(1)
    page.click("#m-summary [data-tile='tier=2']")   # clicking again clears it
    expect(page.locator("#mf-tier")).to_have_value("")
