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
    # Methodology is not a gated field, so this applies without a confirm step.
    edit_model_field(page, "methodology", "Regression")
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


def test_rag_change_routes_to_mrc_signoff(page: Page, base_url: str):
    """A RAG change is a proposal, not an edit (W4c).

    Choosing a rating raises a sign-off request routed to the model's MRC; the
    rating itself must not move until the committee approves. This is the
    governance guarantee, so assert the domain state, not just the screen.
    """
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    page.request.post(base_url + "/api/models",
                      data={"model_id": "MKM-E2E-007", "name": "VaR Model",
                            "confirmed": True}, headers=headers)
    # _proposeRag refuses to route unless an MRC covers the model.
    page.request.post(base_url + "/api/reference/collections/mrc",
                      data={"fields": {"value": "MRC-E2E-RAG", "name": "Company MRC",
                                       "level": "Company"}, "confirmed": True}, headers=headers)
    open_app(page, base_url)
    open_model(page, "MKM-E2E-007")
    page.click("[data-edit='rag_rating']")
    page.select_option("#ed-input", "Amber")
    page.click("#ed-save")   # raises a request — not a gated field edit, so no modal
    # On success the detail jumps to the Risk tab: use that as the sync point.
    expect(page.locator("[data-dtab='risk'].active")).to_be_visible()

    model = page.request.get(base_url + "/api/models/MKM-E2E-007").json()
    data = model["data"]
    assert not data.get("rag_rating"), "rating must not change before MRC approval"
    proposed = [r.get("proposed_rag") for r in (data.get("signoff_requests") or [])]
    assert proposed == ["Amber"], f"expected one queued proposal, got {proposed}"


def _seed_mrc(page: Page, base_url: str, value: str = "MRC-E2E-RET"):
    """A Company-level MRC, so a model has a committee to route requests to."""
    page.request.post(
        base_url + "/api/reference/collections/mrc",
        data={"fields": {"value": value, "name": "Company MRC", "level": "Company",
                         "quorum_require_chair": "No", "quorum_require_secretary": "No",
                         "quorum_min_voting": "0"}, "confirmed": True},
        headers={"X-Auth-Request-User": "e2e", "Content-Type": "application/json"},
    )


def test_requesting_retire_queues_it_and_leaves_the_model_active(page: Page, base_url: str):
    """The Danger tab asks the MRC; it does not hibernate the model itself."""
    _seed_mrc(page, base_url)
    open_app(page, base_url)
    register_model(page, "MKM-E2E-008", "Legacy Model")
    open_model(page, "MKM-E2E-008")
    page.click("[data-dtab='danger']")
    page.click("#d-retire")
    confirm(page)   # requesting is gated: the owner confirms, the MRC then ratifies
    # The tab now reports the request, and the model is still active in the list.
    expect(page.locator("#dt-content")).to_contain_text("awaiting MRC ratification")
    expect(page.locator("tr.clickable[data-id='MKM-E2E-008']")).not_to_contain_text("retired")
    assert page.request.get(base_url + "/api/models/MKM-E2E-008").json()["retired"] is False


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
    """Approved sign-offs surface as a chronological table on the Risk tab (W4c).

    This covers the *rendering*, so the journey that produces the history is
    driven through the API: raising and approving via the UI is covered by
    test_rag_change_routes_to_mrc_signoff and the MRC tests, and doing it here
    only made the test race its own re-renders.
    """
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    post = lambda path, body: page.request.post(base_url + path, data=body, headers=headers)
    post("/api/models", {"model_id": "MKM-X1-SO-01", "name": "Signoff History Model",
                         "fields": {"materiality": "High", "complexity": "Low"},
                         "confirmed": True})
    post("/api/reference/collections/mrc",
         {"fields": {"value": "MRC-X1-SO-CO", "name": "Company MRC", "level": "Company",
                     "quorum_require_chair": "No", "quorum_require_secretary": "No",
                     "quorum_min_voting": "0"}, "confirmed": True})
    post("/api/meetings", {"meeting_id": "MRC-X1-SO", "title": "Signoff Meeting",
                           "date": "2026-11-11", "fields": {"mrc": "MRC-X1-SO-CO"},
                           "confirmed": True})
    post("/api/models/MKM-X1-SO-01/request-signoff",
         {"proposed_rag": "Amber", "confirmed": True})
    agenda = page.request.get(base_url + "/api/meetings/MRC-X1-SO").json()["data"]["agenda"]
    item = next(a for a in agenda if a.get("subject_model_id") == "MKM-X1-SO-01")
    approved = post(f"/api/meetings/MRC-X1-SO/agenda/{item['item_id']}/approve-signoff",
                    {"confirmed": True, "next_review_date": "2027-01-31"})
    assert approved.status == 200, approved.text()

    open_app(page, base_url)
    open_model(page, "MKM-X1-SO-01")
    page.click("[data-dtab='risk']")
    body = page.locator("#dt-content")
    expect(body).to_contain_text("Sign-off history")
    expect(body).to_contain_text("MRC-X1-SO")
    expect(body).to_contain_text("Amber")     # the "To" column of the history row
    expect(body).to_contain_text("2027-01-31")


# test_register_with_company_assignment — retired.
# Phase MRC-5 removed the Company reference list and the Company field on the
# register modal. The instance IS a single institution now; every model is
# implicitly under it.


# --- X2 coverage: retired read-only, org-scope filter, per-model audit ------

def _hibernate_via_mrc(page: Page, base_url: str, model_id: str):
    """Hibernate a model the only way there is: request it, then have the
    committee ratify it."""
    headers = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}
    _seed_mrc(page, base_url)
    page.request.post(base_url + "/api/meetings",
                      data={"meeting_id": "MTG-X2", "title": "Retire", "date": "2026-11-11",
                            "fields": {"mrc": "MRC-E2E-RET"}, "confirmed": True}, headers=headers)
    page.request.post(base_url + f"/api/models/{model_id}/request-retire",
                      data={"confirmed": True}, headers=headers)
    agenda = page.request.get(base_url + "/api/meetings/MTG-X2").json()["data"]["agenda"]
    item = next(a for a in agenda if a.get("signoff_kind") == "retire")
    page.request.post(
        base_url + f"/api/meetings/MTG-X2/agenda/{item['item_id']}/approve-signoff",
        data={"confirmed": True}, headers=headers)


def test_hibernated_model_is_read_only_but_can_be_asked_back(page: Page, base_url: str):
    """Once the MRC ratifies a retire the model is read-only — but hibernation is
    reversible, so the Danger tab offers to ask the committee to bring it back."""
    open_app(page, base_url)
    register_model(page, "MKM-X2-RET", "Legacy Model")
    _hibernate_via_mrc(page, base_url, "MKM-X2-RET")
    open_app(page, base_url)               # reload so the list reflects it
    open_model(page, "MKM-X2-RET")
    # No edit pencils on any Overview row.
    page.click("[data-dtab='overview']")
    expect(page.locator("[data-edit]")).to_have_count(0)
    expect(page.locator("#m-detail")).to_contain_text("retired")
    # The Danger tab offers the way back rather than a dead end.
    page.click("[data-dtab='danger']")
    expect(page.locator("#dt-content")).to_contain_text("hibernated")
    expect(page.locator("#d-reactivate")).to_be_visible()


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


# test_model_actions_with_update_history — retired.
# Actions are no longer managed from the model detail: the tab was dropped from
# Detail._tabbar and they are worked from the MRC meeting (Models in scope), which
# is where the committee revisits them. The orphaned panel it drove
# (inventory/detail_actions.js) has been removed with it.


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
