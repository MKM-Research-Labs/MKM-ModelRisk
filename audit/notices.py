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
"""R5 (reported): a licence notice on every file the header gate does not cover.

R5's full-block gate is ``.py``/``.js`` only (see ``audit.headers``). Everything
else first-party — ``.sql``, ``.css``, ``.html``, ``.sh``, ``.md``, config and
images — carries a one-line notice in its own comment syntax instead. A file that
cannot hold a comment (JSON forbids them; binaries have no syntax) is marked by a
sibling ``<name>.license`` file. Reported, not gating: the wording is prose.
"""
from __future__ import annotations

from pathlib import Path

from config.audit import (FIRST_PARTY_DIRS, HEADER_EXTENSIONS,
                          NOTICE_EXCLUDE_NAMES, NOTICE_EXEMPT_NAMES,
                          NOTICE_MARKER, NOTICE_SIBLING_SUFFIX)

from audit._walk import code_files, rel


def _is_marked(path: Path) -> bool:
    """True when the file states the notice, or a sibling ``.license`` does."""
    if path.with_name(path.name + NOTICE_SIBLING_SUFFIX).exists():
        return True
    try:
        return NOTICE_MARKER in path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False  # binary with no sibling — unmarked


def _in_scope(path: Path) -> bool:
    if path.suffix in HEADER_EXTENSIONS:
        return False  # the header gate owns these
    if path.suffix == NOTICE_SIBLING_SUFFIX:
        return False  # a marker is not itself a subject
    if path.name in NOTICE_EXCLUDE_NAMES:
        return False  # generated or local-only, not first-party
    return path.name not in NOTICE_EXEMPT_NAMES


def notice_findings() -> list[dict]:
    """First-party non-``.py``/``.js`` files carrying no licence notice."""
    return [{"path": rel(path), "kind": path.suffix or "(no suffix)"}
            for path in code_files(FIRST_PARTY_DIRS, None)
            if _in_scope(path) and not _is_marked(path)]
