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
"""Tests for the Meeting Pack LaTeX generation and PDF compilation."""
from __future__ import annotations

import base64

from src.files import save_upload
from src.governance.mrc.pack import build_tex, compile_tex, render_pack_pdf

# A 1x1 PNG so tectonic has a real image to embed.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPw9fUFAAHSAOhesXztAAAAAElFTkSuQmCC"
)

MEETING = {
    "meeting_id": "MTG1",
    "data": {
        "title": "Q2 MRC", "date": "2026-02-16", "chair": "Johnny Mattimore",
        "participants": [{"name": "JM", "role": "Chair", "organisation": "MKM", "status": "Attended"}],
        "agenda": [{"title": "Open", "presenter": "JM", "status": "Completed"}],
        "minutes": [{"title": "Welcome", "presenter": "JM", "text": "Opened."}],
        "decisions": [{"item_id": "D-001", "date": "2026-02-16", "description": "Adopted ToR."}],
        "actions": [{"item_id": "A-001", "description": "Validate", "owner": "DK", "target_date": "2026-06-30", "status": "Open"}],
    },
}


def test_build_tex_includes_logo_org_and_sections():
    tex = build_tex(
        MEETING,
        {"fields": {"org_name": "MKM Labs", "org_address": "1 Risk Lane", "framework": "FW"}},
        "logo.png",
    )
    assert "\\includegraphics" in tex and "logo.png" in tex
    assert "MKM Labs" in tex and "1 Risk Lane" in tex and "Q2 MRC" in tex
    for section in ("Participants", "Agenda", "Minutes", "Decisions", "Actions"):
        assert section in tex
    assert tex.strip().endswith("\\end{document}")


def test_build_tex_escapes_special_characters():
    tex = build_tex({"meeting_id": "M", "data": {"title": "P&L 50% _x_"}}, {"fields": {}})
    assert "P\\&L 50\\% \\_x\\_" in tex
    assert "\\includegraphics" not in tex


def test_build_tex_omits_empty_sections():
    tex = build_tex({"meeting_id": "M", "data": {}}, {"fields": {}})
    assert "Participants" not in tex and "Agenda" not in tex


def test_compile_tex_produces_pdf():
    tex = build_tex(MEETING, {"fields": {"org_name": "MKM"}}, "logo.png")
    pdf = compile_tex(tex, {"logo.png": PNG})
    assert pdf[:4] == b"%PDF"


def _stub_compile(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "src.governance.mrc.pack.compile_tex",
        lambda tex, assets=None: (captured.update(tex=tex, assets=assets) or b"%PDF-stub"),
    )
    return captured


def test_render_without_logo(monkeypatch):
    captured = _stub_compile(monkeypatch)
    assert render_pack_pdf(MEETING, {"fields": {}, "logo": None}) == b"%PDF-stub"
    assert captured["assets"] == {}


def test_render_embeds_uploaded_logo(monkeypatch):
    captured = _stub_compile(monkeypatch)
    save_upload("mrc", "logo.png", PNG)
    settings = {"fields": {}, "logo": {"filename": "logo.png", "original_name": "logo.png"}}
    render_pack_pdf(MEETING, settings)
    assert "logo.png" in captured["assets"]


def test_render_skips_missing_logo_file(monkeypatch):
    captured = _stub_compile(monkeypatch)
    settings = {"fields": {}, "logo": {"filename": "gone.png", "original_name": "gone.png"}}
    render_pack_pdf(MEETING, settings)
    assert captured["assets"] == {}


def test_render_skips_non_image_logo(monkeypatch):
    captured = _stub_compile(monkeypatch)
    settings = {"fields": {}, "logo": {"filename": "doc.pdf", "original_name": "doc.pdf"}}
    render_pack_pdf(MEETING, settings)
    assert captured["assets"] == {}
