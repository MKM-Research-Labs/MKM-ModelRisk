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
"""Reusable browser flows shared across the e2e tests."""
from __future__ import annotations

from playwright.sync_api import Page, expect


def open_app(page: Page, base_url: str) -> Page:
    """Load the console and wait for the inventory tab to be ready."""
    page.goto(base_url)
    expect(page.locator(".tab[data-tab='inventory']")).to_be_visible()
    return page


def open_tab(page: Page, name: str) -> None:
    page.click(f".tab[data-tab='{name}']")
    expect(page.locator(f"#tab-{name}")).to_be_visible()


def confirm(page: Page) -> None:
    """Accept the confirm-to-amend modal and wait for it to close."""
    expect(page.locator("#confirm-overlay")).to_be_visible()
    page.click("#confirm-ok")
    expect(page.locator("#confirm-overlay")).to_be_hidden()


def register_model(page: Page, model_id: str, name: str) -> None:
    page.click("#m-register")          # open the registration modal
    page.fill("#reg-model_id", model_id)
    page.fill("#reg-name", name)
    page.click("#reg-submit")          # submit -> confirm-to-amend
    confirm(page)
    expect(page.locator(f"tr.clickable[data-id='{model_id}']")).to_be_visible()


def open_model(page: Page, model_id: str) -> None:
    page.click(f"tr.clickable[data-id='{model_id}']")
    expect(page.locator(".dtabs")).to_be_visible()


def open_detail_tab(page: Page, dtab: str) -> None:
    page.click(f"[data-dtab='{dtab}']")


def open_admin_subtab(page: Page, atab: str) -> None:
    """Open the Admin tab and switch to one of its sub-tabs."""
    page.click(".tab[data-tab='reference']")
    page.click(f"[data-atab='{atab}']")
    expect(page.locator(".dtab.active")).to_have_attribute("data-atab", atab)


def add_collection_item(page: Page, list_key: str, fields: dict[str, str]) -> str:
    """Fill the add form for a collection and submit through confirm-to-amend.

    Returns the new item's id (read from the rendered row). Falls back to
    ``data-rm`` for collections without inline edit (e.g. version_history).
    """
    for key, value in fields.items():
        selector = f"#add-{list_key}-{key}"
        if page.locator(selector + " >> nth=0").evaluate("el => el.tagName") == "SELECT":
            page.select_option(selector, value)
        else:
            page.fill(selector, value)
    page.click(f"[data-add='{list_key}']")
    confirm(page)
    marker = page.locator(f"[data-ed^='{list_key}|'], [data-rm^='{list_key}|']").first
    expect(marker).to_be_visible()
    return marker.get_attribute("data-ed" if marker.get_attribute("data-ed") else "data-rm").split("|", 1)[1]


def edit_model_field(page: Page, key: str, value: str, *, choice: bool = False) -> None:
    """Edit one scalar field on a model's overview tab via confirm-to-amend."""
    page.click(f"[data-edit='{key}']")
    if choice:
        page.select_option("#ed-input", value)
    else:
        page.fill("#ed-input", value)
    page.click("#ed-save")
    confirm(page)


def edit_pvm_field(page: Page, key: str, value: str, *, choice: bool = False) -> None:
    """Edit one scalar field on a PVM's overview tab via confirm-to-amend."""
    page.click(f"[data-edit='{key}']")
    if choice:
        page.select_option("#ped-input", value)
    else:
        page.fill("#ped-input", value)
    page.click("#ped-save")
    confirm(page)


def edit_collection_item(page: Page, list_key: str, item_id: str, fields: dict[str, str]) -> None:
    page.click(f"[data-ed='{list_key}|{item_id}']")
    for key, value in fields.items():
        selector = f"#ce-{key}"
        if page.locator(selector).evaluate("el => el.tagName") == "SELECT":
            page.select_option(selector, value)
        else:
            page.fill(selector, value)
    page.click("#ce-save")
    confirm(page)


def remove_collection_item(page: Page, list_key: str, item_id: str) -> None:
    page.click(f"[data-rm='{list_key}|{item_id}']")
    confirm(page)


def set_mrc_setting(page: Page, key: str, value: str) -> None:
    """Edit one MRC settings field on the Admin > MRC sub-tab."""
    page.click(f"[data-sed='{key}']")
    selector = "#set-input"
    if page.locator(selector).evaluate("el => el.tagName") == "SELECT":
        page.select_option(selector, value)
    else:
        page.fill(selector, value)
    page.click("#set-save")
    confirm(page)
