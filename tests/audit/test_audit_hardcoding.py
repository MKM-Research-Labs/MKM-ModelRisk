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
"""Audit gate: hard-coded parameters (coding rule R1)."""
from __future__ import annotations

import ast

from audit.hardcoding import (
    _is_allcaps,
    _is_numeric,
    _scan_allcaps,
    _scan_infra,
    hardcoding_findings,
)


def _value(src: str) -> ast.AST:
    return ast.parse(src).body[0].value


def test_is_allcaps():
    assert _is_allcaps("MAX_RETRIES")
    assert not _is_allcaps("ABC")          # no underscore
    assert not _is_allcaps("A_B")          # too short
    assert not _is_allcaps("lower_case")   # not upper


def test_is_numeric():
    assert _is_numeric(_value("X = 5"))
    assert _is_numeric(_value("X = -3.5"))
    assert _is_numeric(_value("X = [1, 2, 3]"))
    assert not _is_numeric(_value("X = True"))
    assert not _is_numeric(_value("X = 'a'"))
    assert not _is_numeric(_value("X = [1, 'a']"))


def test_scan_allcaps_flags_only_numeric_constants():
    found = _scan_allcaps(ast.parse("MAX_N = 10\nLABEL = 'x'\nlower = 3"), "m.py")
    assert [f["name"] for f in found] == ["MAX_N"]


def test_scan_infra_flags_literals_but_not_comments():
    assert _scan_infra('host = "127.0.0.1"', "m.py")
    assert _scan_infra("url = 'http://localhost'", "m.py")
    assert _scan_infra("# reach me at 127.0.0.1", "m.py") == []


def test_repo_has_no_hardcoded_parameters():
    assert hardcoding_findings() == []
