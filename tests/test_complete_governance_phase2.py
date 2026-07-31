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

"""Phase 2 per-model governance completion (``scripts.complete_governance_phase2``).

Sets each model's validation date and records the seven unassessed validation
questions honestly; VQ-005/008/009 stay Not Addressed and the pass is idempotent.
"""
from __future__ import annotations

import pytest

from scripts import complete_governance_phase2 as phase2
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

MODEL_IDS = tuple(phase2.MODELS)


def _register_all():
    for mid in MODEL_IDS:
        register_model(model_id=mid, name=phase2.MODELS[mid]["name"], actor="test")
    rebuild_inventory_view()


def _data(mid):
    return get_model(mid)["data"]


@pytest.mark.parametrize("mid", MODEL_IDS)
def test_it_sets_validation_date(mid):
    _register_all()
    phase2.apply()
    assert _data(mid)["validation_date"] == phase2.MODELS[mid]["validation_date"]


@pytest.mark.parametrize("mid", MODEL_IDS)
def test_all_validation_questions_recorded_and_honest(mid):
    _register_all()
    phase2.apply()
    by_id = {q["item_id"]: q for q in _data(mid)["validation_questions"]}
    assert all(by_id[f"VQ-00{n}"]["rationale"] for n in range(1, 10))
    assert by_id["VQ-001"]["status"] == "Addressed"
    assert by_id["VQ-002"]["status"] == "Partially Addressed"
    assert by_id["VQ-003"]["status"] == "Addressed"
    for undone in ("VQ-004", "VQ-005", "VQ-008", "VQ-009"):
        assert by_id[undone]["status"] == "Not Addressed"


def test_it_gives_the_expected_4_1_4_shape():
    _register_all()
    phase2.apply()
    for mid in MODEL_IDS:
        statuses = [q["status"] for q in _data(mid)["validation_questions"]]
        assert statuses.count("Addressed") == 4
        assert statuses.count("Partially Addressed") == 1
        assert statuses.count("Not Addressed") == 4


def test_it_is_idempotent():
    _register_all()
    phase2.apply()
    again = phase2.apply()
    assert again == [{"model": mid, "fields": [], "questions": 0} for mid in MODEL_IDS]
