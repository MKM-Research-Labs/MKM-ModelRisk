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
                               TRAINING_FIELD_SPECS, TRAINING_RUNS_COLLECTION,
                               TRAINING_SECTIONS,
                               ML_REVIEW_QUESTIONS_COLLECTION)
from src.governance import report_blocks as rb
from src.governance.latex import _para_table, _section, _subsection, _wrappable
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
    # Fifty-odd fields per train: blocks, never a table. A row per field is the only
    # shape a reader can follow, and it is what the section layout on screen does too.
    TRAINING_RUNS_COLLECTION: "blocks",
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


def _train(train: dict, index: int) -> str:
    """One fit, in the six sections it was recorded under and in that order.

    A flat run of fifty-three fields is unreadable and, worse, loses the ordering:
    the split is stated before the preprocessing that depends on it, so a reader
    meets "fitted on: full dataset" already knowing what the split was. Rendered
    flat, that argument disappears into an alphabet of labels.

    A field with nothing in it is STATED as not recorded rather than dropped. A
    document that silently omits what was never answered reads as a complete record
    of a complete fit, and the reader cannot tell the difference.
    """
    from src.governance.ml_application.training import applies

    body = []
    for number, (key, title) in enumerate(TRAINING_SECTIONS, start=1):
        rows = [[spec["label"], rb.value(train, field)]
                for field, spec in TRAINING_FIELD_SPECS.items()
                if spec["section"] == key and applies(field, train)]
        if rows:
            body.append(_subsection(f"{number}. {title}",
                                    _para_table(["Field", "Value"], rows, [0.30, 0.70],
                                                caption=f"{number}. {title}")))
    label = train.get("fit_id") or train.get("item_id") or str(index)
    return _subsection(f"Train {label}", "".join(body))


def _trains(data: dict) -> str:
    """Every fit, most recent first: the current one is what a reader came for."""
    runs = rb.items(data, TRAINING_RUNS_COLLECTION)
    if not runs:
        return _section("Trains", NOT_RECORDED)
    body = "".join(_train(t, i) for i, t in enumerate(reversed(runs), start=1))
    return _section("Trains", body)


def _evidence(data: dict) -> str:
    """What the training evidence adds up to, and what a reviewer must be told.

    The findings are the reason the tab is typed at all. A document carrying every
    field but not the fact that the scaler was fitted on the full dataset has buried
    the one line that decides whether the metrics above it mean anything.
    """
    state = data.get("training_completeness") or {}
    if not state.get("total"):
        return ""
    findings = state.get("qualifications") or []
    lead = (f"{state.get('filled', 0)} of {state.get('total', 0)} fields recorded on "
            "the most recent fit.\n\n")
    if not findings:
        return _section("Training evidence", lead +
                        "Nothing recorded here that a reviewer must be told about.\n\n")
    rows = [[f] for f in findings]
    return _section("Training evidence", lead +
                    _para_table(["A reviewer must be told"], rows, [1.0],
                                caption="Findings on the most recent fit"))


def ml_application_section(record: dict, review_status: str) -> str:
    """One ML Application's complete dossier as top-level sections."""
    data = record.get("data", {})
    parts = [_section("Overview", _wrappable(data.get("description") or "") + "\n\n"
                      if data.get("description") else NOT_RECORDED)]
    for group, keys in _groups().items():
        extra = [[REVIEW_DUE_LABEL, review_status]] if group == REVIEW_DATES_GROUP else []
        parts.append(_field_group(data, group, keys, extra))
    parts.append(_evidence(data))
    parts.append(_trains(data))
    for name, label in COLLECTIONS:
        parts.append(_collection(data, name, label))
    parts.append(rb.documents(data))
    return "".join(parts)
