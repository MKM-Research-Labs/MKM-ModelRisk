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
"""What a meeting is about: the records in scope for analysis, written once.

A model, an ML Application, an AI System and a Product are each presented to the
committee the same way — set the scope, join it to the register, table the paper,
record the outcome. So the endpoints are generated from ``MEETING_SCOPE`` rather than
written out per record type.

They were written out per record type, three times, and had drifted before this file
existed: a model's tabled paper was filed onto the model's own Docs tab and a
product's was not, and the two batch-set endpoints lived in different modules. ML
Applications and AI Systems had none of it at all, so a record the firm governs could
never actually be discussed at a meeting.

The paper is filed on the record wherever the record has a document scope — a model,
an ML Application and an AI System all do. A committee reviews what the record has on
file, and a paper that exists only against the meeting is one nobody finds again from
the record it concerns. A Product carries no document scope in this design, so its
paper stays with the meeting exactly as it did before; that is unchanged behaviour,
not a decision taken here.

The routes and their URLs are unchanged for models and products.
"""
from __future__ import annotations

from datetime import date

from flask import jsonify, request, send_file

from config.governance._mrc_collections import MEETING_SCOPE
from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.documents import add_document
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import (
    add_collection_item,
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    remove_collection_item,
    update_collection_item,
)
from src.web._helpers import context_from_request, json_body, request_actor
from src.web.api_mrc._bp import mrc_bp


def _item(meeting: dict, collection: str, id_key: str, record_id: str) -> dict | None:
    return next((i for i in (meeting["data"].get(collection) or [])
                 if i.get(id_key) == record_id), None)


def register_scope_routes(subject) -> None:
    """Attach the in-scope endpoints for one record type to the meetings blueprint."""
    cfg = MEETING_SCOPE[subject.kind]
    collection, id_key = cfg["collection"], cfg["id_key"]
    url, noun, name_field = cfg["url"], cfg["noun"], cfg["name_field"]

    @mrc_bp.post(f"/<meeting_id>/collections/{collection}/set",
                 endpoint=f"set_{collection}")
    def set_scope(meeting_id: str):
        """Replace the in-scope set with the given list.

        Diffed against the current state: new ids are added, missing ids removed. Each
        add and remove is still its own event, so the audit trail records exactly what
        changed rather than "the scope was replaced".
        """
        body = json_body()
        ctx = context_from_request(body)
        desired = {rid for rid in (body.get(f"{id_key}s") or body.get("ids") or []) if rid}
        meeting = get_meeting(meeting_id)
        if meeting is None:
            return jsonify({"error": "meeting not found"}), 404
        current = meeting["data"].get(collection) or []
        current_by_id = {it[id_key]: it["item_id"] for it in current if it.get(id_key)}
        for rid in desired - current_by_id.keys():
            dispatch("add_collection_item", add_collection_item, context=ctx,
                     meeting_id=meeting_id, collection=collection,
                     fields={id_key: rid})
        for rid in current_by_id.keys() - desired:
            dispatch("remove_collection_item", remove_collection_item, context=ctx,
                     meeting_id=meeting_id, collection=collection,
                     item_id=current_by_id[rid])
        rebuild_meeting_view()
        return jsonify(get_meeting(meeting_id))

    @mrc_bp.get(f"/<meeting_id>/{url}", endpoint=f"{collection}_join")
    def in_scope(meeting_id: str):
        """In scope, joined to the register, with derived review status."""
        meeting = get_meeting(meeting_id)
        if meeting is None:
            return jsonify({"error": "meeting not found"}), 404
        today = date.today().isoformat()
        rows = []
        for item in meeting["data"].get(collection) or []:
            record = subject.get(item.get(id_key))
            data = record["data"] if record else {}
            rows.append({
                "item_id": item.get("item_id"),
                id_key: item.get(id_key),
                "name": data.get(name_field),
                "tier": data.get("tier"),
                "rag_rating": data.get("rag_rating"),
                "review_status": compute_review_status(
                    data.get("next_review_date"), today),
                "presenter": item.get("presenter"),
                # The committee's recorded outcome and note. Without these the Analysis
                # panel re-renders the outcome as "Pending" and a blank note, so saved
                # values never appear to stick.
                "analysis_status": item.get("analysis_status"),
                "analysis_note": item.get("analysis_note"),
                "proceed_basis": item.get("proceed_basis"),
                "analysis_filename": item.get("analysis_filename"),
                "analysis_original_name": item.get("analysis_original_name"),
            })
        return jsonify(rows)

    @mrc_bp.post(f"/<meeting_id>/{url}/<record_id>/analysis",
                 endpoint=f"upload_{collection}_analysis")
    def upload_analysis(meeting_id: str, record_id: str):
        """Table the analysis document for an in-scope record at this meeting."""
        meeting = get_meeting_raw(meeting_id)
        if meeting is None:
            return jsonify({"error": "meeting not found"}), 404
        item = _item(meeting, collection, id_key, record_id)
        if item is None:
            return jsonify({"error": f"{noun} is not in scope for this meeting"}), 400
        file = request.files.get("file")
        if file is None:
            return jsonify({"error": "no file provided"}), 400
        data = file.read()
        try:
            meta = save_upload("meeting_analysis", file.filename, data)
        except UploadError as exc:
            return jsonify({"error": str(exc)}), 400
        update_collection_item(
            meeting_id=meeting_id, collection=collection, item_id=item["item_id"],
            fields={"analysis_filename": meta["filename"],
                    "analysis_original_name": meta["original_name"]},
            actor=request_actor(),
        )
        # File it on the record too, under Docs / Analysis, so it lives with the record
        # rather than only with the meeting. The meeting keeps its own reference above.
        scope = subject.doc_scope(record_id)
        if subject.aggregate_type and scope:
            add_document(
                aggregate_type=subject.aggregate_type, aggregate_id=record_id,
                scope=scope, category="Analysis",
                filename=meta["original_name"] or file.filename, data=data,
                description=f"Analysis presented to the MRC at {meeting_id}",
                actor=request_actor(),
            )
            subject.rebuild()
        rebuild_meeting_view()
        return jsonify(get_meeting(meeting_id)), 201

    @mrc_bp.get(f"/<meeting_id>/{url}/<record_id>/analysis",
                endpoint=f"download_{collection}_analysis")
    def download_analysis(meeting_id: str, record_id: str):
        """Download the tabled analysis for this meeting, if one was uploaded."""
        meeting = get_meeting_raw(meeting_id)
        item = _item(meeting, collection, id_key, record_id) if meeting else None
        if item is None or not item.get("analysis_filename"):
            return jsonify({"error": "no analysis uploaded"}), 404
        path = upload_path("meeting_analysis", item["analysis_filename"])
        if not path.exists():
            return jsonify({"error": "analysis file missing"}), 404
        return send_file(str(path), as_attachment=True,
                         download_name=item.get("analysis_original_name") or "analysis")

    @mrc_bp.post(f"/<meeting_id>/{url}/<record_id>/analysis/remove",
                 endpoint=f"remove_{collection}_analysis")
    def remove_analysis(meeting_id: str, record_id: str):
        """Detach the tabled analysis from this meeting. The copy filed on the record
        is left in place — it is the record's own evidence, not the meeting's."""
        meeting = get_meeting_raw(meeting_id)
        if meeting is None:
            return jsonify({"error": "meeting not found"}), 404
        item = _item(meeting, collection, id_key, record_id)
        if item is None:
            return jsonify({"error": f"{noun} is not in scope for this meeting"}), 400
        update_collection_item(
            meeting_id=meeting_id, collection=collection, item_id=item["item_id"],
            fields={"analysis_filename": "", "analysis_original_name": ""},
            actor=request_actor(),
        )
        rebuild_meeting_view()
        return jsonify(get_meeting(meeting_id)), 200


__all__ = ["register_scope_routes"]
