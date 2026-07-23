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
"""The completeness scan over the register, and the PDF it produces."""
from __future__ import annotations

from src.governance.completeness import report as creport
from src.governance.completeness import scan as cscan

AS_OF = "2026-06-22"
SETTINGS = {"fields": {"org_name": "MKM"}}


def test_scan_covers_models_then_products(client_db_models_and_products):
    """Products follow the models so a reader meets the model gaps before the
    product gaps that inherit from them."""
    rows = cscan.scan(AS_OF)
    kinds = [r["entity_kind"] for r in rows]
    assert kinds, "the scan found nothing to audit"
    assert kinds == sorted(kinds, key=lambda k: 0 if k == cscan.MODEL_KIND else 1)


def test_scan_orders_worst_completeness_first(client_db_models_and_products):
    scores = [r["completeness"] for r in cscan.scan(AS_OF)]
    assert scores == sorted(scores), "least complete record should be read first"


def test_a_recorded_document_with_no_file_is_not_counted_as_present(tmp_path, monkeypatch):
    """A document recorded against a model whose file is missing from disk is a
    gap, not evidence: an audit that trusted the metadata would report a pack that
    cannot actually be produced."""
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    check = cscan._retrievable("model/M1")
    assert check({"filename": "absent.pdf"}) is False
    assert check({}) is False, "a record with no filename cannot be retrievable"
    (tmp_path / "model" / "M1").mkdir(parents=True)
    (tmp_path / "model" / "M1" / "there.pdf").write_bytes(b"%PDF-")
    assert check({"filename": "there.pdf"}) is True


def test_product_scope_mirrors_the_model_one():
    assert cscan.product_scope("PRD-X") == "product/PRD-X"


def test_report_renders_over_a_populated_register(client_db_models_and_products):
    tex = creport.build_completeness_tex(cscan.scan(AS_OF), SETTINGS, AS_OF)
    assert "Summary of findings" in tex
    assert "Findings by severity" in tex
    assert "Records by tier" in tex
    assert tex.strip().endswith("\\end{document}")


def test_report_renders_over_an_empty_register():
    """An instance with nothing registered still produces a document that says so,
    rather than failing or emitting an empty page."""
    tex = creport.build_completeness_tex([], SETTINGS, AS_OF)
    assert "Summary of findings" in tex
    assert tex.strip().endswith("\\end{document}")


def test_report_pdf_compiles(client_db_models_and_products, monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    assert creport.render_completeness_pdf(cscan.scan(AS_OF), SETTINGS, AS_OF) == b"%PDF-stub"
