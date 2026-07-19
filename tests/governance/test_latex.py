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
"""The shared LaTeX house style helpers."""
from __future__ import annotations

from pathlib import Path

from src.governance import latex
from src.governance.latex import (
    DEFAULT_ORG,
    LOGO_ASSET,
    front_matter,
    history_page,
    logo_asset,
    preamble,
    title_page,
)


def test_preamble_carries_org_title_and_confidential_footer():
    tex = preamble("My Report", doc_version="2.0", org_name="Acme")
    assert "Acme" in tex and "My Report --- v2.0" in tex
    assert "CONFIDENTIAL" in tex and "\\pageref{LastPage}" in tex
    assert "mkmblue" in tex


def test_preamble_defaults_the_org():
    assert DEFAULT_ORG in preamble("X")


def test_classification_is_config_driven(monkeypatch):
    # An adopter re-labels every document by changing the config value, not code.
    monkeypatch.setattr(latex, "DEFAULT_CLASSIFICATION", "OFFICIAL-SENSITIVE")
    assert "OFFICIAL-SENSITIVE" in preamble("X")
    assert "OFFICIAL-SENSITIVE" in title_page("T", "s", logo=False)


def test_title_page_with_logo_references_the_cover_asset():
    tex = title_page("T", "sub", logo=True, author="Alice")
    assert LOGO_ASSET in tex and "Alice" in tex and "CONFIDENTIAL" in tex


def test_title_page_without_logo_omits_the_graphic():
    tex = title_page("T", "sub", logo=False)
    assert LOGO_ASSET not in tex


def test_history_page_is_the_document_history_table():
    hist = history_page("2026-07-19", "Report generated", org_name="Acme", version="2.0")
    assert "Document History" in hist
    for cell in ("2026-07-19", "2.0", "Report generated", "Acme"):
        assert cell in hist
    assert "\\clearpage" in hist  # content starts on a fresh page


def test_front_matter_is_title_page_then_history():
    fm = front_matter("Doc", "sub", "generated", org_name="Acme", date="2026-07-19", logo=False)
    # Title page comes before the Document History, so every doc opens the same way.
    assert fm.index("titlepage") < fm.index("Document History")
    assert "generated" in fm and "Acme" in fm


def test_logo_asset_reads_the_cover_when_present():
    assert LOGO_ASSET in logo_asset()


def test_logo_asset_is_empty_when_the_cover_is_missing(monkeypatch):
    # A missing logo must degrade to a text-only title page, not raise.
    monkeypatch.setattr("config.paths.LOGO_IMAGE", Path("/no/such/logo.png"))
    assert logo_asset() == {}
