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
"""Tests for the Meeting Pack LaTeX generation and PDF compilation."""
from __future__ import annotations

import base64
import shutil

import pytest

from src.files import save_upload
from src.governance.mrc.pack import (
    TectonicNotFound, build_tex, compile_tex, render_pack_pdf)

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


@pytest.mark.skipif(shutil.which("tectonic") is None, reason="tectonic not installed (optional)")
def test_compile_tex_produces_pdf():
    tex = build_tex(MEETING, {"fields": {"org_name": "MKM"}}, "logo.png")
    pdf = compile_tex(tex, {"logo.png": PNG})
    assert pdf[:4] == b"%PDF"


def test_compile_tex_raises_when_tectonic_missing(monkeypatch):
    # When the engine is absent, callers get a typed error they can translate
    # into a clean response — not a raw FileNotFoundError from subprocess.
    monkeypatch.setattr("src.governance.mrc.pack.shutil.which", lambda _name: None)
    with pytest.raises(TectonicNotFound, match="tectonic is not installed"):
        compile_tex("\\documentclass{article}\\begin{document}x\\end{document}")


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


def test_build_tex_includes_remediation_for_in_scope_models():
    """Open remediation steps for in-scope models surface as a Pack section."""
    meeting = {
        "meeting_id": "MTG1",
        "data": {
            "title": "Q3 MRC",
            "models_in_scope": [{"model_id": "MDL-A"}, {"model_id": "MDL-B"}],
        },
    }
    remediations = {
        "MDL-A": [
            {"item_id": "RM-001", "description": "Recalibrate vol surface",
             "owner": "Alice", "priority": "High", "due_date": "2026-12-01", "status": "Open"},
        ],
    }
    tex = build_tex(meeting, {"fields": {}}, None, remediations)
    assert "Model Remediation (in-scope)" in tex
    assert "MDL-A" in tex
    assert "Recalibrate vol surface" in tex
    # MDL-B has no items; it doesn't get a subsection.
    assert "{MDL-B}" not in tex


def test_build_tex_omits_remediation_when_empty():
    tex = build_tex({"meeting_id": "M", "data": {"models_in_scope": [{"model_id": "X"}]}},
                    {"fields": {}}, None, {})
    assert "Model Remediation" not in tex


def test_render_pack_pulls_remediations_from_inventory(monkeypatch):
    """render_pack_pdf reaches into the inventory projection for open steps."""
    captured = _stub_compile(monkeypatch)
    monkeypatch.setattr("src.governance.mrc.pack.build_tex",
                        lambda meeting, settings, logo, remediations:
                        (captured.update(remediations=remediations) or "tex"))
    monkeypatch.setattr("src.governance.model_inventory.get_model",
                        lambda mid: {"data": {"remediation_steps": [
                            {"item_id": "RM-1", "description": "Fix", "status": "Open"},
                            {"item_id": "RM-2", "description": "Done", "status": "Closed"},
                        ]}} if mid == "MDL-X" else None)
    meeting = {"meeting_id": "M", "data": {"models_in_scope": [{"model_id": "MDL-X"}]}}
    render_pack_pdf(meeting, {"fields": {}, "logo": None})
    assert list(captured["remediations"].keys()) == ["MDL-X"]
    # Closed steps are filtered out — only Open / In Progress flow into the pack.
    assert [s["item_id"] for s in captured["remediations"]["MDL-X"]] == ["RM-1"]
