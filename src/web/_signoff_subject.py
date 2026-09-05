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

from config.governance._review import (REVIEW_QUESTION_COLLECTIONS,
                                       review_stages_for)
from src.command import CommandContext, dispatch
from src.governance.documents import (ai_system_scope, ml_application_scope,
                                      model_scope)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
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
from src.governance.ml_application.commands import (
    AGGREGATE_TYPE as ML_APPLICATION_AGGREGATE)
from src.governance.ml_application import (
    add_collection_item as _ml_add,
    get_ml_application,
    list_ml_applications,
    reactivate_ml_application,
    rebuild_ml_application_view,
    retire_ml_application,
    update_collection_item as _ml_update,
    update_ml_application_field,
)
from src.governance.ai_system.commands import AGGREGATE_TYPE as AI_SYSTEM_AGGREGATE
from src.governance.ai_system import (
    add_collection_item as _ai_add,
    get_ai_system,
    list_ai_systems,
    reactivate_ai_system,
    rebuild_ai_system_view,
    retire_ai_system,
    update_ai_system_field,
    update_collection_item as _ai_update,
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
    reactivate_product,
    rebuild_product_view,
    retire_product,
    update_collection_item as _product_update,
    update_product_field,
)


class Subject:
    """Per-aggregate adapter so the routing is written once for both kinds."""

    def __init__(self, *, kind: str, agenda_id_field: str, id_key: str,
                 get: Callable, list_all: Callable, add_cmd, update_cmd, field_cmd,
                 rebuild: Callable, id_kwarg: str, retire_cmd=None, reactivate_cmd=None,
                 aggregate_type: str | None = None, doc_scope: Callable | None = None,
                 noun: str | None = None):
        self.kind = kind
        # How the record type reads in a sentence written for a person — a minute the
        # committee signs, an error the owner is shown. ``kind`` is the machine key and
        # passes for the first three by luck; "the ai_system owner" is what happens
        # when a fourth arrives and nobody looks at the minute it writes.
        self.noun = noun or kind
        # Where a generated document is filed against this record. Carried only by the
        # record types a review can be signed off on; a Product or a handoff has no
        # review to file a report from, and None says so rather than pointing at a
        # scope that would never be written to.
        self.aggregate_type = aggregate_type
        self._doc_scope = doc_scope
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

    # The three writes, each in two forms. The ``_as`` form names the command it is
    # running; the plain form is that same call under the generic name. The review
    # workflow needs the named form because "approve_review_stage" and
    # "add_collection_item" are different acts in the audit trail even though both
    # add a row to a collection — and a trail that called an interim approval
    # "add_collection_item" would not be an audit trail of the review.
    def add_item_as(self, command: str, ctx: CommandContext, subject_id: str,
                    collection: str, fields: dict) -> None:
        dispatch(command, self._add_cmd, context=ctx,
                 collection=collection, fields=fields, **{self._id_kwarg: subject_id})

    def update_item_as(self, command: str, ctx: CommandContext, subject_id: str,
                       collection: str, item_id: str, fields: dict) -> None:
        dispatch(command, self._update_cmd, context=ctx,
                 collection=collection, item_id=item_id, fields=fields,
                 **{self._id_kwarg: subject_id})

    def set_field_as(self, command: str, ctx: CommandContext, subject_id: str,
                     field: str, value: Any) -> None:
        dispatch(command, self._field_cmd, context=ctx,
                 field=field, value=value, **{self._id_kwarg: subject_id})

    def add_item(self, ctx: CommandContext, subject_id: str, collection: str, fields: dict) -> None:
        self.add_item_as("add_collection_item", ctx, subject_id, collection, fields)

    def update_item(self, ctx: CommandContext, subject_id: str, collection: str,
                    item_id: str, fields: dict) -> None:
        self.update_item_as("update_collection_item", ctx, subject_id, collection,
                            item_id, fields)

    def set_field(self, ctx: CommandContext, subject_id: str, field: str, value: Any) -> None:
        self.set_field_as("update_field", ctx, subject_id, field, value)

    def doc_scope(self, subject_id: str) -> str | None:
        """The upload scope a document filed against this record belongs in."""
        return self._doc_scope(subject_id) if self._doc_scope else None

    def reviewable(self) -> bool:
        """Whether this record type carries the review workflow.

        The three model-governed record types do; a Product and a handoff are governed
        differently and are not reviewed stage by stage.
        """
        return bool(self.questions_collection() and self.aggregate_type)

    def questions_collection(self) -> str | None:
        """Where this record type keeps the questionnaire its review works through."""
        return REVIEW_QUESTION_COLLECTIONS.get(self.kind)

    def review_stages(self) -> tuple[dict, ...]:
        """The review stages as this record type words them."""
        return review_stages_for(self.kind)

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
    aggregate_type=MODEL_AGGREGATE, doc_scope=model_scope,
)
# Retire and reactivate travel the same route, as they do for every other subject:
# retiring is hibernation, so the committee that ratified it is the one that can
# undo it. A Product was the last of the five to be brought onto that route.
PRODUCT_SUBJECT = Subject(
    kind="product", agenda_id_field="subject_product_id", id_key="product_id",
    get=get_product, list_all=list_products, add_cmd=_product_add, update_cmd=_product_update,
    field_cmd=update_product_field, rebuild=rebuild_product_view, id_kwarg="product_id",
    retire_cmd=retire_product, reactivate_cmd=reactivate_product, noun="Product",
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
# Retire and reactivate travel the same route: retiring is hibernation, so the
# committee that ratified it is the one that can undo it.
ML_APPLICATION_SUBJECT = Subject(
    kind="ml_application", agenda_id_field="subject_ml_application_id",
    id_key="ml_application_id", get=get_ml_application, list_all=list_ml_applications,
    add_cmd=_ml_add, update_cmd=_ml_update, field_cmd=update_ml_application_field,
    rebuild=rebuild_ml_application_view, id_kwarg="ml_application_id",
    retire_cmd=retire_ml_application, reactivate_cmd=reactivate_ml_application,
    noun="ML Application",
    aggregate_type=ML_APPLICATION_AGGREGATE, doc_scope=ml_application_scope,
)
# An AI System takes the same trip as a model and an ML Application: the owner
# proposes a rating and the stored one does not move until the committee approves it.
# It would have been easy to let this record type set its own rating -- it is new and
# nothing downstream depends on it yet -- and that is exactly the argument that left
# ML ratings bypassing the committee until somebody noticed. Same route from the start.
AI_SYSTEM_SUBJECT = Subject(
    kind="ai_system", agenda_id_field="subject_ai_system_id",
    id_key="ai_system_id", get=get_ai_system, list_all=list_ai_systems,
    add_cmd=_ai_add, update_cmd=_ai_update, field_cmd=update_ai_system_field,
    rebuild=rebuild_ai_system_view, id_kwarg="ai_system_id",
    retire_cmd=retire_ai_system, reactivate_cmd=reactivate_ai_system,
    noun="AI System",
    aggregate_type=AI_SYSTEM_AGGREGATE, doc_scope=ai_system_scope,
)
SUBJECTS = (MODEL_SUBJECT, PRODUCT_SUBJECT, HANDOFF_SUBJECT, ML_APPLICATION_SUBJECT,
            AI_SYSTEM_SUBJECT)


def subject_by_kind(kind: str) -> Subject | None:
    """The adapter for a record type, or ``None`` if that is not a record type.

    One lookup rather than a dict built beside ``SUBJECTS``, which would be a second
    list to keep in step with the first. Callers that need to know a record exists —
    the change register, and the routing resolver after it — go through here rather
    than importing five ``get_*`` functions and choosing between them.
    """
    return next((subject for subject in SUBJECTS if subject.kind == kind), None)


def subject_for_agenda_item(item: dict) -> tuple[Subject | None, str | None]:
    """Pick the adapter + subject id an agenda sign-off item points at."""
    for subject in SUBJECTS:
        subject_id = item.get(subject.agenda_id_field)
        if subject_id:
            return subject, subject_id
    return None, None
