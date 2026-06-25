# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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

from config.audit import SOURCE_DIRS

from audit._walk import REPO_ROOT, rel, walk

# The 19-line licence block (lines above the module docstring).
_CANONICAL = (REPO_ROOT / "docs" / "shared" / "copyright.py").read_text(
    encoding="utf-8").splitlines()[:19]


def _expected(suffix: str) -> list[str]:
    if suffix == ".js":
        return ["//" + line[1:] if line.startswith("#") else line for line in _CANONICAL]
    return _CANONICAL


def _has_header(path: Path, suffix: str) -> bool:
    head = path.read_text(encoding="utf-8", errors="replace").splitlines()[: len(_CANONICAL)]
    return head == _expected(suffix)


def header_findings() -> list[dict]:
    """First-party files whose opening lines are not the canonical header."""
    findings: list[dict] = []
    for suffix in (".py", ".js"):
        for name in (*SOURCE_DIRS, "audit"):
            for path in walk(REPO_ROOT / name, suffix):
                if not _has_header(path, suffix):
                    findings.append({"path": rel(path)})
    return findings
