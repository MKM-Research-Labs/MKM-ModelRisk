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

"""The FC-001 documentation filing (scripts.attach_fc001_doc).

The properties worth protecting: v2.2 is filed as Core Documentation, the
earlier filing moves to History, a re-run is a no-op, and a missing model or
source file writes nothing.
"""
from __future__ import annotations

import pytest

from scripts import attach_fc001_doc as attach
from src.governance.documents import add_document
from src.governance.model_inventory import get_model, rebuild_inventory_view, register_model
from src.governance.model_inventory.commands import AGGREGATE_TYPE


def _register():
    register_model(model_id=attach.MODEL_ID, name="Flood Probability Classifier", actor="test")
    rebuild_inventory_view()


def _fake_guide(tmp_path):
    p = tmp_path / attach.SOURCE
    p.parent.mkdir(parents=True)
    p.write_bytes(b"%PDF-1.4 guide\n%%EOF")
    return tmp_path


def _docs():
    return {d["original_name"]: d["category"]
            for d in get_model(attach.MODEL_ID)["data"].get("documents") or []}


def test_it_files_the_document_as_core_documentation(tmp_path):
    _register()
    result = attach.apply(phys_root=_fake_guide(tmp_path))
    assert result["attached"] == [("Core Documentation", attach.STORED_NAME)]
    assert _docs() == {attach.STORED_NAME: "Core Documentation"}


def test_it_retires_the_earlier_filing_to_history(tmp_path):
    _register()
    add_document(aggregate_type=AGGREGATE_TYPE, aggregate_id=attach.MODEL_ID,
                 scope=f"model/{attach.MODEL_ID}", category=attach.CATEGORY,
                 filename=attach.EARLIER_NAME, data=b"%PDF-1.4 old\n%%EOF",
                 description="old", actor="test")
    rebuild_inventory_view()
    attach.apply(phys_root=_fake_guide(tmp_path))
    assert _docs() == {attach.STORED_NAME: "Core Documentation",
                       attach.EARLIER_NAME: "History"}


def test_it_is_idempotent(tmp_path):
    _register()
    root = _fake_guide(tmp_path)
    attach.apply(phys_root=root)
    assert attach.apply(phys_root=root)["attached"] == []


def test_it_refuses_when_the_model_is_absent(tmp_path):
    with pytest.raises(RuntimeError, match="not registered"):
        attach.apply(phys_root=_fake_guide(tmp_path))


def test_a_missing_document_writes_nothing(tmp_path):
    _register()
    with pytest.raises(FileNotFoundError):
        attach.apply(phys_root=tmp_path)
    assert _docs() == {}
