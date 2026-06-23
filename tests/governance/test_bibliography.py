# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
