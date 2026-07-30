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

"""The EF-001 documentation attach (``scripts.attach_ef001_docs``).

EF-001 was the one model the bulk sweep missed, reaching ModelRisk with empty
Docs/Testing tabs. This files its Core Documentation and Sensitivity PDFs into
the per-model store. The properties worth protecting: the documents land in the
right categories, and a re-run is a no-op.
"""
from __future__ import annotations

import pytest

from scripts import attach_ef001_docs, register_ef001
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view


def _register_ef001():
    for model_id, name in (("MKM-GH-001", "GEV Hazard"), ("MKM-PR-001", "PRS Pricing")):
        register_model(model_id=model_id, name=name, actor="test")
    rebuild_inventory_view()
    register_ef001.register()


def _fake_docs(tmp_path):
    """Two minimal PDF files and the spec pointing at them."""
    (tmp_path / "core.pdf").write_bytes(b"%PDF-1.4 core\n%%EOF")
    (tmp_path / "sens.pdf").write_bytes(b"%PDF-1.4 sens\n%%EOF")
    return [
        ("Core Documentation", "event_frequency.pdf", "core.pdf",
         "Event Frequency Model Documentation"),
        ("Sensitivity", "sensitivity_analysis.pdf", "sens.pdf",
         "Sensitivity Analysis - Event Frequency Model"),
    ]


def _docs_by_category(model_id):
    docs = get_model(model_id)["data"]["documents"]
    return {d["original_name"]: d["category"] for d in docs}


def test_it_files_the_docs_in_the_right_categories(tmp_path):
    _register_ef001()
    result = attach_ef001_docs.apply(docs=_fake_docs(tmp_path), phys_root=tmp_path)

    assert len(result["attached"]) == 2
    cats = _docs_by_category("MKM-EF-001")
    assert cats["event_frequency.pdf"] == "Core Documentation"
    assert cats["sensitivity_analysis.pdf"] == "Sensitivity"


def test_it_is_idempotent(tmp_path):
    _register_ef001()
    docs = _fake_docs(tmp_path)
    attach_ef001_docs.apply(docs=docs, phys_root=tmp_path)
    before = len(get_model("MKM-EF-001")["data"]["documents"])

    again = attach_ef001_docs.apply(docs=docs, phys_root=tmp_path)

    assert again["attached"] == []
    assert len(get_model("MKM-EF-001")["data"]["documents"]) == before


def test_it_refuses_when_the_model_is_absent(tmp_path):
    with pytest.raises(RuntimeError, match="not registered"):
        attach_ef001_docs.apply(docs=_fake_docs(tmp_path), phys_root=tmp_path)
