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
"""The shape every measure returns, and the reasons it may decline to return a number.

A measure NEVER raises on data and never returns a figure that looks like an answer
when it is not one. Degenerate input is a finding in its own right -- "the sample was
too small to say" is what a monitoring report should print, and it is a different
sentence from "no shift detected". Code that had to catch exceptions to tell those
apart would end up printing whichever it caught first.
"""
from __future__ import annotations

from typing import Any

from config.governance._monitoring_measures import (STATUS_INSUFFICIENT_SAMPLE,
                                                    STATUS_NO_DATA, STATUS_OK,
                                                    STATUS_UNDEFINED, min_sample,
                                                    rag_for)


def result(measure: str, value: float | None, *, n: int, status: str,
           field_type: str | None = None, detail: Any = None) -> dict[str, Any]:
    """One measure's outcome, in the shape everything downstream reads.

    ``rag`` is resolved here rather than by the caller, so a value and its rating
    cannot disagree — and is ``None`` wherever there is no value to rate.
    """
    return {
        "measure": measure,
        "value": value,
        "rag": rag_for(measure, value, field_type) if status == STATUS_OK else None,
        "n": n,
        "status": status,
        "detail": detail,
    }


def no_data(measure: str, **kw) -> dict[str, Any]:
    return result(measure, None, n=0, status=STATUS_NO_DATA, **kw)


def undefined(measure: str, n: int, detail: str = "", **kw) -> dict[str, Any]:
    """The inputs were present but the measure has no meaning on them: one class, zero
    variance, no overlapping categories. Not an error and not a zero."""
    return result(measure, None, n=n, status=STATUS_UNDEFINED, detail=detail, **kw)


def too_few(measure: str, n: int, **kw) -> dict[str, Any]:
    return result(measure, None, n=n, status=STATUS_INSUFFICIENT_SAMPLE,
                  detail=f"{n} rows; {min_sample(measure)} required", **kw)


def enough(measure: str, n: int) -> bool:
    return n >= min_sample(measure)


__all__ = ["enough", "no_data", "result", "too_few", "undefined"]
