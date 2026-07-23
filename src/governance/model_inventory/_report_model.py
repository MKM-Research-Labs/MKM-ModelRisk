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
"""One model's dossier for the Model Risk Report.

A validation team reviewing a model wants the same material the model detail view
shows, on paper: how the model is classified and why, its methodology, who owns and
reviews it, the validation questions and the evidence answering them, the recorded
assumptions, limitations and weaknesses, what remediation is outstanding, what it
depends on, how it has changed, and what the MRC decided. Every field and every
collection here is read from the same specs the detail view renders, so the dossier
cannot silently fall behind a tab.

Absent material is stated as absent rather than omitted: a validation team needs to
see that (say) no limitations are recorded, which an omitted section would hide.
"""
from __future__ import annotations

from typing import Any

from config.files import HIDDEN_DOC_EXTENSIONS
from config.governance import (COLLECTION_SPECS, MODEL_FIELD_SPECS,
                               TESTING_DOC_CATEGORIES)
from src.files import extension
from src.governance.latex import _esc, _para_table, _section, _subsection, _wrappable

NOT_RECORDED = "\\textit{Not recorded.}\n\n"

# The description opens the dossier as a paragraph, so it is not repeated in the
# classification table underneath it.
SKIP_FIELDS = {"description"}

# The field group the derived review-due status is appended to. It is deliberately
# NOT the stored ``review_status`` field: that tracks how far the validation review
# has got (Not Started -> ... -> Documentation Complete), whereas this says whether
# the next review date has passed. Two different questions, both worth answering.
REVIEW_DATES_GROUP = "Review dates"

# The field group that reports testing. Its three fields are Yes/No flags, which
# read as "no testing exists" when they are unset — even where a test-results pack
# is attached to the model. The evidence is listed beneath them so the section
# answers the question a reviewer is actually asking.
TESTING_GROUP = "Testing"
REVIEW_DUE_LABEL = "Review due (at report date)"

# How each collection is laid out. A tuple gives each column's share of the text
# width; "blocks" renders one labelled block per item, for collections whose fields
# carry too much prose to sit side by side in a readable table.
LAYOUTS: dict[str, Any] = {
    "assumptions": (0.46, 0.10, 0.22, 0.22),
    "limitations": (0.46, 0.10, 0.22, 0.22),
    "model_weaknesses": (0.80, 0.20),
    "validation_questions": "blocks",
    "remediation_steps": (0.42, 0.15, 0.10, 0.13, 0.20),
    "dependencies": (0.15, 0.20, 0.65),
    "version_history": (0.09, 0.12, 0.40, 0.15, 0.14, 0.10),
    "change_history": (0.09, 0.12, 0.15, 0.14, 0.50),
    "signoff_history": "blocks",
}

# The collections making up the dossier, in review order: what the model claims,
# what is wrong with it, what is being done about it, what it rests on, how it has
# changed, and what the committee ruled. The heading overrides the spec label where
# the report needs a fuller name than the tab's.
COLLECTIONS = [
    ("assumptions", None),
    ("validation_questions", "Validation questions and evidence"),
    ("limitations", None),
    ("model_weaknesses", None),
    ("remediation_steps", "Remediation plan"),
    ("dependencies", None),
    ("version_history", "Version history"),
    ("signoff_history", "Model Risk Committee sign-off history"),
]


def history(data: dict) -> list[dict]:
    """The model's release history: every version-history entry, plus any
    change-history entry not already among them, oldest first.

    The two registers record the same thing -- what changed, when, and in which
    version -- and models populate one, the other, or both. Reported as two sections
    they read as a duplicate, and on most models one of the two is empty. Merging
    them gives one history per model without dropping the five models whose only
    record lives in change history. ``change_type`` is not carried across: no model
    has ever set it."""
    entries = list(items(data, "version_history"))
    seen = {(e.get("version"), e.get("date"), e.get("description")) for e in entries}
    for change in items(data, "change_history"):
        key = (change.get("version"), change.get("date"), change.get("description"))
        if key not in seen:
            seen.add(key)
            entries.append(change)
    return sorted(entries, key=lambda e: str(e.get("date") or ""))


def items(data: dict, name: str) -> list[dict]:
    """A collection's entries, ignoring any malformed non-object entry rather than
    failing the whole report over one bad record."""
    return [i for i in data.get(name) or [] if isinstance(i, dict)]


def _value(data: dict, key: str) -> str:
    value = data.get(key)
    if value is None or value == "":
        return "Not recorded"
    return str(value)


def _groups() -> dict[str, list[str]]:
    """The Overview tab's field groups, in the order the detail view shows them."""
    groups: dict[str, list[str]] = {}
    for key, spec in MODEL_FIELD_SPECS.items():
        if key not in SKIP_FIELDS:
            groups.setdefault(spec.get("group", "Other"), []).append(key)
    return groups


def _field_group(data: dict, title: str, keys: list[str], extra: list, heading) -> str:
    rows = [[MODEL_FIELD_SPECS[k].get("label", k), _value(data, k)] for k in keys] + extra
    return heading(title, _para_table(["Field", "Value"], rows, [0.28, 0.72]))


def _blocks(entries: list[dict], fields: list[dict]) -> str:
    """One labelled block per item, each field on its own line so long rationales
    and evidence citations wrap instead of being squeezed into a table column."""
    out = []
    for index, item in enumerate(entries, start=1):
        lines = ["\\textbf{" + _esc(str(index)) + ".}\\quad "]
        for field in fields:
            value = item.get(field["key"])
            if value is None or value == "":
                continue
            lines.append("\\textbf{" + _esc(field["label"]) + ":} " + _wrappable(value) + " \\\\\n")
        out.append("".join(lines).rstrip(" \\\n") + "\n\n")
    return "".join(out)


def _collection(data: dict, name: str, label: str | None, heading,
                entries: list[dict] | None = None) -> str:
    spec = COLLECTION_SPECS[name]
    fields = spec["fields"]
    entries = items(data, name) if entries is None else entries
    title = label or spec["label"]
    if not entries:
        return heading(title, NOT_RECORDED)
    layout = LAYOUTS[name]
    if layout == "blocks":
        return heading(title, _blocks(entries, fields))
    rows = [[item.get(f["key"], "") for f in fields] for item in entries]
    return heading(title, _para_table([f["label"] for f in fields], rows, list(layout)))


def _testing_evidence(data: dict) -> str:
    """The testing documents attached to the model, listed under the Testing
    section. Without this the section shows three unset flags and nothing else, and
    a reviewer concludes no testing was done when the pack is attached."""
    docs = [d for d in items(data, "documents")
            if d.get("category") in TESTING_DOC_CATEGORIES
            and extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    if not docs:
        return "\\textit{No testing evidence is attached to this model.}\n\n"
    rows = [[d.get("category", ""), d.get("original_name", ""), d.get("description", "")]
            for d in docs]
    return ("\\textbf{Testing evidence attached}\\par\\medskip\n" +
            _para_table(["Category", "File", "Description"], rows, [0.22, 0.33, 0.45]))


def _documents(data: dict, heading) -> str:
    """The evidence pack attached to the model. Filenames are listed so a reviewer
    can tie each dossier back to the document it was drawn from. Sources filed beside
    their PDF (``.tex``) are left out: they are the same document, listed twice."""
    docs = [d for d in items(data, "documents")
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    if not docs:
        return heading("Attached documents", NOT_RECORDED)
    rows = [[d.get("category", ""), d.get("filename", ""), d.get("description", "")]
            for d in docs]
    body = _para_table(["Category", "File", "Description"], rows, [0.22, 0.33, 0.45])
    return heading("Attached documents", body)


def model_section(model: dict, review_status: str, *, standalone: bool = False) -> str:
    """A model's complete dossier.

    Inside the Model Risk Report it is one numbered section per model, starting on a
    fresh page. As a standalone client-facing document (``standalone=True``) the
    model is the whole document, so its parts are promoted to top-level sections and
    the wrapping heading — which the title page already carries — is dropped."""
    data = model.get("data", {})
    heading = _section if standalone else _subsection
    parts = []
    if not standalone:
        title = str(model["model_id"]) + " --- " + str(data.get("name") or "")
        parts.append("\\clearpage\n\\section{" + _esc(title) + "}\n")
    # The description opens the document under its own heading: unheaded prose
    # between the contents page and section 1 reads as a stray paragraph, and it
    # never appeared in the table of contents.
    parts.append(heading("Overview", _wrappable(data.get("description") or "")
                         + "\n\n" if data.get("description") else NOT_RECORDED))
    for group, keys in _groups().items():
        extra = [[REVIEW_DUE_LABEL, review_status]] if group == REVIEW_DATES_GROUP else []
        parts.append(_field_group(data, group, keys, extra, heading))
        if group == TESTING_GROUP:
            parts.append(_testing_evidence(data))
    for name, label in COLLECTIONS:
        entries = history(data) if name == "version_history" else None
        parts.append(_collection(data, name, label, heading, entries))
    parts.append(_documents(data, heading))
    return "".join(parts)
