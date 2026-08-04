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
"""Generic, event-sourced document attachments for any aggregate.

A document is metadata in the ``documents`` collection (folded via the shared
collection engine) plus the file bytes on disk. Used by per-model docs and the
governance-wide Documents tab alike.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.database import append_event, read_stream
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.files import save_upload

DOCUMENTS = "documents"

# The top-level Documents area (api_documents) is external-only: governance-wide
# reference material, always uncategorised. Model/product documents carry a
# category and belong on their own aggregate. Enforced in add_document — not left
# to convention — so no caller (UI, seed, or an out-of-repo importer) can dump
# categorised model docs into the external bucket, which is how 93 model documents
# once ended up there.
GOVERNANCE_DOCUMENTS_AGGREGATE = "GovernanceDocuments"


def clean_model_types(model_types) -> list:
    """Normalise a model-types tag list: strings, trimmed, de-duplicated, order-kept.

    Accepts ``None`` (no tags) or any iterable of labels; anything falsy after
    trimming is dropped. The Admin taxonomy is the source of valid labels — this
    only sanitises shape, it does not enforce membership, so renaming a type in
    Admin never rejects an existing document.
    """
    if not model_types:
        return []
    seen, out = set(), []
    for item in model_types:
        label = str(item).strip()
        if label and label not in seen:
            seen.add(label)
            out.append(label)
    return out


def model_scope(model_id: str) -> str:
    """Where a model's uploaded files live under the upload directory. Named here,
    beside the document commands, so the API and the client pack cannot disagree
    about which directory a model's files are in."""
    return f"model/{model_id}"


def client_scope(client_id: str) -> str:
    """Where a client's supplementary uploaded files live under the upload
    directory — named beside ``model_scope`` so the API and the client pack agree."""
    return f"client/{client_id}"


def product_scope(product_id: str) -> str:
    """Where a product's uploaded files live under the upload directory — named
    beside ``model_scope`` so the API and the product pack agree about the path."""
    return f"product/{product_id}"


def _fold(aggregate_type: str, aggregate_id: str, config) -> tuple[list, int]:
    state: dict = {}
    version = 0
    for event in read_stream(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id, config=config
    ):
        folded = coll.fold(state, event.event_type, event.payload)
        if folded is not None:
            state = folded
        version = event.stream_seq
    return list(state.get(DOCUMENTS, ())), version


def list_documents(aggregate_type: str, aggregate_id: str, config=None) -> list:
    """Document metadata recorded against an aggregate."""
    return _fold(aggregate_type, aggregate_id, config)[0]


def find_document(aggregate_type: str, aggregate_id: str, item_id: str, config=None):
    return next(
        (d for d in list_documents(aggregate_type, aggregate_id, config) if d["item_id"] == item_id),
        None,
    )


def add_document(
    *, aggregate_type: str, aggregate_id: str, scope: str, filename: str, data: bytes,
    description: str, actor: str, category: str = "", model_types=None, config=None,
) -> dict:
    """Store the file on disk and record its metadata against the aggregate.

    ``model_types`` tags an external reference document with the Admin-defined
    model types it relates to (a list of labels). It is orthogonal to ``category``
    — the per-model tab a document lives under — which remains forbidden on the
    external Documents area.
    """
    if aggregate_type == GOVERNANCE_DOCUMENTS_AGGREGATE and (category or "").strip():
        raise DomainError(
            "the top-level Documents area is external-only; a categorised document "
            f"({category!r}) belongs on its model or product, not here"
        )
    meta = save_upload(scope, filename, data)
    documents, version = _fold(aggregate_type, aggregate_id, config)
    payload = {
        "collection": DOCUMENTS, "item_id": f"DOC-{len(documents) + 1:03d}",
        "category": category, "filename": meta["filename"],
        "original_name": meta["original_name"], "description": description or "",
        "model_types": clean_model_types(model_types),
        "size": len(data), "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    append_event(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id,
        event_type=coll.EVENT_ITEM_ADDED, payload=payload, actor=actor,
        reason="Upload document", expected_version=version, config=config,
    )
    return payload


def update_document(
    *, aggregate_type: str, aggregate_id: str, item_id: str, fields: dict,
    actor: str, reason: str = "Update document", config=None,
) -> None:
    """Amend a stored document's metadata — its category or description.

    Recategorising is a metadata change, not a re-upload: the file on disk and the
    item id stay put, so every reference to the document survives. Remove-and-add
    would reissue ids and silently break them.
    """
    documents, version = _fold(aggregate_type, aggregate_id, config)
    if not any(d["item_id"] == item_id for d in documents):
        raise DomainError(f"unknown document: {item_id}")
    append_event(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id,
        event_type=coll.EVENT_ITEM_UPDATED,
        payload={"collection": DOCUMENTS, "item_id": item_id, **fields},
        actor=actor, reason=reason, expected_version=version, config=config,
    )


def remove_document(
    *, aggregate_type: str, aggregate_id: str, item_id: str, actor: str, config=None,
) -> None:
    """Record removal of a document (the on-disk file is left in place)."""
    documents, version = _fold(aggregate_type, aggregate_id, config)
    if not any(d["item_id"] == item_id for d in documents):
        raise DomainError(f"unknown document: {item_id}")
    append_event(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id,
        event_type=coll.EVENT_ITEM_REMOVED, payload={"collection": DOCUMENTS, "item_id": item_id},
        actor=actor, reason="Remove document", expected_version=version, config=config,
    )
