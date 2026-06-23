# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
    *, aggregate_type: str, aggregate_id: str, scope: str, category: str,
    filename: str, data: bytes, description: str, actor: str, config=None,
) -> dict:
    """Store the file on disk and record its metadata against the aggregate."""
    meta = save_upload(scope, filename, data)
    documents, version = _fold(aggregate_type, aggregate_id, config)
    payload = {
        "collection": DOCUMENTS, "item_id": f"DOC-{len(documents) + 1:03d}",
        "category": category, "filename": meta["filename"],
        "original_name": meta["original_name"], "description": description or "",
        "size": len(data), "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    append_event(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id,
        event_type=coll.EVENT_ITEM_ADDED, payload=payload, actor=actor,
        reason="Upload document", expected_version=version, config=config,
    )
    return payload


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
