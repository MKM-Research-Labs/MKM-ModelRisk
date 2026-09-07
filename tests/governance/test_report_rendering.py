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
"""How a generated document treats the values it is handed.

Two small shared primitives that every PDF in the platform passes its content
through. Neither is interesting until it is wrong, and both are wrong in ways a
reader sees before anybody else does: a Python repr on a governance document, or a
report that will not build because the settings record is missing.
"""
from __future__ import annotations

from src.governance.report_blocks import _shown
from src.governance.wording import report_wording


def test_a_multi_value_field_reaches_the_page_as_a_sentence():
    """``['rainfall_mm', 'soil_moisture']`` is a Python repr, not a sentence. A record
    stores a multi-value field as a list, and the page must not show the brackets."""
    # Stated as an equivalence rather than by matching the output text: _shown also
    # LaTeX-escapes and inserts break hints, and a test that spelled those out would
    # fail the next time the escaping improved without anything being wrong.
    rendered = _shown(["rainfall_mm", "soil_moisture"])
    assert rendered == _shown("rainfall_mm, soil_moisture")
    assert "[" not in rendered and "'" not in rendered


def test_a_tuple_is_treated_the_same_as_a_list():
    """Same shape, same reader. Which of the two a projection happens to return is an
    implementation detail nobody reading the document should be able to tell."""
    assert _shown(("a", "b")) == _shown(["a", "b"])


def test_a_single_value_passes_through_unchanged():
    assert "Gradient boosting" in _shown("Gradient boosting")


def test_wording_falls_back_to_the_shipped_defaults_when_settings_cannot_be_read(
        monkeypatch):
    """A document must still build where there is no settings record — a unit test, a
    first run, a database that is up but empty. Failing to read the institution's
    preferred wording is a reason to use the shipped wording, never a reason to stop
    the compile: the report is the evidence, and no report is worse than one whose
    headings are not the adopter's own.
    """
    import src.governance.wording as wording_mod

    def _explode():
        raise RuntimeError("no settings record")

    monkeypatch.setattr("src.governance.mrc_settings.get_settings", _explode)
    assert isinstance(report_wording(), dict)


def test_wording_uses_the_settings_it_is_handed_without_reading_the_store(monkeypatch):
    """Passing settings in is the path every real caller takes — the report already
    holds them, and re-reading per field would be a query per heading."""
    def _should_not_be_called():
        raise AssertionError("get_settings was read despite settings being supplied")

    monkeypatch.setattr("src.governance.mrc_settings.get_settings",
                        _should_not_be_called)
    assert isinstance(report_wording({"fields": {}}), dict)
