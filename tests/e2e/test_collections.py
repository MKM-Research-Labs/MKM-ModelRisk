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
"""Collections e2e: add a remediation step to a model and see it listed."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_detail_tab, open_model, register_model

pytestmark = pytest.mark.e2e


def test_add_remediation_step(page: Page, base_url: str):
    open_app(page, base_url)
    register_model(page, "MKM-E2E-010", "PRS Pricing")
    open_model(page, "MKM-E2E-010")
    open_detail_tab(page, "remediation_steps")

    page.fill("#add-remediation_steps-description", "Recalibrate severity tail")
    page.click("[data-add='remediation_steps']")
    confirm(page)

    expect(page.locator("#dt-content")).to_contain_text("Recalibrate severity tail")
    # The Remediation tab badge now shows a count of 1.
    expect(page.locator("[data-dtab='remediation_steps']")).to_contain_text("1")
