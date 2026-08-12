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
"""Product e2e for the components model.

A Product is now a list of typed component models plus a Calculating Agent
(``PRODUCT_BINDINGS == ('calculating_agent',)``), not a fixed analytics+MDM pair.
Registration binds only the agent; component models are added on the Components
tab, and the identifier derives (``<sorted model ids>.<agent>``) once the Product
has both a component and an agent.
"""
from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import (add_collection_item, confirm, maybe_confirm,
                              open_admin_subtab, open_app, open_tab, register_model)

pytestmark = pytest.mark.e2e


def _register_product(page: Page, product_id: str, product: str, agent: str = "Murex") -> None:
    """Register a Product. The only binding is the Calculating Agent; component
    models are bound afterwards on the Components tab."""
    open_tab(page, "product")
    page.click("#product-register")
    page.fill("#preg-product_id", product_id)
    page.fill("#preg-product", product)
    page.fill("#preg-calculating_agent", agent)
    page.click("#product-reg-submit")
    confirm(page)


def _open_product(page: Page, product_id: str) -> None:
    page.click(f"tr.clickable[data-id='{product_id}']")


def _add_component(page: Page, component_type: str, model_id: str, role: str) -> None:
    """Bind a typed component model on the Components tab (a generic collection:
    component_type + model_id render as reference dropdowns, role as text)."""
    page.click("[data-ptab='components']")
    add_collection_item(page, "components", {
        "component_type": component_type, "model_id": model_id, "role": role,
    })


def test_product_define_components_and_derived_identifier(page: Page, base_url: str):
    """The Components tab binds a typed model, and the identifier derives from the
    component models + agent once the Product is built out."""
    open_app(page, base_url)
    register_model(page, "MKM-E2E-CMP1", "GEV Hazard Curve")
    _register_product(page, "Product-E2E-001", "Physical Risk Swap")
    _open_product(page, "Product-E2E-001")
    expect(page.locator(".dtabs")).to_contain_text("Components")
    _add_component(page, "Analytical Model", "MKM-E2E-CMP1", "Pricing engine")
    expect(page.locator("#pt-content")).to_contain_text("MKM-E2E-CMP1")
    expect(page.locator("#pt-content")).to_contain_text("Analytical Model")
    # Identifier derives from <component model ids>.<agent> once built out.
    open_tab(page, "product")
    expect(page.locator("tr.clickable[data-id='Product-E2E-001']")).to_contain_text(
        "MKM-E2E-CMP1.Murex")


def test_product_multiple_components_sorted_identifier(page: Page, base_url: str):
    """A Product may bind several component models; the identifier sorts them so it
    reflects what the Product *is*, not the add order."""
    open_app(page, base_url)
    register_model(page, "MKM-E2E-CMP3", "Storm Intensity")
    register_model(page, "MKM-E2E-CMP2", "Depth-Damage")
    _register_product(page, "Product-E2E-00M", "Multi-Model Product")
    _open_product(page, "Product-E2E-00M")
    _add_component(page, "Statistical", "MKM-E2E-CMP3", "Hazard")
    _add_component(page, "Damage", "MKM-E2E-CMP2", "Loss")
    open_tab(page, "product")
    # Sorted (CMP2 before CMP3) regardless of the order they were added.
    expect(page.locator("tr.clickable[data-id='Product-E2E-00M']")).to_contain_text(
        "MKM-E2E-CMP2.MKM-E2E-CMP3.Murex")


def test_product_detail_tabs_and_rebind_agent(page: Page, base_url: str):
    open_app(page, base_url)
    _register_product(page, "Product-E2E-002", "Swaption")
    _open_product(page, "Product-E2E-002")
    expect(page.locator(".dtabs")).to_contain_text("Components")
    expect(page.locator(".dtabs")).to_contain_text("Limitations")
    expect(page.locator(".dtabs")).to_contain_text("Audit")
    page.click("[data-rebind='calculating_agent']")
    page.fill("#ped-input", "Calypso")
    page.click("#ped-save")
    maybe_confirm(page, "rebind_component", "calculating_agent")  # not gated: applies immediately
    expect(page.locator("#row-calculating_agent")).to_contain_text("Calypso")


def test_product_edit_status_field(page: Page, base_url: str):
    open_app(page, base_url)
    _register_product(page, "Product-E2E-003", "Equity Option")
    _open_product(page, "Product-E2E-003")
    page.click("[data-edit='status']")
    page.select_option("#ped-input", "Active")
    page.click("#ped-save")
    maybe_confirm(page, "update_product_field", "status")  # status is not gated
    expect(page.locator("#row-status")).to_contain_text("Active")


def test_product_governance_tabs_and_rag(page: Page, base_url: str):
    open_app(page, base_url)
    _register_product(page, "Product-E2E-004", "Government Bond")
    _open_product(page, "Product-E2E-004")
    expect(page.locator(".dtabs")).to_contain_text("Remediation")
    expect(page.locator(".dtabs")).to_contain_text("Docs")
    page.click("[data-edit='rag_rating']")
    page.select_option("#ped-input", "Green")
    page.click("#ped-save")
    confirm(page)
    expect(page.locator("#row-rag_rating")).to_contain_text("Green")


def test_product_add_assumption(page: Page, base_url: str):
    open_app(page, base_url)
    _register_product(page, "Product-E2E-005", "Swap")
    _open_product(page, "Product-E2E-005")
    page.click("[data-ptab='assumptions']")
    add_collection_item(page, "assumptions", {"description": "Flat vol surface", "impact": "Low"})
    expect(page.locator("#pt-content")).to_contain_text("Flat vol surface")


def test_product_add_remediation_step(page: Page, base_url: str):
    """Remediation is edited fully in place — no data-ed/data-rm buttons. Drive
    the add form directly rather than the shared helper (which looks for them)."""
    open_app(page, base_url)
    _register_product(page, "Product-E2E-006", "Cap")
    _open_product(page, "Product-E2E-006")
    page.click("[data-ptab='remediation_steps']")
    page.fill("#add-remediation_steps-description", "Re-bootstrap curve")
    page.click("[data-add='remediation_steps']")
    maybe_confirm(page, "add_collection_item")  # collection adds are not gated
    expect(page.locator("#pt-content")).to_contain_text("Re-bootstrap curve")


def test_product_upload_supporting_document(page: Page, base_url: str, tmp_path):
    open_app(page, base_url)
    _register_product(page, "Product-E2E-007", "Floor")
    _open_product(page, "Product-E2E-007")
    page.click("[data-ptab='docs']")
    pdf = tmp_path / "product_spec.pdf"
    pdf.write_bytes(b"%PDF-1.4\n% e2e fixture\n")
    page.set_input_files("#doc-file", str(pdf))
    page.fill("#doc-desc", "Product specification")
    page.click("#doc-upload")
    expect(page.locator("#pt-content")).to_contain_text("product_spec.pdf")


def test_product_monitoring_docs_subtab_upload(page: Page, base_url: str, tmp_path):
    """Monitoring results are timestamped document uploads on the Docs tab's
    Monitoring sub-tab (the old scalar monitoring_results field is gone). The
    uploaded file lists back with an upload timestamp (date + time to the minute),
    so several results landing on one day are still told apart."""
    open_app(page, base_url)
    _register_product(page, "Product-E2E-009", "Autocall")
    _open_product(page, "Product-E2E-009")
    page.click("[data-ptab='docs']")
    page.click("[data-doctab='Monitoring']")
    pdf = tmp_path / "monitoring_q3.pdf"
    pdf.write_bytes(b"%PDF-1.4\n% e2e monitoring fixture\n")
    page.set_input_files("#doc-file", str(pdf))
    page.fill("#doc-desc", "Q3 back-testing results")
    page.click("#doc-upload")
    expect(page.locator("#pt-content")).to_contain_text("monitoring_q3.pdf")
    # The upload carries a timestamp: YYYY-MM-DD HH:MM.
    expect(page.locator("#pt-content")).to_contain_text(
        re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"))


def test_product_retire(page: Page, base_url: str):
    open_app(page, base_url)
    _register_product(page, "Product-E2E-008", "Inflation Swap")
    _open_product(page, "Product-E2E-008")
    page.click("[data-ptab='danger']")          # Retire now lives on the Danger tab
    page.click("#product-retire")
    confirm(page)
    expect(page.locator("tr.clickable[data-id='Product-E2E-008']")).to_contain_text("retired")


def test_events_counter_reflects_recent_event(page: Page, base_url: str):
    """Adding an event bumps the past-year counter on the Risk Rating tab.

    The counter is deliberately product-only: operational failures are a
    production concern and production is where a Product lives, so a model's Risk
    tab does not carry one (``DetailTabs.risk(..., showEvents)``).
    """
    open_app(page, base_url)
    _register_product(page, "Product-E2E-EV-01", "Events Counter Product")
    _open_product(page, "Product-E2E-EV-01")
    page.click("[data-ptab='risk']")
    events_card = page.locator(".scard", has_text="Events (past 365 days)")
    expect(events_card).to_contain_text("0")
    # Add a recent event, then re-open the Risk tab.
    page.click("[data-ptab='operational_failure_events']")
    add_collection_item(
        page, "operational_failure_events",
        {"date": "2026-06-01", "description": "Recent incident"},
    )
    page.click("[data-ptab='risk']")
    expect(events_card).to_contain_text("1")


def test_events_tab_records_a_post_mortem_with_raci(page: Page, base_url: str):
    """W4b: Operational Failure Events captures an incident with the RACI legs.

    Held on the Product: an operational failure happens in production, and it is
    the Product that runs there. A model carries the collection in its data but
    renders no screen for it.
    """
    open_app(page, base_url)
    # Seed a Person so the People-referenced RACI fields render as choices.
    open_admin_subtab(page, "people")
    add_collection_item(page, "people", {"name": "Lena Okafor"})
    _register_product(page, "Product-E2E-EV2", "Swaption")
    _open_product(page, "Product-E2E-EV2")
    page.click("[data-ptab='operational_failure_events']")
    add_collection_item(
        page, "operational_failure_events",
        {"date": "2026-05-12", "description": "Curve flipped sign on illiquid tenor",
         "remediation": "Rolled back to prior dataset; root cause under investigation",
         "responsible": "Lena Okafor",
         "informed_client": "No", "informed_senior_mgmt": "Yes"},
    )
    # An event row is edited in place, so what happened and when it happened are
    # input values rather than cell text — assert the value, not the rendering.
    # The RACI legs are selects, whose chosen option does read as text.
    expect(page.locator("#pt-content input[data-upd$='|description']").first).to_have_value(
        "Curve flipped sign on illiquid tenor")
    expect(page.locator("#pt-content input[data-upd$='|date']").first).to_have_value("2026-05-12")
    expect(page.locator("#pt-content")).to_contain_text("Lena Okafor")
    expect(page.locator("[data-ptab='operational_failure_events']")).to_contain_text("(1)")
