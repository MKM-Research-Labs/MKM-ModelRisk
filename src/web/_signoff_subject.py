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
"""The subject of a sign-off: the per-aggregate adapter.

A model and a product take the same trip through the committee, so the routing is
written once against this small adapter, which captures the per-aggregate
differences — which command to dispatch, which agenda field carries the subject
id, and which decisions the aggregate can actually carry out.
"""
from __future__ import annotations

from typing import Any, Callable

from src.command import CommandContext, dispatch
from src.governance.model_inventory import (
    add_collection_item as _model_add,
    get_model,
    list_models,
    reactivate_model,
    rebuild_inventory_view,
    retire_model,
    update_collection_item as _model_update,
    update_model_field,
)
from src.governance.ml_application import (
    add_collection_item as _ml_add,
    get_ml_application,
    list_ml_applications,
    rebuild_ml_application_view,
    retire_ml_application,
    update_collection_item as _ml_update,
    update_ml_application_field,
)
from src.governance.model_handoff import (
    add_collection_item as _handoff_add,
    get_handoff,
    list_handoffs,
    rebuild_handoff_view,
    update_collection_item as _handoff_update,
    update_handoff_field,
)
from src.governance.product import (
    add_collection_item as _product_add,
    get_product,
    list_products,
    rebuild_product_view,
    retire_product,
    update_collection_item as _product_update,
    update_product_field,
)


class Subject:
    """Per-aggregate adapter so the routing is written once for both kinds."""

    def __init__(self, *, kind: str, agenda_id_field: str, id_key: str,
                 get: Callable, list_all: Callable, add_cmd, update_cmd, field_cmd,
                 rebuild: Callable, id_kwarg: str, retire_cmd=None, reactivate_cmd=None):
        self.kind = kind
        self.agenda_id_field = agenda_id_field   # e.g. "subject_model_id"
        self.id_key = id_key                       # e.g. "model_id" (row key)
        self._get = get
        self._list = list_all
        self._add_cmd = add_cmd
        self._update_cmd = update_cmd
        self._field_cmd = field_cmd
        self._rebuild = rebuild
        self._id_kwarg = id_kwarg                  # e.g. "model_id" (command kwarg)
        self._retire_cmd = retire_cmd
        self._reactivate_cmd = reactivate_cmd

    def get(self, subject_id: str) -> dict | None:
        return self._get(subject_id)

    def list_all(self) -> list[dict]:
        return self._list()

    def rebuild(self) -> None:
        self._rebuild()

    def add_item(self, ctx: CommandContext, subject_id: str, collection: str, fields: dict) -> None:
        dispatch("add_collection_item", self._add_cmd, context=ctx,
                 collection=collection, fields=fields, **{self._id_kwarg: subject_id})

    def update_item(self, ctx: CommandContext, subject_id: str, collection: str,
                    item_id: str, fields: dict) -> None:
        dispatch("update_collection_item", self._update_cmd, context=ctx,
                 collection=collection, item_id=item_id, fields=fields,
                 **{self._id_kwarg: subject_id})

    def set_field(self, ctx: CommandContext, subject_id: str, field: str, value: Any) -> None:
        dispatch("update_field", self._field_cmd, context=ctx,
                 field=field, value=value, **{self._id_kwarg: subject_id})

    def retire(self, ctx: CommandContext, subject_id: str) -> None:
        """Hibernate the subject — the committee ratified a retire request."""
        dispatch(f"retire_{self.kind}", self._retire_cmd, context=ctx,
                 **{self._id_kwarg: subject_id})

    def reactivate(self, ctx: CommandContext, subject_id: str) -> None:
        """Bring the subject back — the committee ratified a reactivate request."""
        dispatch(f"reactivate_{self.kind}", self._reactivate_cmd, context=ctx,
                 **{self._id_kwarg: subject_id})

    def supports(self, signoff_kind: str) -> bool:
        """Whether this subject can carry out the decision the committee took."""
        if signoff_kind == "retire":
            return self._retire_cmd is not None
        if signoff_kind == "reactivate":
            return self._reactivate_cmd is not None
        return True


MODEL_SUBJECT = Subject(
    kind="model", agenda_id_field="subject_model_id", id_key="model_id",
    get=get_model, list_all=list_models, add_cmd=_model_add, update_cmd=_model_update,
    field_cmd=update_model_field, rebuild=rebuild_inventory_view, id_kwarg="model_id",
    retire_cmd=retire_model, reactivate_cmd=reactivate_model,
)
# A product can be retired but not yet brought back — ``supports`` keeps the
# committee from being offered a decision the subject cannot carry out.
PRODUCT_SUBJECT = Subject(
    kind="product", agenda_id_field="subject_product_id", id_key="product_id",
    get=get_product, list_all=list_products, add_cmd=_product_add, update_cmd=_product_update,
    field_cmd=update_product_field, rebuild=rebuild_product_view, id_kwarg="product_id",
    retire_cmd=retire_product,
)
# A handoff goes to the committee to have its compatibility ratified. It is never
# retired/reactivated (those belong to the models it connects), so it carries
# neither command — ``supports`` then keeps the committee from being offered them.
HANDOFF_SUBJECT = Subject(
    kind="handoff", agenda_id_field="subject_handoff_id", id_key="handoff_id",
    get=get_handoff, list_all=list_handoffs, add_cmd=_handoff_add, update_cmd=_handoff_update,
    field_cmd=update_handoff_field, rebuild=rebuild_handoff_view, id_kwarg="handoff_id",
)
# An ML Application takes the same trip through the committee as a model: its rating
# is proposed, and moves only once the committee approves it. Before this it applied
# directly, which meant an ML rating bypassed the committee that signs off every other
# rating in the estate.
#
# Retire is carried; reactivate is not yet, so ``supports`` keeps the committee from
# being offered a decision the subject cannot carry out.
ML_APPLICATION_SUBJECT = Subject(
    kind="ml_application", agenda_id_field="subject_ml_application_id",
    id_key="ml_application_id", get=get_ml_application, list_all=list_ml_applications,
    add_cmd=_ml_add, update_cmd=_ml_update, field_cmd=update_ml_application_field,
    rebuild=rebuild_ml_application_view, id_kwarg="ml_application_id",
    retire_cmd=retire_ml_application,
)
SUBJECTS = (MODEL_SUBJECT, PRODUCT_SUBJECT, HANDOFF_SUBJECT, ML_APPLICATION_SUBJECT)


def subject_for_agenda_item(item: dict) -> tuple[Subject | None, str | None]:
    """Pick the adapter + subject id an agenda sign-off item points at."""
    for subject in SUBJECTS:
        subject_id = item.get(subject.agenda_id_field)
        if subject_id:
            return subject, subject_id
    return None, None
