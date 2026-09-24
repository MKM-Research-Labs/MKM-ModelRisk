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
"""Stamping and holding ``model_class``, written once for every governed model record.

A model, an ML Application and an AI System each carry the field (see
``config/governance/_model_class.py``) and each needs the same three things of it: stamp
it from the record type at registration, refuse to have it edited, and read a record
registered before the field existed as its type says. Three copies of that would be three
chances for one aggregate to let a record across the SR 26-2 line.

Pure: no I/O, raises ``DomainError`` on refusal.
"""
from __future__ import annotations

from typing import Any

from config.governance._model_class import MODEL_CLASS_BY_RECORD_TYPE, MODEL_CLASS_FIELD
from src.governance.errors import DomainError


def stamp_model_class(aggregate_type: str, fields: dict[str, Any]) -> dict[str, Any]:
    """``fields`` with the class this record type carries. A caller naming the other class
    is refused rather than overruled: it has misunderstood what it is registering."""
    model_class = MODEL_CLASS_BY_RECORD_TYPE[aggregate_type]
    if fields.get(MODEL_CLASS_FIELD, model_class) != model_class:
        raise DomainError(f"{MODEL_CLASS_FIELD} for this record type is {model_class}")
    return {**fields, MODEL_CLASS_FIELD: model_class}


def reject_immutable_edit(field_specs: dict[str, dict], field: str) -> None:
    """Refuse an edit to a field the spec marks immutable."""
    if (field_specs.get(field) or {}).get("immutable"):
        raise DomainError(f"{field} is set at registration and cannot be edited")


def with_model_class(aggregate_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """A record as read: one registered before the field existed (2026-09-23) carries no
    class in its event, and its type answers the question the same way."""
    data.setdefault(MODEL_CLASS_FIELD, MODEL_CLASS_BY_RECORD_TYPE[aggregate_type])
    return data


__all__ = ["reject_immutable_edit", "stamp_model_class", "with_model_class"]
