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
"""Audit gate: screens use the shared layout vocabulary (coding rule R11)."""
from __future__ import annotations

from audit import layout
from audit.layout import layout_findings


def test_every_screen_uses_the_shared_headings_and_tab_bars():
    assert layout_findings() == []


def _scan(tmp_path, monkeypatch, js="", css=""):
    (tmp_path / "js").mkdir()
    (tmp_path / "css").mkdir()
    (tmp_path / "js" / "screen.js").write_text(js, encoding="utf-8")
    (tmp_path / "css" / "app.css").write_text(css, encoding="utf-8")
    monkeypatch.setattr(layout, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(layout, "LAYOUT_ASSET_DIRS", ("js",))
    monkeypatch.setattr(layout, "LAYOUT_STYLESHEET_DIR", "css")
    monkeypatch.setattr(layout, "walk", lambda root, suffix: sorted(root.rglob("*" + suffix)))
    monkeypatch.setattr(layout, "rel", lambda p: p.name)
    return {(f["kind"], f["line"]) for f in layout_findings()}


def test_a_card_or_modal_title_passes_and_any_other_heading_does_not(tmp_path, monkeypatch):
    js = ("x = '<div class=\"card\"><h3>Title</h3>';\n"
          "y = '<div class=\"modal\"><h2>Preview</h2>';\n"
          "z = '<h4 style=\"margin:0\">Weights</h4>';\n"
          "// '<h5>' in a comment is not markup\n")
    assert _scan(tmp_path, monkeypatch, js=js) == {("heading", 3)}


def test_a_tab_bar_takes_no_modifier_class(tmp_path, monkeypatch):
    js = ("a = '<div class=\"dtabs\">';\n"
          "b = '<div class=\"dtabs admin-tabs\">';\n"
          "c = '<div class=\"dtabs\" style=\"margin-top:var(--space-4)\">';\n")
    assert _scan(tmp_path, monkeypatch, js=js) == {("tab_bar_variant", 2)}


def test_only_the_three_shared_heading_rules_may_style_a_heading(tmp_path, monkeypatch):
    css = (".card h3 { font-size: var(--size-xs); }\n"
           "/* .card h4 { } is a comment */\n"
           ".modal h2, .brand h1 { margin: 0; }\n"
           ".card h3.vocab-group { font-size: var(--size-lg); }\n")
    assert _scan(tmp_path, monkeypatch, css=css) == {("heading_style", 4)}
