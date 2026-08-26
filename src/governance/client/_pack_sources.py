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
"""What a client pack covers: the source selection, shared by both entry points.

``build_client_pack`` writes the archive and ``pack_manifest`` previews it without
compiling a single PDF, and the preview is only honest for as long as the two walk
the SAME sources. That contract used to live in a comment on ``pack_manifest``
("mirrors build_client_pack's source selection"); it lives here now, as the one
module both of them ask.

Nothing in here touches the archive or renders anything. These functions answer
"what would be in the pack", and that is deliberately the whole of their job -- the
moment one of them starts writing a file, the preview can diverge from the pack
again.
"""
from __future__ import annotations

from config.files import HIDDEN_DOC_EXTENSIONS
from config.governance import (
    CLIENT_LINKS, CLIENT_PACK_RECENT_MEETINGS, CLOSED_MEETING_STATUS,
)
from src.files import extension
from src.governance.model_handoff.document import render_handover_pdf
from src.governance.model_handoff.projection import get_handoff_for_edge
from src.governance.model_inventory import get_model
from src.governance.mrc import list_meetings
from src.governance.product import get_product
from src.governance.reference import get_reference_lists

UNCATEGORISED = "Other"
# Where minutes and Terms of Reference files live under the upload directory.
MINUTES_SCOPE = "meeting_minutes"
TOR_SCOPE = "mrc"


def linked_model_ids(client: dict, config) -> list[str]:
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


def packable(data: dict) -> list[dict]:
    """A model's attached documents worth packing: PDFs/evidence, LaTeX excluded."""
    docs = [d for d in (data.get("documents") or [])
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    return sorted(docs, key=lambda d: (str(d.get("category") or UNCATEGORISED),
                                       str(d.get("original_name") or "")))


def handover_edge(original_name: str) -> tuple[str, str] | None:
    """The provider/consumer models a handover evidence file names, or None if the
    file is not a handover. Handover documents are filed as ``handover_<from>_to_<to>
    .pdf``; model ids carry no underscores, so ``_to_`` is an unambiguous separator."""
    name = original_name or ""
    if not (name.startswith("handover_") and name.endswith(".pdf")):
        return None
    core = name[len("handover_"):-len(".pdf")]
    frm, sep, to = core.partition("_to_")
    return (frm, to) if sep and frm and to else None


def fresh_handover(original_name: str, as_of: str, config) -> bytes | None:
    """A freshly-compiled handover PDF for a handover evidence file, or None if the
    file is not a handover or its declared edge no longer exists. Rendering at pack
    time means the bundled handover reflects the current template and the current
    field lineage, rather than whatever was uploaded as evidence earlier."""
    edge = handover_edge(original_name)
    if edge is None:
        return None
    handoff = get_handoff_for_edge(edge[0], edge[1], config=config)
    if handoff is None:
        return None
    return render_handover_pdf(handoff, get_model(edge[0], config=config),
                               get_model(edge[1], config=config), as_of)


def recent_minutes(config) -> list[dict]:
    """The most-recent completed meetings that have a saved minutes PDF."""
    meetings = [m for m in list_meetings(config=config)
                if (m.get("data") or {}).get("minutes_filename")
                and (m.get("data") or {}).get("status") == CLOSED_MEETING_STATUS]
    meetings.sort(key=lambda m: str((m.get("data") or {}).get("date") or ""), reverse=True)
    return meetings[:CLIENT_PACK_RECENT_MEETINGS]


def supplementary_docs(client: dict) -> list[dict]:
    """User-supplied extra documents attached to the client, PDFs and evidence
    alike (LaTeX sources excluded, as for a model's attachments)."""
    docs = [d for d in (client.get("data") or {}).get("documents") or []
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    return sorted(docs, key=lambda d: str(d.get("original_name") or ""))


def committee_tors(config) -> list[dict]:
    """Every MRC committee that has a Terms of Reference on file. The ToR is held per
    committee (reference collection ``mrc``, field ``tor_filename``), not in global
    settings, so this is where a client pack must look for it."""
    return [c for c in (get_reference_lists(config).get("mrc") or []) if c.get("tor_filename")]


def tor_pack_name(committee: dict, labelled: bool) -> str:
    """Where a committee's ToR is filed in the pack. With one committee the original
    filename is enough; with several, label each by its committee so they never
    collide and the reader can tell them apart."""
    original = committee.get("tor_original_name") or committee["tor_filename"]
    if not labelled:
        return "governance/" + original
    who = str(committee.get("name") or committee.get("item_id") or "MRC")
    return "governance/" + who + " --- " + original


__all__ = ["UNCATEGORISED", "MINUTES_SCOPE", "TOR_SCOPE", "linked_model_ids",
           "packable", "handover_edge", "fresh_handover", "recent_minutes",
           "supplementary_docs", "committee_tors", "tor_pack_name"]
