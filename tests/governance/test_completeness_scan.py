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

import pytest

from src.governance.completeness.report import (
    build_completeness_tex, render_completeness_pdf)
from src.governance.completeness.scan import (
    MODEL_KIND, _retrievable, product_scope, scan)
from src.governance.model_inventory import rebuild_inventory_view, register_model
from src.governance.product import rebuild_product_view, register_product

AS_OF = "2026-06-22"
SETTINGS = {"fields": {"org_name": "MKM"}}


@pytest.fixture
def register():
    """One model and one product on the register, so the scan has both kinds to
    audit and the report has rows to lay out."""
    register_model(model_id="M1", name="Alpha", actor="a", fields={"tier": 2})
    register_product(product_id="PRD-1", product="Swap", actor="a",
                     fields={"calculating_agent": "Murex"})
    rebuild_inventory_view()
    rebuild_product_view()


def test_scan_covers_models_then_products(register):
    """Products follow the models so a reader meets the model gaps before the
    product gaps that inherit from them."""
    rows = scan(AS_OF)
    kinds = [r["entity_kind"] for r in rows]
    assert kinds, "the scan found nothing to audit"
    assert kinds == sorted(kinds, key=lambda k: 0 if k == MODEL_KIND else 1)


def test_scan_orders_worst_completeness_first(register):
    scores = [r["completeness"] for r in scan(AS_OF)]
    assert scores == sorted(scores), "least complete record should be read first"


def test_a_recorded_document_with_no_file_is_not_counted_as_present(tmp_path, monkeypatch):
    """A document recorded against a model whose file is missing from disk is a
    gap, not evidence: an audit that trusted the metadata would report a pack that
    cannot actually be produced."""
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    check = _retrievable("model/M1")
    assert check({"filename": "absent.pdf"}) is False
    assert check({}) is False, "a record with no filename cannot be retrievable"
    (tmp_path / "model" / "M1").mkdir(parents=True)
    (tmp_path / "model" / "M1" / "there.pdf").write_bytes(b"%PDF-")
    assert check({"filename": "there.pdf"}) is True


def test_product_scope_mirrors_the_model_one():
    assert product_scope("PRD-X") == "product/PRD-X"


def test_report_renders_over_a_populated_register(register):
    tex = build_completeness_tex(scan(AS_OF), SETTINGS, AS_OF)
    assert "Summary of findings" in tex
    assert "Findings by severity" in tex
    assert "Records by tier" in tex
    assert tex.strip().endswith("\\end{document}")


def test_report_renders_over_an_empty_register():
    """An instance with nothing registered still produces a document that says so,
    rather than failing or emitting an empty page."""
    tex = build_completeness_tex([], SETTINGS, AS_OF)
    assert "Summary of findings" in tex
    assert tex.strip().endswith("\\end{document}")


def test_report_pdf_scans_the_register_itself(register, monkeypatch):
    """Called without rows the report runs the scan; a caller that already has
    them passes them in rather than paying for a second pass."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    assert render_completeness_pdf(SETTINGS, AS_OF) == b"%PDF-stub"
    assert render_completeness_pdf(SETTINGS, AS_OF, rows=scan(AS_OF)) == b"%PDF-stub"
