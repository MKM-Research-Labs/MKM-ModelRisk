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
"""R5: every first-party ``.py`` / ``.js`` file must carry the canonical header.

The single source of truth is the comment block at the top of
``docs/shared/copyright.py``; ``.js`` files use the same lines with ``//`` in
place of ``#``.
"""
from __future__ import annotations

from pathlib import Path

from config.audit import HEADER_EXTENSIONS, HEADER_SCAN_DIRS

from audit._walk import REPO_ROOT, code_files, rel

# Marks a leading comment block as a licence header rather than ordinary prose,
# so the fixer replaces only the header and never eats an explanatory comment.
_MARKER = "Copyright (c)"


def _canonical() -> list[str]:
    """The licence block: every leading ``#`` line, up to the module docstring."""
    lines = (REPO_ROOT / "docs" / "shared" / "copyright.py").read_text(
        encoding="utf-8").splitlines()
    block: list[str] = []
    for line in lines:
        if not line.startswith("#"):
            break
        block.append(line)
    return block


_CANONICAL = _canonical()


def _expected(suffix: str) -> list[str]:
    if suffix == ".js":
        return ["//" + line[1:] if line.startswith("#") else line for line in _CANONICAL]
    return _CANONICAL


def _split_shebang(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split a leading ``#!`` line off the rest; the header follows it."""
    if lines and lines[0].startswith("#!"):
        return lines[:1], lines[1:]
    return [], lines


def _has_header(path: Path, suffix: str) -> bool:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    _, rest = _split_shebang(lines)
    return rest[: len(_CANONICAL)] == _expected(suffix)


def _comment_prefix(suffix: str) -> str:
    return "//" if suffix == ".js" else "#"


def _strip_header(lines: list[str], prefix: str) -> list[str]:
    """Drop the leading comment block iff it is a licence header."""
    size = 0
    for line in lines:
        if not line.startswith(prefix):
            break
        size += 1
    if size and any(_MARKER in line for line in lines[:size]):
        return lines[size:]
    return lines


def _scan():
    """Every first-party file R5 covers, as ``(path, suffix)`` pairs."""
    for path in code_files(HEADER_SCAN_DIRS, HEADER_EXTENSIONS):
        yield path, path.suffix


def header_findings() -> list[dict]:
    """First-party files whose opening lines are not the canonical header."""
    return [{"path": rel(path)} for path, suffix in _scan()
            if not _has_header(path, suffix)]


def apply_headers() -> list[str]:
    """Rewrite every non-compliant file's header in place; return what changed.

    Self-healing counterpart to ``header_findings`` (coding rule R5): replaces an
    existing licence block, or prepends the header when a file has none.
    """
    changed: list[str] = []
    for path, suffix in _scan():
        if _has_header(path, suffix):
            continue
        text = path.read_text(encoding="utf-8")
        shebang, rest = _split_shebang(text.splitlines())
        body = _strip_header(rest, _comment_prefix(suffix))
        out = "\n".join(shebang + _expected(suffix) + body)
        if text.endswith("\n"):
            out += "\n"
        path.write_text(out, encoding="utf-8")
        changed.append(rel(path))
    return changed
