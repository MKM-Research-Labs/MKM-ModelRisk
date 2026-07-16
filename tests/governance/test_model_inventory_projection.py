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
"""Tests for the model-inventory read-model projection."""
from __future__ import annotations

from src.database import append_event
from src.governance.model_inventory import (
    get_model,
    list_models,
    rebuild_inventory_view,
    register_model,
    retire_model,
    update_model_field,
)


def test_rebuild_reflects_current_state():
    register_model(model_id="M1", name="Alpha", actor="alice", fields={"tier": 3})
    update_model_field(model_id="M1", field="owner", value="bob", actor="alice")
    count = rebuild_inventory_view()
    assert count == 1
    model = get_model("M1")
    assert model["model_id"] == "M1"
    assert model["retired"] is False
    # 1 register + 9 seeded validation questions + 1 field update.
    assert model["version"] == 11
    assert model["data"]["owner"] == "bob"
    assert model["data"]["tier"] == 3
    assert model["data"]["name"] == "Alpha"
    assert len(model["data"]["validation_questions"]) == 9


def test_rebuild_marks_retired_models():
    register_model(model_id="M1", name="Alpha", actor="alice")
    retire_model(model_id="M1", actor="alice")
    rebuild_inventory_view()
    assert get_model("M1")["retired"] is True


def test_list_models_is_ordered():
    register_model(model_id="M2", name="Beta", actor="alice")
    register_model(model_id="M1", name="Alpha", actor="alice")
    rebuild_inventory_view()
    assert [m["model_id"] for m in list_models()] == ["M1", "M2"]


def test_get_model_returns_none_when_absent():
    rebuild_inventory_view()
    assert get_model("missing") is None


def test_rebuild_is_idempotent():
    register_model(model_id="M1", name="Alpha", actor="alice")
    assert rebuild_inventory_view() == 1
    assert rebuild_inventory_view() == 1
    assert len(list_models()) == 1


def test_rebuild_ignores_other_aggregate_types():
    register_model(model_id="M1", name="Alpha", actor="alice")
    # An event from a different aggregate must not leak into this read model.
    append_event(
        aggregate_type="SomethingElse",
        aggregate_id="X",
        event_type="Noted",
        payload={},
        actor="system",
    )
    assert rebuild_inventory_view() == 1
    assert [m["model_id"] for m in list_models()] == ["M1"]
