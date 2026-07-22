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
"""The legal notice carried by every generated document."""
from __future__ import annotations

from config.reporting import DEFAULT_LEGAL_NOTICE
from src.governance.latex import _quoted, legal_notice, title_page
from src.governance.model_inventory.document import build_model_document_tex
from src.governance.model_inventory.report import build_report_tex
from src.governance.mrc.pack import build_tex as build_pack_tex

MODEL = {"model_id": "M1", "data": {"name": "Alpha"}}
SETTINGS = {"fields": {"org_name": "MKM"}}

# A phrase from the notice that survives LaTeX escaping, so the assertions below
# check the real text rather than that some block happens to be present.
PHRASE = "exclusive intellectual property and confidential trade secrets"


def test_title_page_carries_the_notice():
    """Every document family reaches the notice through the shared title page, so a
    new report cannot be published without one."""
    assert PHRASE in title_page("T", "S")
    assert "Legal notice" in title_page("T", "S")


def test_model_risk_document_carries_the_notice():
    assert PHRASE in build_model_document_tex(MODEL, SETTINGS, "2026-06-22")


def test_model_risk_report_carries_the_notice():
    assert PHRASE in build_report_tex([MODEL], SETTINGS, "2026-06-22")


def test_meeting_pack_carries_the_notice():
    meeting = {"meeting_id": "MTG-1", "data": {"title": "Q3", "date": "2026-09-30"}}
    assert PHRASE in build_pack_tex(meeting, SETTINGS)


def test_notice_covers_the_document_not_the_software_licence():
    """The platform is MIT-licensed; the notice speaks to the models and methodology
    the document describes. Asserting a software licence here would contradict it."""
    text = " ".join(DEFAULT_LEGAL_NOTICE)
    assert "MIT" not in text
    assert "algorithms, models, methodology" in text


def test_straight_quotes_become_latex_quote_pairs():
    assert _quoted('an "as is" basis') == "an ``as is'' basis"


def test_notice_block_is_empty_when_an_adopter_clears_it():
    """An institution that files its own notice elsewhere can empty the setting
    rather than having a block it did not write printed on its documents."""
    assert legal_notice(()) == ""
