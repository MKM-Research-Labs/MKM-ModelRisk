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
"""Shared file-discovery helpers for the coding-rule audits."""
from __future__ import annotations

from pathlib import Path

from config.audit import EXCLUDE_DIRS

REPO_ROOT = Path(__file__).resolve().parents[1]


def _excluded(rel: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def walk(root: Path, suffix: str):
    """Yield every ``*suffix`` file under ``root`` outside excluded dirs."""
    if not root.exists():
        return
    for path in sorted(root.rglob("*" + suffix)):
        if not _excluded(path.relative_to(REPO_ROOT)):
            yield path


def py_files(*dirs: str):
    """Yield ``.py`` files under each named top-level directory."""
    for name in dirs:
        yield from walk(REPO_ROOT / name, ".py")


def code_files(dirs, extensions):
    """Yield first-party code files with the given extensions, repo-wide.

    Covers root-level files (e.g. ``model.py``) plus every file under each named
    top-level directory in ``dirs``, restricted to ``extensions`` and outside
    the excluded dirs. This is the repo-wide counterpart to ``py_files`` — the
    scope the modularisation ("split") rule measures. Pass ``extensions=None``
    for every file regardless of suffix (the licence-notice scan's scope).
    """
    suffixes = None if extensions is None else frozenset(extensions)
    seen = set()

    def _emit(path: Path):
        if (path.is_file()
                and (suffixes is None or path.suffix in suffixes)
                and path not in seen
                and not _excluded(path.relative_to(REPO_ROOT))):
            seen.add(path)
            return True
        return False

    # Root-level files (e.g. model.py) — not covered by any sub-tree walk.
    for path in sorted(REPO_ROOT.glob("*")):
        if _emit(path):
            yield path
    # Named sub-trees.
    for name in dirs:
        root = REPO_ROOT / name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if _emit(path):
                yield path


def rel(path: Path) -> str:
    """Repo-relative POSIX path, for stable reporting."""
    return path.relative_to(REPO_ROOT).as_posix()


def count_lines(path: Path) -> int:
    with path.open(encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)
