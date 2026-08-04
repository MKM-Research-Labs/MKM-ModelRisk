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
from src.governance.model_handoff.document import render_handover_pdf
from src.governance.model_handoff.projection import get_handoff_for_edge
from src.governance.model_inventory import get_model
from src.governance.model_inventory.document import render_model_document_pdf
from src.governance.mrc import list_meetings
from src.governance.product import get_product, list_products

PACK_NAME = "{client_id}_client_pack.zip"
CONTENTS_NAME = "CONTENTS.txt"
# The human-facing cover page. Named to sort first in the archive listing so it is
# the first thing a reader opens; the machine-readable CONTENTS.txt sits alongside.
COVER_NAME = "00_Cover.pdf"
UNCATEGORISED = "Other"

# Friendly section names for the top-level folder each packed file lives under, used
# on the cover page's "Pack contents" table.
_FOLDER_LABELS = {
    "models": "Model Risk Documents",
    "events": "Operational event write-ups",
    "governance": "Governance",
    "mrc": "MRC minutes and Terms of Reference",
    "supplementary": "Supplementary evidence",
}
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


def _handover_edge(original_name: str) -> tuple[str, str] | None:
    """The provider/consumer models a handover evidence file names, or None if the
    file is not a handover. Handover documents are filed as ``handover_<from>_to_<to>
    .pdf``; model ids carry no underscores, so ``_to_`` is an unambiguous separator."""
    name = original_name or ""
    if not (name.startswith("handover_") and name.endswith(".pdf")):
        return None
    core = name[len("handover_"):-len(".pdf")]
    frm, sep, to = core.partition("_to_")
    return (frm, to) if sep and frm and to else None


def _fresh_handover(original_name: str, as_of: str, config) -> bytes | None:
    """A freshly-compiled handover PDF for a handover evidence file, or None if the
    file is not a handover or its declared edge no longer exists. Rendering at pack
    time means the bundled handover reflects the current template and the current
    field lineage, rather than whatever was uploaded as evidence earlier."""
    edge = _handover_edge(original_name)
    if edge is None:
        return None
    handoff = get_handoff_for_edge(edge[0], edge[1], config=config)
    if handoff is None:
        return None
    return render_handover_pdf(handoff, get_model(edge[0], config=config),
                               get_model(edge[1], config=config), as_of)


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
            name = (f"models/{model_id}/" + str(doc.get("category") or UNCATEGORISED) +
                    "/" + str(doc.get("original_name") or doc["filename"]))
            # Handover documents are re-rendered fresh from their handoff record so
            # the pack carries the current template and lineage, not stale evidence.
            fresh = _fresh_handover(doc.get("original_name", ""), as_of, config)
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


def _cover_rows(paths: list[str]) -> list[list[str]]:
    """One row per packed file: its friendly section and its path within the pack,
    grouped by section so the reader can find each document."""
    return [[_FOLDER_LABELS.get(p.split("/", 1)[0], p.split("/", 1)[0]), p]
            for p in sorted(paths, key=lambda x: (x.split("/", 1)[0], x))]


def _cover_pdf(client: dict, as_of: str, generated_at: str,
               packed: list[str], missing: list[str], settings: dict) -> bytes:
    """A cover-page PDF in the shared house style: title page with the client and the
    bi-temporal stamps, then a numbered "Pack contents" table (and, when relevant, a
    table of items recorded but unavailable). The same information as CONTENTS.txt,
    presented for a human rather than a machine."""
    from src.governance.latex import (_esc, _para_table, _section, front_matter,
                                       logo_asset, preamble)
    from src.governance.mrc.pack import compile_tex
    data = client.get("data") or {}
    org = (settings.get("fields") or {}).get("org_name", "")
    name = data.get("name") or ""
    title = str(client["client_id"]) + (" --- " + name if name else "")
    assets = logo_asset(settings)
    intro = ("Generated on \\textbf{" + _esc(generated_at) + "} for the model risk "
             "position as of \\textbf{" + _esc(as_of) + "}. This pack bundles the "
             "documents listed below; every generated PDF was built at the moment of "
             "packing, so nothing here is a stale copy.\n\n")
    body = _section("Pack contents", intro + _para_table(
        ["Section", "File in pack"], _cover_rows(packed), [0.34, 0.66],
        caption="Pack contents"))
    if missing:
        body += _section("Recorded but not available", (
            "The following items are recorded against the client but their files were "
            "not available when the pack was built.\n\n") + _para_table(
            ["Section", "File in pack"], _cover_rows(missing), [0.34, 0.66],
            caption="Recorded but not available at packing"))
    tex = (preamble("Client Pack", org_name=org) + "\\begin{document}\n"
           + front_matter(title, "Client Pack", org_name=org, date=as_of,
                          logo=bool(assets))
           + body + "\\end{document}\n")
    return compile_tex(tex, assets)


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
        # The text manifest (machine-readable) and the cover page (human-facing) both
        # describe the finished pack, so they are written last, once packed/missing
        # are complete. Neither lists itself.
        archive.writestr(CONTENTS_NAME, _contents(client, as_of, generated_at, packed, missing))
        archive.writestr(COVER_NAME,
                         _cover_pdf(client, as_of, generated_at, packed, missing, settings))
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
            # A handover is regenerated from its handoff record at pack time, so a
            # missing evidence file is not a gap as long as the edge still exists.
            edge = _handover_edge(doc.get("original_name", ""))
            if edge and get_handoff_for_edge(edge[0], edge[1], config=config) is not None:
                continue
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
