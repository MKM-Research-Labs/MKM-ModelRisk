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
"""The legal notice carried by a generated document.

The platform ships without one. A notice asserts somebody's rights over their own
model documentation, and the only party who can assert those is the institution
generating the document -- a default would put a claim written for someone else on
every adopter's documents. So these tests check the mechanism: the wording an
institution records in Admin > Misc reaches every document family, and nothing is
printed until one does.
"""
from __future__ import annotations

import pytest

from config.reporting import DEFAULT_LEGAL_NOTICE
from src.governance import wording
from src.governance.latex import _quoted, legal_notice, title_page
from src.governance.mrc_settings import set_field
from src.governance.model_inventory.document import build_model_document_tex
from src.governance.model_inventory.report import build_report_tex
from src.governance.mrc.pack import build_tex as build_pack_tex

MODEL = {"model_id": "M1", "data": {"name": "Alpha"}}
SETTINGS = {"fields": {"org_name": "MKM"}}

# The adopting institution's own words. The phrase asserted below survives LaTeX
# escaping, so the assertions check the real text rather than that some block
# happens to be present.
NOTICE = "Property of Sterling Bank plc.\n\nCirculation is restricted."
PHRASE = "Circulation is restricted."


@pytest.fixture
def filed_notice():
    """An institution has filed its notice in Admin > Misc."""
    set_field(field="report_legal_notice", actor="a@b.c", value=NOTICE)


def test_title_page_carries_the_notice(filed_notice):
    """Every document family reaches the notice through the shared title page, so
    the wording an institution files is on all of them or on none."""
    assert PHRASE in title_page("T", "S")
    assert "Legal notice" in title_page("T", "S")


def test_model_risk_document_carries_the_notice(filed_notice):
    assert PHRASE in build_model_document_tex(MODEL, SETTINGS, "2026-06-22")


def test_model_risk_report_carries_the_notice(filed_notice):
    assert PHRASE in build_report_tex([MODEL], SETTINGS, "2026-06-22")


def test_meeting_pack_carries_the_notice(filed_notice):
    meeting = {"meeting_id": "MTG-1", "data": {"title": "Q3", "date": "2026-09-30"}}
    assert PHRASE in build_pack_tex(meeting, SETTINGS)


def test_no_notice_is_shipped_for_an_adopter_to_publish_unread():
    """The platform is MIT-licensed and says nothing about the contents of the
    documents it generates; the notice speaks to the models and methodology a
    document describes. Shipping wording for that would have every adopter
    publishing a claim it did not write, so there is none to ship."""
    assert DEFAULT_LEGAL_NOTICE == ()


def test_straight_quotes_become_latex_quote_pairs():
    assert _quoted('an "as is" basis') == "an ``as is\'\' basis"


def test_notice_block_is_empty_when_an_adopter_clears_it():
    """An institution that files its own notice elsewhere can empty the setting
    rather than having a block it did not write printed on its documents."""
    assert legal_notice(()) == ""


def test_title_page_splits_the_notice_into_paragraphs(filed_notice):
    """The notice is the institution's own words, recorded in Admin > Misc. Blank
    lines separate paragraphs, and each becomes its own block."""
    tex = title_page("T", "S")
    assert "Property of Sterling Bank plc." in tex
    assert "Circulation is restricted." in tex
    assert tex.count("\\par\\medskip") == 2   # heading + one paragraph break


def test_notice_is_dropped_when_the_setting_is_saved_empty():
    set_field(field="report_legal_notice", value="", actor="a@b.c")
    assert "Legal notice" not in title_page("T", "S")


def test_no_notice_is_invented_when_nothing_is_recorded(monkeypatch):
    """Nothing recorded (a fresh install, or the settings unreadable): the document
    carries no notice, rather than one the institution never wrote."""
    monkeypatch.setattr(wording, "_settings_fields", lambda settings=None: {})
    assert "Legal notice" not in title_page("T", "S")
