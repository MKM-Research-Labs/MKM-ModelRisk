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
"""Collections e2e: add items to every structured register on a model
(assumptions, limitations, versions, change history, dependencies, remediation)
plus change a seeded validation question's status."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import (
    add_collection_item,
    confirm,
    edit_collection_item,
    maybe_confirm,
    open_app,
    open_detail_tab,
    open_review_stage,
    open_model,
    register_model,
    remove_collection_item,
)

pytestmark = pytest.mark.e2e


def _setup(page: Page, base_url: str, model_id: str, tab: str) -> None:
    open_app(page, base_url)
    register_model(page, model_id, "Test Model")
    open_model(page, model_id)
    open_detail_tab(page, tab)


def test_add_remediation_step(page: Page, base_url: str):
    """Remediation is edited fully in place (every field is an inline control),
    so it doesn't render row-level edit/remove buttons — drive it through the
    add form + description assertion rather than the shared helper."""
    _setup(page, base_url, "MKM-E2E-010", "review")
    open_review_stage(page, "remediation")
    page.fill("#add-remediation_steps-description", "Recalibrate severity tail")
    page.click("[data-add='remediation_steps']")
    maybe_confirm(page, "add_collection_item")
    expect(page.locator("#dt-content")).to_contain_text("Recalibrate severity tail")


def test_add_assumption(page: Page, base_url: str):
    # Assumptions are stage 1 of the review, not a tab of their own.
    _setup(page, base_url, "MKM-E2E-011", "review")
    open_review_stage(page, "assumptions")
    add_collection_item(
        page, "assumptions",
        {"description": "Returns are i.i.d. Gaussian", "impact": "Medium"},
    )
    expect(page.locator("#dt-content")).to_contain_text("Returns are i.i.d. Gaussian")


def test_add_limitation(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-012", "review")
    open_review_stage(page, "limitations")
    add_collection_item(
        page, "limitations",
        {"description": "Not calibrated to crisis vol", "impact": "High"},
    )
    expect(page.locator("#dt-content")).to_contain_text("Not calibrated to crisis vol")


def test_add_version_history(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-013", "version_history")
    add_collection_item(
        page, "version_history",
        {"version": "1.2.0", "date": "2026-05-01", "description": "Recalibration"},
    )
    expect(page.locator("#dt-content")).to_contain_text("1.2.0")
    expect(page.locator("#dt-content")).to_contain_text("Recalibration")


def test_add_version_with_lifecycle_shows_badge(page: Page, base_url: str):
    """A version's lifecycle renders as a coloured badge on the timeline (W4d)."""
    _setup(page, base_url, "MKM-E2E-013L", "version_history")
    add_collection_item(
        page, "version_history",
        {"version": "2.0.0", "date": "2026-06-01",
         "description": "Major refresh", "lifecycle": "Being Enhanced"},
    )
    item = page.locator(".vitem", has_text="2.0.0")
    expect(item).to_contain_text("Being Enhanced")


# test_events_tab_records_a_post_mortem_with_raci moved to test_e2e_product.
# A model still carries the operational_failure_events collection, but nothing on
# a model's screen renders it: a failure in production is the Product's event, and
# that is where the register is shown. The test follows the screen.


def test_add_change_history(page: Page, base_url: str):
    # Change history now lives under the merged "Versions" tab.
    _setup(page, base_url, "MKM-E2E-014", "version_history")
    add_collection_item(
        page, "change_history",
        {"version": "1.2.0", "date": "2026-05-01", "description": "Methodology refresh"},
    )
    expect(page.locator("#dt-content")).to_contain_text("Methodology refresh")


def test_set_validation_question_status_and_rationale(page: Page, base_url: str):
    """Set status + rationale on the first SR 26-2 question; both commit in one save.

    There is no save button: every change to a question posts as it is made, and
    the handler sends the status and the rationale together whichever of the two
    was touched. So each edit is its own save, and each re-renders the tab —
    hence re-resolving the second control rather than holding a stale handle.
    """
    _setup(page, base_url, "MKM-E2E-016", "review")
    open_review_stage(page, "questions")
    item_id = page.locator("[data-vq-item]").first.get_attribute("data-vq-item")
    page.select_option(f"#vq-{item_id}-status", "Addressed")
    page.fill(f"#vq-{item_id}-rationale", "Owner walked through the assumptions in detail.")
    page.locator(f"#vq-{item_id}-rationale").blur()
    # After re-render, the rationale persists in the input's value attribute.
    expect(page.locator(f"#vq-{item_id}-rationale")).to_have_value(
        "Owner walked through the assumptions in detail."
    )
    expect(page.locator(f"#vq-{item_id}-status")).to_have_value("Addressed")
    # The Review tab's count is the owner's coverage across the nine questions.
    expect(page.locator("[data-dtab='review']")).to_contain_text("1/9")


# --- X1 coverage: edit and remove operations on model collections -----------

def test_edit_limitation_updates_row(page: Page, base_url: str):
    _setup(page, base_url, "MKM-X1-EDIT1", "review")
    open_review_stage(page, "limitations")
    item_id = add_collection_item(
        page, "limitations",
        {"description": "Original wording", "impact": "Medium"},
    )
    edit_collection_item(page, "limitations", item_id,
                         {"description": "Refined after review", "impact": "High"})
    body = page.locator("#dt-content")
    expect(body).to_contain_text("Refined after review")
    expect(body).to_contain_text("High")


# test_remove_remediation_step_shrinks_list — retired.
# Remediation is edited fully in place (owner/priority/status inline selects,
# due-date inline date input); there is no row-level Remove button. Closing
# a step happens via the inline Status → "Closed" choice instead.


def test_close_remediation_step_via_inline_status(page: Page, base_url: str):
    """Closing an item flips its inline Status control to "Closed" — the row
    stays in the list (audit trail) but its state changes."""
    _setup(page, base_url, "MKM-X1-RM1", "review")
    open_review_stage(page, "remediation")
    page.fill("#add-remediation_steps-description", "Transient item")
    page.click("[data-add='remediation_steps']")
    maybe_confirm(page, "add_collection_item")
    # Every remediation field is an inline data-upd control; use the Status one.
    page.locator("select[data-upd^='remediation_steps|'][data-upd$='|status']").select_option("Closed")
    maybe_confirm(page, "update_collection_item")
    expect(page.locator("select[data-upd$='|status']").first).to_have_value("Closed")


def test_remove_version_history_entry(page: Page, base_url: str):
    """Versions use the timeline renderer (data-rm only, no data-ed)."""
    _setup(page, base_url, "MKM-X1-RM2", "version_history")
    item_id = add_collection_item(
        page, "version_history",
        {"version": "0.9.0", "description": "Beta rev", "lifecycle": "Marked for Removal"},
    )
    remove_collection_item(page, "version_history", item_id)
    expect(page.locator("#dt-content")).not_to_contain_text("Beta rev")
