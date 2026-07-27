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
"""
from __future__ import annotations

import io
import zipfile
from typing import Any

from config.files import HIDDEN_DOC_EXTENSIONS
from config.governance import (
    CLIENT_LINKS, CLIENT_PACK_RECENT_MEETINGS, CLOSED_MEETING_STATUS,
)
from src.files import extension, upload_path
from src.governance.client._pack_events import render_event_writeups_pdf
from src.governance.completeness.report import render_completeness_pdf
from src.governance.documents import client_scope, model_scope
from src.governance.model_inventory import get_model
from src.governance.model_inventory.document import render_model_document_pdf
from src.governance.mrc import list_meetings
from src.governance.product import get_product, list_products

PACK_NAME = "{client_id}_client_pack.zip"
CONTENTS_NAME = "CONTENTS.txt"
UNCATEGORISED = "Other"
_MINUTES_SCOPE = "meeting_minutes"
_TOR_SCOPE = "mrc"


def _linked_model_ids(client: dict, config) -> list[str]:
    """Every model the pack must cover: models linked directly, plus every model a
    linked product binds as a component. De-duplicated, in first-seen order."""
    data = client.get("data") or {}
    ids: list[str] = []
    for link in data.get(CLIENT_LINKS) or []:
        subject = link.get("subject_id")
        if not subject:
            continue
        if link.get("link_type") == "Model":
            ids.append(subject)
        elif link.get("link_type") == "Product":
            product = get_product(subject, config=config)
            for comp in ((product or {}).get("data") or {}).get("components") or []:
                if comp.get("model_id"):
                    ids.append(comp["model_id"])
    seen: set[str] = set()
    return [i for i in ids if not (i in seen or seen.add(i))]


def _packable(data: dict) -> list[dict]:
    """A model's attached documents worth packing: PDFs/evidence, LaTeX excluded."""
    docs = [d for d in (data.get("documents") or [])
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    return sorted(docs, key=lambda d: (str(d.get("category") or UNCATEGORISED),
                                       str(d.get("original_name") or "")))


def _recent_minutes(config) -> list[dict]:
    """The most-recent completed meetings that have a saved minutes PDF."""
    meetings = [m for m in list_meetings(config=config)
                if (m.get("data") or {}).get("minutes_filename")
                and (m.get("data") or {}).get("status") == CLOSED_MEETING_STATUS]
    meetings.sort(key=lambda m: str((m.get("data") or {}).get("date") or ""), reverse=True)
    return meetings[:CLIENT_PACK_RECENT_MEETINGS]


def _add_models(archive, client, settings, as_of, config, packed, missing) -> None:
    for model_id in _linked_model_ids(client, config):
        model = get_model(model_id, config=config)
        if model is None:
            missing.append(f"models/{model_id} (not in the inventory)")
            continue
        doc_name = f"models/{model_id}/{model_id}_model_risk_document.pdf"
        archive.writestr(doc_name, render_model_document_pdf(model, settings, as_of))
        packed.append(doc_name)
        for doc in _packable(model.get("data", {})):
            path = upload_path(model_scope(model_id), doc["filename"])
            name = (f"models/{model_id}/" + str(doc.get("category") or UNCATEGORISED) +
                    "/" + str(doc.get("original_name") or doc["filename"]))
            if not path.exists():
                missing.append(name)
                continue
            archive.writestr(name, path.read_bytes())
            packed.append(name)


def _add_minutes(archive, config, packed, missing) -> None:
    for meeting in _recent_minutes(config):
        data = meeting.get("data") or {}
        path = upload_path(_MINUTES_SCOPE, data["minutes_filename"])
        name = "mrc/minutes/" + (data.get("minutes_original_name")
                                 or (meeting["meeting_id"] + "_minutes.pdf"))
        if path.exists():
            archive.writestr(name, path.read_bytes())
            packed.append(name)
        else:
            missing.append(name)


def _supplementary_docs(client: dict) -> list[dict]:
    """User-supplied extra documents attached to the client, PDFs and evidence
    alike (LaTeX sources excluded, as for a model's attachments)."""
    docs = [d for d in (client.get("data") or {}).get("documents") or []
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    return sorted(docs, key=lambda d: str(d.get("original_name") or ""))


def _add_supplementary(archive, client, packed, missing) -> None:
    client_id = client["client_id"]
    for doc in _supplementary_docs(client):
        path = upload_path(client_scope(client_id), doc["filename"])
        name = "supplementary/" + str(doc.get("original_name") or doc["filename"])
        if path.exists():
            archive.writestr(name, path.read_bytes())
            packed.append(name)
        else:
            missing.append(name + " (recorded but file missing)")


def _add_tor(archive, settings, packed, missing) -> None:
    tor = settings.get("tor")
    if not tor or not tor.get("filename"):
        missing.append("governance/MRC Terms of Reference (none uploaded)")
        return
    path = upload_path(_TOR_SCOPE, tor["filename"])
    name = "governance/" + (tor.get("original_name") or tor["filename"])
    if path.exists():
        archive.writestr(name, path.read_bytes())
        packed.append(name)
    else:
        missing.append(name + " (recorded but file missing)")


def _contents(client: dict, as_of: str, generated_at: str,
              packed: list[str], missing: list[str]) -> str:
    data = client.get("data") or {}
    lines = [
        f"{client['client_id']} --- {data.get('name') or ''}",
        "Client pack",
        f"As of (valid time):      {as_of}",
        f"Generated at (txn time): {generated_at}",
        "",
        "This pack contains:",
    ]
    lines += ["  " + name for name in packed]
    if missing:
        lines += ["", "Recorded but not available at the time of packing:"]
        lines += ["  " + name for name in missing]
    return "\n".join(lines) + "\n"


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
        _add_tor(archive, settings, packed, missing)
        gaps_name = "governance/completeness_audit.pdf"
        archive.writestr(gaps_name, render_completeness_pdf(settings, as_of))
        packed.append(gaps_name)
        archive.writestr(CONTENTS_NAME, _contents(client, as_of, generated_at, packed, missing))
    return buffer.getvalue()


def _manifest_models(client: dict, config, warnings: list[str]) -> list[dict]:
    """Preview rows for each model the pack would cover (no PDF compilation)."""
    rows: list[dict] = []
    for model_id in _linked_model_ids(client, config):
        model = get_model(model_id, config=config)
        if model is None:
            warnings.append(f"Linked model {model_id} is not in the inventory — it will be skipped.")
            rows.append({"model_id": model_id, "name": None, "present": False, "attachments": []})
            continue
        data = model.get("data") or {}
        docs = _packable(data)
        for doc in docs:
            if not upload_path(model_scope(model_id), doc["filename"]).exists():
                warnings.append(
                    f"{model_id}: attachment '{doc.get('original_name') or doc['filename']}' "
                    "is recorded but its file is missing.")
        rows.append({"model_id": model_id, "name": data.get("name"), "present": True,
                     "attachments": [str(d.get("original_name") or d["filename"]) for d in docs]})
    return rows


def pack_manifest(client: dict, settings: dict, config=None) -> dict:
    """A cheap preview of what a pack would contain, computed without compiling any
    PDF. Mirrors ``build_client_pack``'s source selection, so the preview matches
    the file a subsequent generate produces, and surfaces the same warnings up front."""
    warnings: list[str] = []
    models = _manifest_models(client, config, warnings)
    supplementary = []
    for doc in _supplementary_docs(client):
        present = upload_path(client_scope(client["client_id"]), doc["filename"]).exists()
        supplementary.append({"name": str(doc.get("original_name") or doc["filename"]),
                              "item_id": doc.get("item_id"), "present": present})
        if not present:
            warnings.append(f"Supplementary document '{doc.get('original_name')}' is recorded "
                            "but its file is missing.")
    minutes = []
    for meeting in _recent_minutes(config):
        data = meeting.get("data") or {}
        present = upload_path(_MINUTES_SCOPE, data["minutes_filename"]).exists()
        minutes.append({"meeting_id": meeting["meeting_id"], "date": data.get("date"),
                        "present": present})
        if not present:
            warnings.append(f"Minutes for {meeting['meeting_id']} are recorded but the file is missing.")
    event_count = sum(len((p.get("data") or {}).get("operational_failure_events") or [])
                      for p in list_products(config=config))
    tor = settings.get("tor")
    if tor and tor.get("filename"):
        tor_info = {"present": upload_path(_TOR_SCOPE, tor["filename"]).exists(),
                    "name": tor.get("original_name") or tor["filename"]}
        if not tor_info["present"]:
            warnings.append("The MRC Terms of Reference is recorded but its file is missing.")
    else:
        tor_info = {"present": False, "name": None}
        warnings.append("No MRC Terms of Reference has been uploaded.")
    return {"models": models, "supplementary": supplementary, "minutes": minutes,
            "event_count": event_count, "tor": tor_info, "includes_gaps_audit": True,
            "warnings": warnings}
