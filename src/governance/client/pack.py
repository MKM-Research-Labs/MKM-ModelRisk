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
"""The client pack: everything a client needs for its linked models, as a ZIP.

A bundle, not a merged PDF, because it carries files of mixed type — freshly
generated Model Risk Documents and the Governance Completeness (gaps) audit, the
attached test/analysis evidence, recent MRC minutes, the operational-event
write-ups, and the MRC Terms of Reference (often a Word document). Generated PDFs
are built at the moment of packing, so a pack never carries a stale write-up. A
CONTENTS listing carries the bi-temporal stamps (as-of + generated-at) and says
what was packed and what was recorded but unavailable, so the pack explains itself.

This module is the ASSEMBLY: which sections go in, in what order, and the two entry
points that build the pack or preview it. What each section draws on lives in
``_pack_sources`` — shared, because a preview that selected its sources differently
from the pack would stop being a preview. How the pack explains itself lives in
``_pack_cover``, and the event write-ups in ``_pack_events``.
"""
from __future__ import annotations

import io
import zipfile

from src.files import upload_path
from src.governance.client._pack_cover import contents_txt, cover_pdf
from src.governance.client._pack_events import render_event_writeups_pdf
from src.governance.client._pack_sources import (
    MINUTES_SCOPE, TOR_SCOPE, UNCATEGORISED, committee_tors, fresh_handover,
    handover_edge, linked_model_ids, packable, recent_minutes, supplementary_docs,
    tor_pack_name,
)
from src.governance.completeness.report import render_completeness_pdf
from src.governance.documents import client_scope, model_scope
from src.governance.model_handoff.projection import get_handoff_for_edge
from src.governance.model_inventory import get_model
from src.governance.model_inventory.document import render_model_document_pdf
from src.governance.product import list_products

PACK_NAME = "{client_id}_client_pack.zip"
CONTENTS_NAME = "CONTENTS.txt"
# The human-facing cover page. Named to sort first in the archive listing so it is
# the first thing a reader opens; the machine-readable CONTENTS.txt sits alongside.
COVER_NAME = "00_Cover.pdf"


def _add_models(archive, client, settings, as_of, config, packed, missing) -> None:
    for model_id in linked_model_ids(client, config):
        model = get_model(model_id, config=config)
        if model is None:
            missing.append(f"models/{model_id} (not in the inventory)")
            continue
        doc_name = f"models/{model_id}/{model_id}_model_risk_document.pdf"
        archive.writestr(doc_name, render_model_document_pdf(model, settings, as_of))
        packed.append(doc_name)
        for doc in packable(model.get("data", {})):
            name = (f"models/{model_id}/" + str(doc.get("category") or UNCATEGORISED) +
                    "/" + str(doc.get("original_name") or doc["filename"]))
            # Handover documents are re-rendered fresh from their handoff record so
            # the pack carries the current template and lineage, not stale evidence.
            fresh = fresh_handover(doc.get("original_name", ""), as_of, config)
            if fresh is not None:
                archive.writestr(name, fresh)
                packed.append(name)
                continue
            path = upload_path(model_scope(model_id), doc["filename"])
            if not path.exists():
                missing.append(name)
                continue
            archive.writestr(name, path.read_bytes())
            packed.append(name)


def _add_minutes(archive, config, packed, missing) -> None:
    for meeting in recent_minutes(config):
        data = meeting.get("data") or {}
        path = upload_path(MINUTES_SCOPE, data["minutes_filename"])
        name = "mrc/minutes/" + (data.get("minutes_original_name")
                                 or (meeting["meeting_id"] + "_minutes.pdf"))
        if path.exists():
            archive.writestr(name, path.read_bytes())
            packed.append(name)
        else:
            missing.append(name)


def _add_supplementary(archive, client, packed, missing) -> None:
    client_id = client["client_id"]
    for doc in supplementary_docs(client):
        path = upload_path(client_scope(client_id), doc["filename"])
        name = "supplementary/" + str(doc.get("original_name") or doc["filename"])
        if path.exists():
            archive.writestr(name, path.read_bytes())
            packed.append(name)
        else:
            missing.append(name + " (recorded but file missing)")


def _add_tor(archive, packed, missing, config) -> None:
    committees = committee_tors(config)
    if not committees:
        missing.append("governance/MRC Terms of Reference (none uploaded)")
        return
    labelled = len(committees) > 1
    for committee in committees:
        name = tor_pack_name(committee, labelled)
        path = upload_path(TOR_SCOPE, committee["tor_filename"])
        if path.exists():
            archive.writestr(name, path.read_bytes())
            packed.append(name)
        else:
            missing.append(name + " (recorded but file missing)")


def build_client_pack(client: dict, settings: dict, as_of: str,
                      generated_at: str, config=None) -> bytes:
    """Assemble a client's full evidence pack as ZIP bytes (see module docstring)."""
    packed: list[str] = []
    missing: list[str] = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        _add_models(archive, client, settings, as_of, config, packed, missing)
        _add_supplementary(archive, client, packed, missing)
        _add_minutes(archive, config, packed, missing)
        events_name = "events/event_writeups.pdf"
        archive.writestr(events_name,
                         render_event_writeups_pdf(list_products(config=config), settings, as_of))
        packed.append(events_name)
        _add_tor(archive, packed, missing, config)
        gaps_name = "governance/completeness_audit.pdf"
        archive.writestr(gaps_name, render_completeness_pdf(settings, as_of))
        packed.append(gaps_name)
        # The text manifest (machine-readable) and the cover page (human-facing) both
        # describe the finished pack, so they are written last, once packed/missing
        # are complete. Neither lists itself.
        archive.writestr(CONTENTS_NAME, contents_txt(client, as_of, generated_at, packed, missing))
        archive.writestr(COVER_NAME,
                         cover_pdf(client, as_of, generated_at, packed, missing, settings))
    return buffer.getvalue()


def _manifest_models(client: dict, config, warnings: list[str]) -> list[dict]:
    """Preview rows for each model the pack would cover (no PDF compilation)."""
    rows: list[dict] = []
    for model_id in linked_model_ids(client, config):
        model = get_model(model_id, config=config)
        if model is None:
            warnings.append(f"Linked model {model_id} is not in the inventory — it will be skipped.")
            rows.append({"model_id": model_id, "name": None, "present": False, "attachments": []})
            continue
        data = model.get("data") or {}
        docs = packable(data)
        for doc in docs:
            # A handover is regenerated from its handoff record at pack time, so a
            # missing evidence file is not a gap as long as the edge still exists.
            edge = handover_edge(doc.get("original_name", ""))
            if edge and get_handoff_for_edge(edge[0], edge[1], config=config) is not None:
                continue
            if not upload_path(model_scope(model_id), doc["filename"]).exists():
                warnings.append(
                    f"{model_id}: attachment '{doc.get('original_name') or doc['filename']}' "
                    "is recorded but its file is missing.")
        rows.append({"model_id": model_id, "name": data.get("name"), "present": True,
                     "attachments": [str(d.get("original_name") or d["filename"]) for d in docs]})
    return rows


def _manifest_tor(config, warnings: list[str]) -> dict:
    """The Terms of Reference row of the preview, and the warnings it raises."""
    tors = committee_tors(config)
    if not tors:
        warnings.append("No MRC Terms of Reference has been uploaded.")
        return {"present": False, "name": None}
    present = [c for c in tors if upload_path(TOR_SCOPE, c["tor_filename"]).exists()]
    names = [c.get("tor_original_name") or c["tor_filename"] for c in tors]
    for committee in tors:
        if not upload_path(TOR_SCOPE, committee["tor_filename"]).exists():
            who = committee.get("name") or committee.get("item_id")
            warnings.append(f"The MRC Terms of Reference for {who} is "
                            "recorded but its file is missing.")
    return {"present": bool(present),
            "name": names[0] if len(names) == 1
            else f"{len(names)} committees' Terms of Reference"}


def pack_manifest(client: dict, settings: dict, config=None) -> dict:
    """A cheap preview of what a pack would contain, computed without compiling any
    PDF. Reads the same ``_pack_sources`` the pack itself does, so the preview matches
    the file a subsequent generate produces, and surfaces the same warnings up front."""
    warnings: list[str] = []
    models = _manifest_models(client, config, warnings)
    supplementary = []
    for doc in supplementary_docs(client):
        present = upload_path(client_scope(client["client_id"]), doc["filename"]).exists()
        supplementary.append({"name": str(doc.get("original_name") or doc["filename"]),
                              "item_id": doc.get("item_id"), "present": present})
        if not present:
            warnings.append(f"Supplementary document '{doc.get('original_name')}' is recorded "
                            "but its file is missing.")
    minutes = []
    for meeting in recent_minutes(config):
        data = meeting.get("data") or {}
        present = upload_path(MINUTES_SCOPE, data["minutes_filename"]).exists()
        minutes.append({"meeting_id": meeting["meeting_id"], "date": data.get("date"),
                        "present": present})
        if not present:
            warnings.append(f"Minutes for {meeting['meeting_id']} are recorded but the file is missing.")
    event_count = sum(len((p.get("data") or {}).get("operational_failure_events") or [])
                      for p in list_products(config=config))
    return {"models": models, "supplementary": supplementary, "minutes": minutes,
            "event_count": event_count, "tor": _manifest_tor(config, warnings),
            "includes_gaps_audit": True, "warnings": warnings}
