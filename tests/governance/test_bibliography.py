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
"""Tests for the bibliography aggregate and BibTeX export."""
from __future__ import annotations

import pytest

from src.database import append_event
from src.governance.bibliography import (
    add_reference,
    get_references,
    remove_reference,
    to_bibtex,
    update_reference,
)
from src.governance.errors import DomainError


def test_load_ignores_unrelated_event():
    append_event(aggregate_type="Bibliography", aggregate_id="global",
                 event_type="Noise", payload={}, actor="system")
    assert get_references() == []


def test_add_and_get():
    add_reference(fields={"authors": "Kelly, D.", "title": "Handbook", "year": "2025"}, actor="admin")
    refs = get_references()
    assert refs[0]["item_id"] == "REF-001"
    assert refs[0]["title"] == "Handbook"


def test_add_requires_title():
    with pytest.raises(DomainError):
        add_reference(fields={"authors": "Kelly, D."}, actor="admin")


def test_update_reference():
    add_reference(fields={"authors": "A", "title": "T"}, actor="admin")
    update_reference(item_id="REF-001", fields={"category": "Governance"}, actor="admin")
    assert get_references()[0]["category"] == "Governance"


def test_remove_reference():
    add_reference(fields={"authors": "A", "title": "T"}, actor="admin")
    remove_reference(item_id="REF-001", actor="admin")
    assert get_references() == []


def test_bibtex_export():
    add_reference(
        fields={"authors": "Kelly, D.", "title": "Handbook", "year": "2025", "url": "http://x"},
        actor="admin",
    )
    bib = to_bibtex(get_references())
    assert "@misc{REF001" in bib
    assert "author = {Kelly, D.}" in bib and "title = {Handbook}" in bib


def test_bibtex_empty():
    assert to_bibtex([]) == ""


def test_notes_are_stored_and_exported_as_bibtex_note():
    add_reference(
        fields={"authors": "Chow, V. T.", "title": "Open-Channel Hydraulics",
                "notes": "Foundation text for Manning's equation."},
        actor="admin",
    )
    refs = get_references()
    assert refs[0]["notes"] == "Foundation text for Manning's equation."
    assert "note = {Foundation text for Manning's equation.}" in to_bibtex(refs)
