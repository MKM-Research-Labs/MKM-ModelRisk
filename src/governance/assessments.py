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
"""Reading the assessment registers: what a record's measurements currently say.

Pure derivation, no I/O. The fairness register records one row per attribute per time
it was looked at, so "what does this firm currently believe about age?" is not any
single row -- it is the latest row for that attribute. That reading is here rather than
in the console because the sign-off gate and the screen must not be able to disagree
about it.

Nothing is stored resolved. A measured disparity is open until a later assessment of
the same attribute says otherwise, exactly as a challenge in a review thread is open
until a later note answers it. Both are derived for the same reason: the collections
are append-and-amend, and a state written onto the row would have to be maintained by
whoever remembered to.
"""
from __future__ import annotations

from typing import Any

from config.governance._assessments import (ADVERSE_EVALUATION_VERDICT,
                                             ADVERSE_FAIRNESS_VERDICT,
                                             EVALUATIONS_COLLECTION,
                                             FAIRNESS_COLLECTION)


def _key(value: Any) -> str:
    """What counts as the same subject: "Age band", "age  band" and "AGE BAND" are one
    attribute, because ``attribute`` is free text and has to be — which characteristics
    are protected is a matter of law and differs by jurisdiction."""
    return " ".join(str(value or "").split()).casefold()


def _latest_per_subject(rows, subject_field: str) -> list[dict[str, Any]]:
    """The last row recorded about each subject, in the order the subjects appear.

    Latest means last recorded, not the latest date field: the register is the order
    the work happened in, and a date somebody typed is not evidence of sequence. A
    backdated row still takes effect from where it was filed, which is what an audit
    trail is for.
    """
    latest: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        latest[_key(row.get(subject_field))] = row
    return list(latest.values())


def _unanswered(rows, subject_field: str, adverse: str) -> list[dict[str, Any]]:
    return [row for row in _latest_per_subject(rows, subject_field)
            if (row.get("verdict") or row.get("passed") or "") == adverse]


def current_fairness_position(data: dict) -> list[dict[str, Any]]:
    """The latest assessment of each attribute, in the order the attributes appear."""
    return _latest_per_subject(data.get(FAIRNESS_COLLECTION), "attribute")


def open_fairness_findings(data: dict) -> list[dict[str, Any]]:
    """Attributes whose most recent assessment found a disparity nobody has answered.

    A row is answered by a later assessment OF THE SAME ATTRIBUTE reaching a different
    verdict -- not by editing the original, and not by assessing something else. That
    is the whole gate: a review cannot be signed off while the firm's own latest word
    on an attribute is that it found a disparity.
    """
    return _unanswered(data.get(FAIRNESS_COLLECTION), "attribute",
                       ADVERSE_FAIRNESS_VERDICT)


def open_failed_evaluations(data: dict) -> list[dict[str, Any]]:
    """Kinds of evaluation whose most recent run failed and has not been re-run.

    Keyed by KIND rather than by row, because the question a committee asks is "does
    this thing pass its red-team exercise", not "did run 14 pass". A failed red team
    answered by a later passing red team is answered; a failed red team answered by a
    passing held-out score is not, and keying by kind is what keeps those apart.
    """
    return _unanswered(data.get(EVALUATIONS_COLLECTION), "kind",
                       ADVERSE_EVALUATION_VERDICT)


__all__ = ["current_fairness_position", "open_failed_evaluations",
           "open_fairness_findings"]
