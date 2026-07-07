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
"""Documents e2e: governance-wide upload + delete, plus per-model uploads to
each of the four document categories and a per-model delete."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_model, open_tab, register_model

pytestmark = pytest.mark.e2e


def _make_pdf(tmp_path, name: str = "policy.pdf") -> str:
    path = tmp_path / name
    path.write_bytes(b"%PDF-1.4\n% e2e fixture\n")
    return str(path)


def _open_model_docs(page: Page, base_url: str, model_id: str) -> None:
    open_app(page, base_url)
    register_model(page, model_id, "Doc Test Model")
    open_model(page, model_id)
    page.click("[data-dtab='docs']")


def _upload_in_category(page: Page, tmp_path, name: str, category: str, description: str) -> None:
    page.click(f"[data-doctab='{category}']")
    page.set_input_files("#doc-file", _make_pdf(tmp_path, name))
    page.fill("#doc-desc", description)
    page.click("#doc-upload")
    expect(page.locator("#dt-content")).to_contain_text(name)


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


def test_model_doc_upload_core_documentation(page: Page, base_url: str, tmp_path):
    _open_model_docs(page, base_url, "MKM-E2E-DOC1")
    _upload_in_category(page, tmp_path, "spec.pdf", "Core Documentation", "Model spec")


def test_model_doc_upload_test_results(page: Page, base_url: str, tmp_path):
    _open_model_docs(page, base_url, "MKM-E2E-DOC2")
    _upload_in_category(page, tmp_path, "results.pdf", "Test Results", "Backtest results")


def test_model_doc_upload_analysis(page: Page, base_url: str, tmp_path):
    _open_model_docs(page, base_url, "MKM-E2E-DOC3")
    _upload_in_category(page, tmp_path, "analysis.pdf", "Analysis", "Sensitivity analysis")


def test_model_doc_upload_monitoring(page: Page, base_url: str, tmp_path):
    _open_model_docs(page, base_url, "MKM-E2E-DOC4")
    _upload_in_category(page, tmp_path, "monitor.pdf", "Monitoring", "Monthly monitoring report")


def test_model_doc_delete(page: Page, base_url: str, tmp_path):
    _open_model_docs(page, base_url, "MKM-E2E-DOC5")
    _upload_in_category(page, tmp_path, "to_delete.pdf", "Core Documentation", "Will be removed")
    page.locator("[data-rmdoc]").first.click()
    confirm(page)
    expect(page.locator("#dt-content")).not_to_contain_text("to_delete.pdf")


def test_governance_doc_download_link_works(page: Page, base_url: str, tmp_path):
    """The Download link on the governance-wide docs table returns the file."""
    open_app(page, base_url)
    open_tab(page, "documents")
    pdf_path = _make_pdf(tmp_path, "downloadable.pdf")
    page.set_input_files("#gd-file", pdf_path)
    page.fill("#gd-desc", "Downloadable")
    page.click("#gd-upload")
    link = page.locator("#tab-documents tbody tr", has_text="downloadable.pdf").locator("a", has_text="Download")
    href = link.get_attribute("href")
    assert href and href.startswith("/api/documents/")
    response = page.request.get(base_url + href)
    assert response.ok
    assert response.body().startswith(b"%PDF")
