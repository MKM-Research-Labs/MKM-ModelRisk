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
"""The audit reaches every first-party tree, including its own.

``REPO_SCAN_DIRS`` is a hand-written list, and a hand-written list of directories
goes stale the moment somebody adds one. It did: ``audit/``, ``packages/`` and
``modelrisk/`` were missing until 2026-09-05, so the audit suite was the single
tree its own rules never measured, and ``audit/pdf.py`` sat 12 lines over the R2
limit without ever being reported.

The test below is the part that does not go stale -- it derives the answer from
the filesystem instead of restating the list, so a package added tomorrow fails
here rather than quietly opting out of every rule.
"""
from __future__ import annotations

from pathlib import Path

from config.audit import EXCLUDE_DIRS, REPO_SCAN_DIRS

_ROOT = Path(__file__).resolve().parents[2]

# ``tests`` is first-party and deliberately absent: it carries a higher size
# limit and is scanned separately by ``large_test_files``. It is the only tree
# entitled to that exemption, and naming it here is what makes it an exemption
# rather than an oversight.
_SCANNED_ELSEWHERE = {"tests"}


def _first_party_python_trees() -> set[str]:
    """Top-level directories holding first-party Python, read off the disk."""
    found = set()
    for entry in _ROOT.iterdir():
        if not entry.is_dir() or entry.name.startswith(".") or entry.name in EXCLUDE_DIRS:
            continue
        if any(entry.rglob("*.py")):
            found.add(entry.name)
    return found


def test_every_first_party_python_tree_is_scanned():
    unscanned = _first_party_python_trees() - set(REPO_SCAN_DIRS) - _SCANNED_ELSEWHERE
    assert not unscanned, (
        "these trees hold first-party Python that no audit rule reads: "
        f"{sorted(unscanned)}. Add them to REPO_SCAN_DIRS in config/audit.py, or "
        "to _SCANNED_ELSEWHERE here with the reason they are exempt."
    )


def test_the_audit_measures_itself():
    # The specific case that went unnoticed, pinned on its own: a tool that
    # grades the codebase is part of the codebase it grades.
    assert "audit" in REPO_SCAN_DIRS


def test_scan_roots_all_exist():
    # A directory renamed away leaves a dead entry that silently scans nothing,
    # which reads exactly like a clean result.
    missing = [d for d in REPO_SCAN_DIRS if not (_ROOT / d).is_dir()]
    assert not missing, f"REPO_SCAN_DIRS names directories that do not exist: {missing}"
