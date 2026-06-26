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
"""Collections e2e: add items to every structured register on a model
(assumptions, limitations, versions, change history, dependencies, remediation)
plus change a seeded validation question's status."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import (
    add_collection_item,
    confirm,
    open_app,
    open_detail_tab,
    open_model,
    register_model,
)

pytestmark = pytest.mark.e2e


def _setup(page: Page, base_url: str, model_id: str, tab: str) -> None:
    open_app(page, base_url)
    register_model(page, model_id, "Test Model")
    open_model(page, model_id)
    open_detail_tab(page, tab)


def test_add_remediation_step(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-010", "remediation_steps")
    add_collection_item(page, "remediation_steps", {"description": "Recalibrate severity tail"})
    expect(page.locator("#dt-content")).to_contain_text("Recalibrate severity tail")
    expect(page.locator("[data-dtab='remediation_steps']")).to_contain_text("1")


def test_add_assumption(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-011", "assumptions")
    add_collection_item(
        page, "assumptions",
        {"description": "Returns are i.i.d. Gaussian", "impact": "Medium"},
    )
    expect(page.locator("#dt-content")).to_contain_text("Returns are i.i.d. Gaussian")
    expect(page.locator("[data-dtab='assumptions']")).to_contain_text("1")


def test_add_limitation(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-012", "limitations")
    add_collection_item(
        page, "limitations",
        {"description": "Not calibrated to crisis vol", "impact": "High"},
    )
    expect(page.locator("#dt-content")).to_contain_text("Not calibrated to crisis vol")
    expect(page.locator("[data-dtab='limitations']")).to_contain_text("1")


def test_add_version_history(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-013", "version_history")
    add_collection_item(
        page, "version_history",
        {"version": "1.2.0", "date": "2026-05-01", "description": "Recalibration"},
    )
    expect(page.locator("#dt-content")).to_contain_text("1.2.0")
    expect(page.locator("#dt-content")).to_contain_text("Recalibration")


def test_add_change_history(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-014", "change_history")
    add_collection_item(
        page, "change_history",
        {"version": "1.2.0", "date": "2026-05-01", "description": "Methodology refresh"},
    )
    expect(page.locator("#dt-content")).to_contain_text("Methodology refresh")


def test_add_dependency(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-015", "dependencies")
    add_collection_item(
        page, "dependencies",
        {"direction": "upstream", "model_id": "MKM-CR-002", "note": "Consumes PD output"},
    )
    expect(page.locator("#dt-content")).to_contain_text("MKM-CR-002")
    expect(page.locator("#dt-content")).to_contain_text("upstream")


def test_set_validation_question_status(page: Page, base_url: str):
    _setup(page, base_url, "MKM-E2E-016", "validation_questions")
    # The nine SR 26-2 questions are seeded on registration; pick the first
    # row's status <select> and mark it Addressed.
    first = page.locator("select[data-upd^='validation_questions|']").first
    first.select_option("Addressed")
    confirm(page)
    expect(page.locator("#dt-content")).to_contain_text("Addressed")
    # Tab badge reads "n/9" — the n is now 1.
    expect(page.locator("[data-dtab='validation_questions']")).to_contain_text("1/9")
