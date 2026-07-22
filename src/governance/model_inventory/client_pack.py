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
"""The client pack: one model's Model Risk Document plus its evidence, as a ZIP.

What a client or an external validator actually needs is the write-up *and* the
documents it refers to -- the model documentation, the sensitivity analysis, the
test results. Sending the document alone means a follow-up asking for the rest.

Only PDFs are packed. The LaTeX sources filed beside them are the same documents in
a form no recipient wants, and the Model Risk Document itself is generated fresh at
the moment the pack is built, so a pack can never carry a stale write-up of the
model it describes. Files are foldered by category, and a CONTENTS listing says
what is inside and what was left out, so the pack explains itself without this app.
"""
from __future__ import annotations

import io
import zipfile

from config.files import HIDDEN_DOC_EXTENSIONS
from src.files import extension, upload_path
from src.governance.documents import model_scope
from src.governance.model_inventory._report_model import items
from src.governance.model_inventory.document import DOC_TITLE, render_model_document_pdf

DOCUMENT_NAME = "{model_id}_model_risk_document.pdf"
PACK_NAME = "{model_id}_model_risk_pack.zip"
CONTENTS_NAME = "CONTENTS.txt"
UNCATEGORISED = "Other"


def _packable(data: dict) -> list[dict]:
    """The attached documents a client pack carries: PDFs only, in a stable order."""
    docs = [d for d in items(data, "documents")
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    return sorted(docs, key=lambda d: (str(d.get("category") or UNCATEGORISED),
                                       str(d.get("original_name") or "")))


def _contents(model: dict, as_of: str, packed: list[str], missing: list[str]) -> str:
    """A plain-text listing of the pack, for whoever opens the ZIP."""
    data = model.get("data", {})
    lines = [
        f"{model['model_id']} --- {data.get('name') or ''}",
        f"{DOC_TITLE} pack, generated {as_of}",
        "",
        "This pack contains:",
    ]
    lines += ["  " + name for name in packed]
    if missing:
        # A file recorded on the model but absent from disk is stated, not skipped:
        # a silently short pack is worse than one that says what is missing.
        lines += ["", "Recorded on the model but not available at the time of packing:"]
        lines += ["  " + name for name in missing]
    return "\n".join(lines) + "\n"


def build_model_pack(model: dict, settings: dict, as_of: str) -> bytes:
    """One model's Model Risk Document plus every PDF attached to it, as ZIP bytes."""
    model_id = model["model_id"]
    document_name = DOCUMENT_NAME.format(model_id=model_id)
    packed, missing = [document_name], []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(document_name,
                         render_model_document_pdf(model, settings, as_of))
        for doc in _packable(model.get("data", {})):
            path = upload_path(model_scope(model_id), doc["filename"])
            name = (str(doc.get("category") or UNCATEGORISED) + "/" +
                    str(doc.get("original_name") or doc["filename"]))
            if not path.exists():
                missing.append(name)
                continue
            archive.writestr(name, path.read_bytes())
            packed.append(name)
        archive.writestr(CONTENTS_NAME, _contents(model, as_of, packed, missing))
    return buffer.getvalue()
