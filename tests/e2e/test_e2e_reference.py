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
"""Admin > reference data e2e: division / line_of_business / calculating agent /
people — create, edit, delete each; plus the single institution's name and
logo upload. Company is no longer a list (single institution per instance)."""
from __future__ import annotations

import base64

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import (
    add_collection_item,
    edit_collection_item,
    open_admin_subtab,
    open_app,
    remove_collection_item,
)

pytestmark = pytest.mark.e2e


# A 1x1 PNG, used to verify the company logo upload + render round-trip.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPw9fUFAAHSAOhesXztAAAAAElFTkSuQmCC"
)


def _on(page: Page, base_url: str, sub_tab: str) -> None:
    open_app(page, base_url)
    open_admin_subtab(page, sub_tab)


# --------------------------------------------------------------- Division ----

def test_division_create(page: Page, base_url: str):
    _on(page, base_url, "division")
    item_id = add_collection_item(page, "division", {"value": "Markets"})
    expect(page.locator(f"[data-ed='division|{item_id}']")).to_be_visible()


def test_division_edit(page: Page, base_url: str):
    _on(page, base_url, "division")
    item_id = add_collection_item(page, "division", {"value": "Markets"})
    edit_collection_item(page, "division", item_id, {"value": "Global Markets"})
    expect(page.locator(f"[data-ed='division|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Global Markets")


def test_division_delete(page: Page, base_url: str):
    _on(page, base_url, "division")
    item_id = add_collection_item(page, "division", {"value": "Markets"})
    remove_collection_item(page, "division", item_id)
    expect(page.locator(f"[data-ed='division|{item_id}']")).to_have_count(0)


# ------------------------------------------------------------- Line of Business ----

def _seed_division(page: Page) -> None:
    """Seed Markets division so a Line of Business can choose it."""
    open_admin_subtab(page, "division")
    add_collection_item(page, "division", {"value": "Markets"})


def test_line_of_business_create(page: Page, base_url: str):
    open_app(page, base_url)
    _seed_division(page)
    open_admin_subtab(page, "line_of_business")
    item_id = add_collection_item(page, "line_of_business", {"value": "Rates Trading", "division": "Markets"})
    expect(page.locator(f"[data-ed='line_of_business|{item_id}']")).to_be_visible()


def test_line_of_business_edit(page: Page, base_url: str):
    open_app(page, base_url)
    _seed_division(page)
    open_admin_subtab(page, "line_of_business")
    item_id = add_collection_item(page, "line_of_business", {"value": "Rates Trading", "division": "Markets"})
    edit_collection_item(page, "line_of_business", item_id, {"value": "Rates & FX Trading"})
    expect(page.locator(f"[data-ed='line_of_business|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Rates & FX Trading")


def test_line_of_business_delete(page: Page, base_url: str):
    open_app(page, base_url)
    _seed_division(page)
    open_admin_subtab(page, "line_of_business")
    item_id = add_collection_item(page, "line_of_business", {"value": "Rates Trading", "division": "Markets"})
    remove_collection_item(page, "line_of_business", item_id)
    expect(page.locator(f"[data-ed='line_of_business|{item_id}']")).to_have_count(0)


# Market Data Models are no longer a reference list — they live in the Model
# Inventory tagged type="Market Data Model" (see test_e2e_product for the binding).


# -------------------------------------------------------- Calculating Agent ----

def test_calculating_agent_create(page: Page, base_url: str):
    _on(page, base_url, "calculating_agent")
    item_id = add_collection_item(page, "calculating_agent", {"value": "Quartz Pricer"})
    expect(page.locator(f"[data-ed='calculating_agent|{item_id}']")).to_be_visible()


def test_calculating_agent_edit(page: Page, base_url: str):
    _on(page, base_url, "calculating_agent")
    item_id = add_collection_item(page, "calculating_agent", {"value": "Quartz Pricer"})
    edit_collection_item(page, "calculating_agent", item_id, {"value": "Quartz Pricer v2"})
    expect(page.locator(f"[data-ed='calculating_agent|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Quartz Pricer v2")


def test_calculating_agent_delete(page: Page, base_url: str):
    _on(page, base_url, "calculating_agent")
    item_id = add_collection_item(page, "calculating_agent", {"value": "Quartz Pricer"})
    remove_collection_item(page, "calculating_agent", item_id)
    expect(page.locator(f"[data-ed='calculating_agent|{item_id}']")).to_have_count(0)


# ----------------------------------------------------------------- People ----

def test_people_create(page: Page, base_url: str):
    _on(page, base_url, "people")
    item_id = add_collection_item(
        page, "people",
        {"name": "David Kerr Kelly", "email": "dkk@example.com"},
    )
    expect(page.locator(f"[data-ed='people|{item_id}']")).to_be_visible()


def test_people_edit(page: Page, base_url: str):
    _on(page, base_url, "people")
    # Division/Line of Business are free text until the admin lists are populated.
    item_id = add_collection_item(
        page, "people",
        {"name": "D. Kelly", "line_of_business": "Rates Trading"})
    edit_collection_item(page, "people", item_id, {"line_of_business": "Equity Derivatives"})
    expect(page.locator(f"[data-ed='people|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Equity Derivatives")


def test_people_delete(page: Page, base_url: str):
    _on(page, base_url, "people")
    item_id = add_collection_item(page, "people", {"name": "D. Kelly"})
    remove_collection_item(page, "people", item_id)
    expect(page.locator(f"[data-ed='people|{item_id}']")).to_have_count(0)


# ----------------------------------------------------- Company logo upload ----

def test_company_logo_upload(page: Page, base_url: str, tmp_path):
    _on(page, base_url, "company")
    logo = tmp_path / "logo.png"
    logo.write_bytes(PNG_BYTES)
    page.set_input_files("#inst-logo-file", str(logo))
    page.click("#inst-logo-upload")
    # The page re-renders with a logo <img> in the Company logo section (the
    # header logo also renders — scope to the admin body to avoid ambiguity).
    expect(page.locator("#admin-body img[alt='logo']")).to_be_visible()


# MRC committees are managed through a dedicated Admin > MRC panel with its own
# add/edit/remove UI (see src/static/js/mrc_committee.js) rather than the
# generic Collections table used by the other reference lists — they get their
# own e2e coverage in test_e2e_mrc_committee (to be added alongside that JS).
