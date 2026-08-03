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
"""The disposable-database guard that stops tests truncating a live event log.

A dev ``.env`` sets ``DB_NAME=mkm_modelrisk``; a plain ``pytest`` run once
resolved the test database to that live name and the autouse truncation wiped
the real log. ``assert_disposable`` is the backstop every destructive fixture
now calls, so a protected database can never be reset.
"""
from __future__ import annotations

import pytest

from config.database import PROTECTED_DB_NAMES, assert_disposable


def test_the_live_database_is_protected():
    assert "mkm_modelrisk" in PROTECTED_DB_NAMES


@pytest.mark.parametrize("name", sorted(PROTECTED_DB_NAMES))
def test_assert_disposable_refuses_protected_databases(name):
    with pytest.raises(RuntimeError, match="protected database"):
        assert_disposable(name)


@pytest.mark.parametrize("name", ["mkm_modelrisk_test", "mkm_modelrisk_test_p123",
                                  "mkm_modelrisk_e2e", "mkm_modelrisk_journey"])
def test_assert_disposable_allows_scratch_databases(name):
    # A throwaway test database must pass silently (returns None, no raise).
    assert assert_disposable(name) is None
