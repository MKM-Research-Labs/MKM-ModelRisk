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

"""The sensitivity-document filing (``scripts.attach_sensitivity_docs``).

Files each model's Sensitivity PDF into the matching per-model Sensitivity tab and
is idempotent on re-run.
"""
from __future__ import annotations

from scripts import attach_sensitivity_docs as attach
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

MODEL_IDS = ("MKM-PF-001", "MKM-ST-001", "MKM-TC-001")


def _register_all():
    for mid in MODEL_IDS:
        register_model(model_id=mid, name=f"Model {mid}", actor="test")
    rebuild_inventory_view()


def _fake_root(tmp_path):
    for _mid, (relpath, _desc) in attach.DOCS.items():
        p = tmp_path / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4 sensitivity\n%%EOF")
    return tmp_path


def _docs(mid):
    return get_model(mid)["data"].get("documents") or []


def test_it_files_a_sensitivity_doc_on_each_model(tmp_path):
    _register_all()
    result = attach.apply(phys_root=_fake_root(tmp_path))
    assert len(result["attached"]) == len(MODEL_IDS)
    for mid in MODEL_IDS:
        cats = {d["category"] for d in _docs(mid)}
        assert "Sensitivity" in cats


def test_it_is_idempotent(tmp_path):
    root = _fake_root(tmp_path)
    _register_all()
    attach.apply(phys_root=root)
    again = attach.apply(phys_root=root)
    assert again == {"attached": []}
