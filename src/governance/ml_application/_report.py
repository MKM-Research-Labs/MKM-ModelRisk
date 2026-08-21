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
"""The ML Application dossier: the record rendered as document sections.

The ML sibling of ``_report_model`` and ``_report_product``, and built from the
same shared blocks (``src.governance.report_blocks``) so the three documents look
like one family rather than three efforts.

What is particular to this one is the order. A reader arrives asking what the thing
is for and what it is built on, so Use case and Estimator lead; the classification
and governance record follows; the registers and the questionnaire close it. An
unanswered question is stated as unanswered rather than omitted -- a dossier that
silently drops what nobody filled in reads as a complete record of a complete model.
"""
from __future__ import annotations

from typing import Any

from config.governance import (ML_APPLICATION_COLLECTION_SPECS, ML_APPLICATION_FIELD_SPECS,
                               ML_REVIEW_QUESTIONS_COLLECTION)
from src.governance import report_blocks as rb
from src.governance.latex import _section, _wrappable
from src.governance.report_blocks import NOT_RECORDED

# The description opens the dossier as a paragraph, so it is not repeated in the
# field table beneath it.
SKIP_FIELDS = {"description"}

REVIEW_DATES_GROUP = "Review dates"
REVIEW_DUE_LABEL = "Review due (at document date)"

# How each register is laid out: per-column widths for a table, or "blocks" where the
# fields carry too much prose to sit side by side in one row. The questionnaire is
# blocks for exactly that reason -- an answer about training data is a paragraph.
LAYOUTS: dict[str, Any] = {
    "assumptions": (0.46, 0.10, 0.22, 0.22),
    "limitations": (0.46, 0.10, 0.22, 0.22),
    "model_weaknesses": "blocks",
    "remediation_steps": "blocks",
    "version_history": (0.10, 0.12, 0.30, 0.14, 0.20, 0.14),
    "data_sources": (0.32, 0.68),
    "change_history": (0.12, 0.14, 0.18, 0.16, 0.40),
    "operational_failure_events": "blocks",
    "actions": "blocks",
    ML_REVIEW_QUESTIONS_COLLECTION: "blocks",
    "signoff_history": "blocks",
    "signoff_requests": "blocks",
    "review_notes": "blocks",
    "review_signoffs": "blocks",
}

# Which registers appear, in order, and under what heading. "Retrains" rather than
# "Versions": a refit on new data is this record's substantial change, and calling it
# a version invites a reader to think of it as a code release.
COLLECTIONS = (
    (ML_REVIEW_QUESTIONS_COLLECTION, "Review questions"),
    ("assumptions", None),
    ("limitations", None),
    ("model_weaknesses", None),
    ("version_history", "Retrains"),
    ("data_sources", None),
    ("change_history", None),
    ("remediation_steps", None),
    ("operational_failure_events", None),
    ("signoff_history", "MRC sign-off history"),
)


def _groups() -> dict[str, list[str]]:
    return rb.field_groups(ML_APPLICATION_FIELD_SPECS, SKIP_FIELDS)


def _field_group(data: dict, title: str, keys: list[str], extra: list) -> str:
    return rb.field_group(data, title, keys, extra, field_specs=ML_APPLICATION_FIELD_SPECS)


def _collection(data: dict, name: str, label: str | None) -> str:
    return rb.collection(data, name, label, specs=ML_APPLICATION_COLLECTION_SPECS,
                         layouts=LAYOUTS)


def ml_application_section(record: dict, review_status: str) -> str:
    """One ML Application's complete dossier as top-level sections."""
    data = record.get("data", {})
    parts = [_section("Overview", _wrappable(data.get("description") or "") + "\n\n"
                      if data.get("description") else NOT_RECORDED)]
    for group, keys in _groups().items():
        extra = [[REVIEW_DUE_LABEL, review_status]] if group == REVIEW_DATES_GROUP else []
        parts.append(_field_group(data, group, keys, extra))
    for name, label in COLLECTIONS:
        parts.append(_collection(data, name, label))
    parts.append(rb.documents(data))
    return "".join(parts)
