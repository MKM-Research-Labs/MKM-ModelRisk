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
"""MRC settings e2e: every field on the Admin > MRC sub-tab is editable via
the confirm-to-amend modal and visible after save."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import open_admin_subtab, open_app, set_mrc_setting

pytestmark = pytest.mark.e2e


def _open(page: Page, base_url: str) -> None:
    open_app(page, base_url)
    # The MRC sub-tab now hosts both the committees list and the MRC branding
    # settings (org name / chair / frequency + ToR) in the same card stack.
    open_admin_subtab(page, "mrc")


def test_set_org_name(page: Page, base_url: str):
    _open(page, base_url)
    set_mrc_setting(page, "org_name", "Sterling Bank Group")
    expect(page.locator("#srow-org_name")).to_contain_text("Sterling Bank Group")


def test_set_chair(page: Page, base_url: str):
    _open(page, base_url)
    set_mrc_setting(page, "chair", "Johnny Mattimore")
    expect(page.locator("#srow-chair")).to_contain_text("Johnny Mattimore")


def test_set_frequency_choice(page: Page, base_url: str):
    _open(page, base_url)
    set_mrc_setting(page, "frequency", "Semi-annual")
    expect(page.locator("#srow-frequency")).to_contain_text("Semi-annual")
