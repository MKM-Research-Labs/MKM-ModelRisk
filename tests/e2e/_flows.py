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
