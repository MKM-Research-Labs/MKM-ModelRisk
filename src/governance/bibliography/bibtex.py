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
"""Render bibliography references as BibTeX (pure)."""
from __future__ import annotations

_FIELD_MAP = (("authors", "author"), ("title", "title"), ("year", "year"),
              ("journal", "journal"), ("url", "url"), ("notes", "note"))


def to_bibtex(references: list[dict]) -> str:
    """Render references as a BibTeX document."""
    entries = []
    for ref in references:
        key = (ref.get("item_id") or "ref").replace("-", "")
        lines = [
            f"  {bib} = {{{ref[key_in]}}}"
            for key_in, bib in _FIELD_MAP
            if ref.get(key_in)
        ]
        entries.append("@misc{" + key + ",\n" + ",\n".join(lines) + "\n}")
    return "\n\n".join(entries) + "\n" if entries else ""
