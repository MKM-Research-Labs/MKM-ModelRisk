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
"""The small reads every clause probe is built from.

Lifted out of ``framework.py`` when the AI System probes arrived and needed the
same four functions. One home rather than two copies -- these are the definition
of what "the record carries this" means, and two copies free to drift is two
answers to that question.
"""
from __future__ import annotations

from typing import Any

from src.governance.completeness._gaps import _recorded


def _data(record: dict) -> dict:
    return record.get("data") or {}


def _filled(data: dict, *fields: str) -> bool:
    """Whether every named scalar field holds an answer rather than a placeholder."""
    return all(_recorded(data.get(field)) for field in fields)


def _any_entries(data: dict, *collections: str) -> bool:
    """Whether any of the named collections holds at least one entry."""
    return any(data.get(name) for name in collections)


def _share(estate: dict, predicate, applies=None) -> tuple[int, int]:
    """How many of the applicable records carry the evidence.

    ``applies`` narrows the population to the records a clause bites on. A clause
    that only applies to some of the estate must not be scored against all of it --
    and a population of zero is reported rather than hidden, because "nothing needed
    it" is a claim the reader should get to challenge.
    """
    population = [_data(record) for record in estate["models"]]
    if applies is not None:
        population = [d for d in population if applies(d)]
    return sum(1 for d in population if predicate(d)), len(population)


__all__ = ["_data", "_filled", "_any_entries", "_share"]
