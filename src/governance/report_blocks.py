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
"""Shared building blocks for the generated governance documents.

A model, a Product and an ML Application each render a document from their own
record, and the parts that draw those records were three copies of the same code:
a field group as a two-column table, a collection as either a table or one block
per entry, the attached-document list. What actually differs between them is which
spec dict to read, which layout each collection takes, and whether a heading is a
section or a subsection -- so those are parameters and the rest is written once.

Named without a leading underscore because three packages import it; the private
spellings stay in each report module so their own call sites read unchanged.
"""
from __future__ import annotations

from typing import Any

from config.files import HIDDEN_DOC_EXTENSIONS
from src.files import extension
from src.governance.latex import _esc, _para_table, _section, _wrappable
from src.governance.risk_policy.naming import field_label

NOT_RECORDED = "\\textit{Not recorded.}\n\n"


def items(data: dict, name: str) -> list[dict]:
    """A collection's entries, skipping any malformed non-object entry rather than
    failing the whole document over one bad record."""
    return [i for i in data.get(name) or [] if isinstance(i, dict)]


def value(data: dict, key: str) -> str:
    recorded = data.get(key)
    if recorded is None or recorded == "":
        return "Not recorded"
    return str(recorded)


def field_groups(field_specs: dict, skip: set[str]) -> dict[str, list[str]]:
    """The record's field groups, in the order the specs declare them."""
    groups: dict[str, list[str]] = {}
    for key, spec in field_specs.items():
        if key not in skip:
            groups.setdefault(spec.get("group", "Other"), []).append(key)
    return groups


def field_group(data: dict, title: str, keys: list[str], extra: list, *,
                field_specs: dict, heading=_section) -> str:
    """One field group as a two-column table.

    Risk-dimension fields are labelled the way the record's own division names
    them: a document that printed "Complexity" for a division that calls it
    something else would misdescribe the very policy it is reporting against.
    """
    division = data.get("division") or ""
    rows = [[field_label(k, field_specs[k].get("label", k), division), value(data, k)]
            for k in keys] + extra
    return heading(title, _para_table(["Field", "Value"], rows, [0.28, 0.72], caption=title))


def blocks(entries: list[dict], fields: list[dict]) -> str:
    """One labelled block per item, each field on its own line so long rationales
    and evidence citations wrap instead of being squeezed into a table column."""
    out = []
    for index, item in enumerate(entries, start=1):
        lines = ["\\textbf{" + _esc(str(index)) + ".}\\quad "]
        for field in fields:
            recorded = item.get(field["key"])
            if recorded is None or recorded == "":
                continue
            lines.append("\\textbf{" + _esc(field["label"]) + ":} " +
                         _wrappable(recorded) + " \\\\\n")
        out.append("".join(lines).rstrip(" \\\n") + "\n\n")
    return "".join(out)


def collection(data: dict, name: str, label: str | None, *, specs: dict,
               layouts: dict[str, Any], heading=_section,
               entries: list[dict] | None = None) -> str:
    """One collection, as a table or as blocks depending on its declared layout."""
    spec = specs[name]
    fields = spec["fields"]
    entries = items(data, name) if entries is None else entries
    title = label or spec["label"]
    if not entries:
        return heading(title, NOT_RECORDED)
    layout = layouts[name]
    if layout == "blocks":
        return heading(title, blocks(entries, fields))
    rows = [[item.get(f["key"], "") for f in fields] for item in entries]
    return heading(title, _para_table([f["label"] for f in fields], rows, list(layout),
                                      caption=title))


def documents(data: dict, heading=_section) -> str:
    """The evidence pack attached to the record. Filenames are listed so a reviewer
    can tie each dossier back to the document it was drawn from. Sources filed beside
    their PDF (``.tex``) are left out: they are the same document, listed twice."""
    docs = [d for d in items(data, "documents")
            if extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS]
    if not docs:
        return heading("Attached documents", NOT_RECORDED)
    rows = [[d.get("category", ""), d.get("filename", ""), d.get("description", "")]
            for d in docs]
    body = _para_table(["Category", "File", "Description"], rows, [0.22, 0.33, 0.45],
                       caption="Attached documents")
    return heading("Attached documents", body)
