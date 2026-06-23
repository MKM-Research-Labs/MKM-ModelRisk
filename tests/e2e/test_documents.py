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
"""Documents e2e: upload a governance document, see it listed, then delete it."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_tab

pytestmark = pytest.mark.e2e


def _make_pdf(tmp_path) -> str:
    path = tmp_path / "policy.pdf"
    path.write_bytes(b"%PDF-1.4\n% e2e fixture\n")
    return str(path)


def test_upload_and_delete_document(page: Page, base_url: str, tmp_path):
    open_app(page, base_url)
    open_tab(page, "documents")

    page.set_input_files("#gd-file", _make_pdf(tmp_path))
    page.fill("#gd-desc", "Model risk policy")
    page.click("#gd-upload")

    row = page.locator("#tab-documents tbody tr", has_text="policy.pdf")
    expect(row).to_contain_text("Model risk policy")

    row.locator("[data-rmgd]").click()
    confirm(page)
    expect(page.locator("#tab-documents tbody")).to_contain_text("No documents uploaded yet.")
