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
"""Reusable browser flows shared across the e2e tests."""
from __future__ import annotations

from playwright.sync_api import Page, expect

from config.commands import CONFIRM_REQUIRED_COMMANDS, CONFIRM_REQUIRED_FIELDS


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


def maybe_confirm(page: Page, command: str, field: str | None = None) -> None:
    """Accept the confirm modal only when the policy actually demands one.

    Only the commands/fields named in ``config.commands`` are gated; everything
    else applies immediately with no dialog. Deriving that here — rather than
    assuming every mutation confirms — keeps these flows in lockstep with the
    policy, so a change to it can never silently rot the suite again.
    """
    gated = command in CONFIRM_REQUIRED_COMMANDS or (
        field is not None and field in CONFIRM_REQUIRED_FIELDS.get(command, frozenset())
    )
    if gated:
        confirm(page)


def register_model(page: Page, model_id: str, name: str, model_type: str | None = None) -> None:
    # A model owner is required at registration. Seed a person via the API and
    # refresh the cached reference data so the owner picker (populated on modal
    # open) offers them.
    page.evaluate(
        """async () => {
          await fetch('/api/reference/collections/people', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-Auth-Request-User': 'e2e'},
            body: JSON.stringify({fields: {name: 'E2E Owner'}, confirmed: true}),
          });
          if (typeof MrcNav !== 'undefined') MrcNav.invalidate();
        }"""
    )
    page.click("#m-register")          # open the registration modal
    page.fill("#reg-model_id", model_id)
    page.fill("#reg-name", name)
    if model_type is not None:
        page.select_option("#reg-type", model_type)   # e.g. "Market Data Model"
    page.select_option("#reg-owner", "E2E Owner")     # owner is mandatory
    page.click("#reg-submit")          # submit -> confirm-to-amend
    confirm(page)
    expect(page.locator(f"tr.clickable[data-id='{model_id}']")).to_be_visible()


def open_model(page: Page, model_id: str) -> None:
    page.click(f"tr.clickable[data-id='{model_id}']")
    expect(page.locator("#m-detail .dtabs")).to_be_visible()


def open_detail_tab(page: Page, dtab: str) -> None:
    page.click(f"[data-dtab='{dtab}']")


def open_admin_subtab(page: Page, atab: str) -> None:
    """Open the Admin tab and switch to one of its sub-tabs."""
    page.click(".tab[data-tab='reference']")
    page.click(f"[data-atab='{atab}']")
    # Scope to the admin sub-tabs — the persistent region-nav bar also renders
    # `.dtab.active` buttons, so match only tabs carrying a data-atab.
    expect(page.locator("[data-atab].active")).to_have_attribute("data-atab", atab)


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
    maybe_confirm(page, "add_collection_item")
    marker = page.locator(f"[data-ed^='{list_key}|'], [data-rm^='{list_key}|']").first
    expect(marker).to_be_visible()
    return marker.get_attribute("data-ed" if marker.get_attribute("data-ed") else "data-rm").split("|", 1)[1]


def edit_model_field(page: Page, key: str, value: str, *, choice: bool = False) -> None:
    """Edit one scalar field on a model's overview tab.

    Only the gated fields raise the confirm modal (see ``maybe_confirm``).
    """
    page.click(f"[data-edit='{key}']")
    if choice:
        page.select_option("#ed-input", value)
    else:
        page.fill("#ed-input", value)
    page.click("#ed-save")
    maybe_confirm(page, "update_model_field", key)
    # Wait for the async re-render to settle — the inline editor is gone once the
    # detail has re-fetched and re-rendered. Otherwise a follow-on tab switch can
    # race the re-render and get clobbered back to the overview.
    expect(page.locator("#ed-input")).to_have_count(0)


def edit_product_field(page: Page, key: str, value: str, *, choice: bool = False) -> None:
    """Edit one scalar field on a Product's overview tab.

    Only the gated fields raise the confirm modal (see ``maybe_confirm``).
    """
    page.click(f"[data-edit='{key}']")
    if choice:
        page.select_option("#ped-input", value)
    else:
        page.fill("#ped-input", value)
    page.click("#ped-save")
    maybe_confirm(page, "update_product_field", key)


def edit_collection_item(page: Page, list_key: str, item_id: str, fields: dict[str, str]) -> None:
    page.click(f"[data-ed='{list_key}|{item_id}']")
    for key, value in fields.items():
        selector = f"#ce-{key}"
        if page.locator(selector).evaluate("el => el.tagName") == "SELECT":
            page.select_option(selector, value)
        else:
            page.fill(selector, value)
    page.click("#ce-save")
    maybe_confirm(page, "update_collection_item")


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
