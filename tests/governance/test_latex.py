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

from src.governance import wording
from src.governance.latex import (
    DEFAULT_ORG,
    LOGO_ASSET,
    front_matter,
    history_page,
    logo_asset,
    preamble,
    title_page,
)
from src.governance.mrc_settings import set_field


def test_preamble_carries_org_title_and_confidential_footer():
    tex = preamble("My Report", doc_version="2.0", org_name="Acme")
    assert "Acme" in tex and "My Report --- v2.0" in tex
    assert "CONFIDENTIAL" in tex and "\\pageref{LastPage}" in tex
    assert "mkmblue" in tex


def test_preamble_defaults_the_org():
    assert DEFAULT_ORG in preamble("X")


def test_classification_is_settings_driven():
    # An adopter re-labels every document from Admin > Misc, not by editing code.
    set_field(field="report_classification", value="OFFICIAL-SENSITIVE", actor="a@b.c")
    assert "OFFICIAL-SENSITIVE" in preamble("X")
    assert "OFFICIAL-SENSITIVE" in title_page("T", "s", logo=False)


def test_classification_falls_back_to_the_shipped_default(monkeypatch):
    # Nothing recorded (a fresh install, or the settings unreadable): the document
    # still carries the banner config ships rather than none at all.
    monkeypatch.setattr(wording, "_settings_fields", lambda settings=None: {})
    monkeypatch.setattr(wording, "DEFAULT_CLASSIFICATION", "OFFICIAL-SENSITIVE")
    assert "OFFICIAL-SENSITIVE" in preamble("X")


def test_author_line_is_settings_driven():
    set_field(field="report_author", value="Sterling Bank Model Risk", actor="a@b.c")
    assert "Sterling Bank Model Risk" in front_matter("Doc", "sub", date="2026-07-19")


def test_title_page_with_logo_references_the_cover_asset():
    tex = title_page("T", "sub", logo=True, author="Alice")
    assert LOGO_ASSET in tex and "Alice" in tex and "CONFIDENTIAL" in tex


def test_title_page_without_logo_omits_the_graphic():
    tex = title_page("T", "sub", logo=False)
    assert LOGO_ASSET not in tex


def test_history_page_is_a_numbered_document_history_section():
    hist = history_page("2026-07-19", "Report generated", org_name="Acme", version="2.0")
    # Numbered section (no star), matching the template; placed at the front of a doc.
    assert "\\section{Document Revision History}" in hist
    for cell in ("2026-07-19", "2.0", "Report generated", "Acme"):
        assert cell in hist


def test_front_matter_is_title_page_then_optional_contents():
    plain = front_matter("Doc", "sub", org_name="Acme", date="2026-07-19", author="A")
    assert "titlepage" in plain and "A" in plain
    assert "tableofcontents" not in plain  # no TOC unless asked
    with_toc = front_matter("Doc", "sub", date="2026-07-19", toc=True)
    assert "tableofcontents" in with_toc


def test_front_matter_defaults_the_author():
    from config.reporting import DEFAULT_AUTHOR
    assert DEFAULT_AUTHOR in front_matter("Doc", "sub", date="2026-07-19")


def test_logo_asset_uses_the_uploaded_org_logo():
    import base64

    from src.files import save_upload
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPw9fUFAAHSAOhesXztAAAAAElFTkSuQmCC")
    save_upload("mrc", "brand.png", png)
    assets = logo_asset({"logo": {"filename": "brand.png"}})
    # The uploaded logo is embedded under its real extension; none is bundled.
    assert assets == {"logo.png": png}


def test_logo_asset_is_empty_when_no_logo_uploaded():
    # No uploaded logo -> text-only title page, never a bundled image.
    assert logo_asset({"logo": None}) == {}
    assert logo_asset({}) == {}
