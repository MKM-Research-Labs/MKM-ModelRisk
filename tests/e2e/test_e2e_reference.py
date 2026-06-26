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
"""Admin > reference data e2e: company / division / department / market data
model / calculating agent / people — create, edit, delete each; plus the
company logo upload."""
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


# ---------------------------------------------------------------- Company ----

def test_company_create(page: Page, base_url: str):
    _on(page, base_url, "company")
    item_id = add_collection_item(page, "company", {"value": "Sterling Bank"})
    expect(page.locator(f"[data-ed='company|{item_id}']")).to_be_visible()


def test_company_edit(page: Page, base_url: str):
    _on(page, base_url, "company")
    item_id = add_collection_item(page, "company", {"value": "Sterling Bank"})
    edit_collection_item(page, "company", item_id, {"value": "Sterling Bank PLC"})
    expect(page.locator(f"[data-ed='company|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Sterling Bank PLC")


def test_company_delete(page: Page, base_url: str):
    _on(page, base_url, "company")
    item_id = add_collection_item(page, "company", {"value": "Sterling Bank"})
    remove_collection_item(page, "company", item_id)
    expect(page.locator(f"[data-ed='company|{item_id}']")).to_have_count(0)


# --------------------------------------------------------------- Division ----

def test_division_create(page: Page, base_url: str):
    _on(page, base_url, "company")
    add_collection_item(page, "company", {"value": "Sterling Bank"})
    open_admin_subtab(page, "division")
    # The Company field is now a choice because companies exist.
    item_id = add_collection_item(page, "division", {"value": "Markets", "company": "Sterling Bank"})
    expect(page.locator(f"[data-ed='division|{item_id}']")).to_be_visible()


def test_division_edit(page: Page, base_url: str):
    _on(page, base_url, "company")
    add_collection_item(page, "company", {"value": "Sterling Bank"})
    open_admin_subtab(page, "division")
    item_id = add_collection_item(page, "division", {"value": "Markets", "company": "Sterling Bank"})
    edit_collection_item(page, "division", item_id, {"value": "Global Markets"})
    expect(page.locator(f"[data-ed='division|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Global Markets")


def test_division_delete(page: Page, base_url: str):
    _on(page, base_url, "company")
    add_collection_item(page, "company", {"value": "Sterling Bank"})
    open_admin_subtab(page, "division")
    item_id = add_collection_item(page, "division", {"value": "Markets", "company": "Sterling Bank"})
    remove_collection_item(page, "division", item_id)
    expect(page.locator(f"[data-ed='division|{item_id}']")).to_have_count(0)


# ------------------------------------------------------------- Department ----

def _seed_division(page: Page) -> None:
    """Seed Sterling Bank > Markets so a Department can choose its Division."""
    open_admin_subtab(page, "company")
    add_collection_item(page, "company", {"value": "Sterling Bank"})
    open_admin_subtab(page, "division")
    add_collection_item(page, "division", {"value": "Markets", "company": "Sterling Bank"})


def test_department_create(page: Page, base_url: str):
    open_app(page, base_url)
    _seed_division(page)
    open_admin_subtab(page, "department")
    item_id = add_collection_item(page, "department", {"value": "Rates Trading", "division": "Markets"})
    expect(page.locator(f"[data-ed='department|{item_id}']")).to_be_visible()


def test_department_edit(page: Page, base_url: str):
    open_app(page, base_url)
    _seed_division(page)
    open_admin_subtab(page, "department")
    item_id = add_collection_item(page, "department", {"value": "Rates Trading", "division": "Markets"})
    edit_collection_item(page, "department", item_id, {"value": "Rates & FX Trading"})
    expect(page.locator(f"[data-ed='department|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Rates & FX Trading")


def test_department_delete(page: Page, base_url: str):
    open_app(page, base_url)
    _seed_division(page)
    open_admin_subtab(page, "department")
    item_id = add_collection_item(page, "department", {"value": "Rates Trading", "division": "Markets"})
    remove_collection_item(page, "department", item_id)
    expect(page.locator(f"[data-ed='department|{item_id}']")).to_have_count(0)


# ------------------------------------------------------- Market Data Model ----

def test_market_data_model_create(page: Page, base_url: str):
    _on(page, base_url, "market_data_model")
    item_id = add_collection_item(
        page, "market_data_model",
        {"name": "Bloomberg Curves", "vendor": "Bloomberg", "update_frequency": "Daily"},
    )
    expect(page.locator(f"[data-ed='market_data_model|{item_id}']")).to_be_visible()


def test_market_data_model_edit(page: Page, base_url: str):
    _on(page, base_url, "market_data_model")
    item_id = add_collection_item(
        page, "market_data_model",
        {"name": "Bloomberg Curves", "update_frequency": "Daily"},
    )
    edit_collection_item(page, "market_data_model", item_id, {"name": "Bloomberg IR Curves"})
    expect(page.locator(f"[data-ed='market_data_model|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Bloomberg IR Curves")


def test_market_data_model_delete(page: Page, base_url: str):
    _on(page, base_url, "market_data_model")
    item_id = add_collection_item(
        page, "market_data_model",
        {"name": "Bloomberg Curves", "update_frequency": "Daily"},
    )
    remove_collection_item(page, "market_data_model", item_id)
    expect(page.locator(f"[data-ed='market_data_model|{item_id}']")).to_have_count(0)


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
        {"name": "David Kerr Kelly", "email": "dkk@example.com", "role": "Head of Risk"},
    )
    expect(page.locator(f"[data-ed='people|{item_id}']")).to_be_visible()


def test_people_edit(page: Page, base_url: str):
    _on(page, base_url, "people")
    item_id = add_collection_item(page, "people", {"name": "D. Kelly", "role": "Analyst"})
    edit_collection_item(page, "people", item_id, {"role": "Lead Analyst"})
    expect(page.locator(f"[data-ed='people|{item_id}']").locator("xpath=ancestor::tr")).to_contain_text("Lead Analyst")


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
    page.set_input_files("#logo-file", str(logo))
    page.click("#logo-upload")
    # The page re-renders with a logo <img> in the Company logo section.
    expect(page.locator("img[alt='logo']")).to_be_visible()
