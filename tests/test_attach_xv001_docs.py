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

"""The XV-001 documentation attach (scripts.attach_xv001_docs).

Files the PRS XVA model document under Core Documentation, Test Results and
Sensitivity. The properties worth protecting: the categories are right and a
re-run is a no-op.
"""
from __future__ import annotations

import pytest

from scripts import attach_xv001_docs, register_xv001


def _register():
    register_xv001.register()


def _fake_docs(tmp_path):
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4 xva\n%%EOF")
    return [(c, name, "doc.pdf", d) for c, name, _, d in attach_xv001_docs.DOCS]


def _docs_by_category():
    from src.governance.model_inventory import get_model
    return {d["original_name"]: d["category"]
            for d in get_model("MKM-XV-001")["data"]["documents"]}


def test_it_files_the_document_in_each_category(tmp_path):
    _register()
    result = attach_xv001_docs.apply(docs=_fake_docs(tmp_path), phys_root=tmp_path)
    assert len(result["attached"]) == 3
    cats = _docs_by_category()
    assert cats["prs_xva.pdf"] == "Core Documentation"
    assert cats["test_results.pdf"] == "Test Results"
    assert cats["sensitivity_analysis.pdf"] == "Sensitivity"


def test_it_is_idempotent(tmp_path):
    _register()
    docs = _fake_docs(tmp_path)
    attach_xv001_docs.apply(docs=docs, phys_root=tmp_path)
    assert attach_xv001_docs.apply(docs=docs, phys_root=tmp_path)["attached"] == []


def test_it_refuses_when_the_model_is_absent(tmp_path):
    with pytest.raises(RuntimeError, match="not registered"):
        attach_xv001_docs.apply(docs=_fake_docs(tmp_path), phys_root=tmp_path)


def test_the_real_spec_points_at_the_generated_model_document():
    assert {rel for _, _, rel, _ in attach_xv001_docs.DOCS} == {
        "docs/models/prs_xva/MKM-XV-001_model_document.pdf"}
