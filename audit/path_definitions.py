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
"""Path-definition audit: filesystem paths belong in the ``config`` package.

Policy: **every filesystem path definition lives in** ``config``. Modules
elsewhere obtain directories from config (e.g. ``config.files.UPLOAD_DIR``,
``config.audit.AUDIT_OUTPUT_DIR``) rather than hand-deriving the project root or
hard-coding the ``uploads/`` tree. What is flagged outside ``config`` (and the
audit package, which must bootstrap its own repo root to scan):

* ``root_walk`` — deriving an ancestor directory by hand, e.g.
  ``Path(__file__).resolve().parents[1]`` or ``os.path.dirname(__file__)``.
* ``data_literal`` — a quoted string that is (or begins with) an owned data
  tree name, e.g. ``"uploads"``, ``"uploads/audit"``, ``root / "uploads"`` or
  ``os.path.join(root, "uploads")`` — every quoted use of the tree name.

The owned tree names come from ``config.audit.DATA_TREE_NAMES`` so the policy is
single-sourced. Comment lines and triple-quoted blocks are skipped so prose and
examples in docstrings are not mistaken for live path construction.

Reported rather than gated; registered exceptions live in ``_ALLOWLIST``.
"""
from __future__ import annotations

import re

from config.audit import DATA_TREE_NAMES, PATH_CONFIG_PACKAGE, REPO_SCAN_DIRS

from audit._walk import code_files, rel

# The audit package must derive the repo root to scan the tree, before (and
# independently of) config — the same chicken-and-egg config itself resolves.
_SELF_PKG = "audit/"

# First-party files exempt by explicit, justified registration. Kept minimal.
_ALLOWLIST: dict[str, str] = {
    # (none yet)
}

# Deriving an ancestor directory from __file__ by hand.
_ROOT_WALK_RE = re.compile(
    r"Path\(__file__\)[^#\n]*\.parents?\b"          # Path(__file__)....parent[s]
    r"|os\.path\.dirname\([^#\n]*__file__"          # os.path.dirname(... __file__)
)

# A quoted literal that opens with an owned tree name (optionally preceded by a
# ``./`` or ``../``) as a whole path segment — the trailing lookahead requires a
# closing quote or a ``/`` so ``"uploads"`` and ``"uploads/audit"`` match while a
# URL like ``"https://host/uploads/x"`` (no quote before the name) does not.
_names = "|".join(re.escape(n) for n in DATA_TREE_NAMES)
_DATA_LITERAL_RE = re.compile(
    r"""['"](?:\.\.?/)?(?:""" + _names + r")(?=['\"/])"
)

# Precedence: a hand-derived root wins over a data literal so each line yields a
# single, most-specific finding.
_RULES = (
    ("root_walk", _ROOT_WALK_RE),
    ("data_literal", _DATA_LITERAL_RE),
)


def _scan_text(text: str, path: str) -> list[dict]:
    """Path-definition findings for one file's *text* (comments/docstrings skipped)."""
    findings = []
    in_doc = None  # active triple-quote delimiter, or None
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if in_doc:
            if in_doc in line:
                in_doc = None
            continue
        delim = next((d for d in ('"""', "'''") if stripped.startswith(d)), None)
        if delim is not None:
            if line.count(delim) % 2 == 1:
                in_doc = delim
            continue
        if stripped.startswith("#"):
            continue
        for kind, rx in _RULES:
            if rx.search(line):
                findings.append({"path": path, "line": index, "kind": kind,
                                 "snippet": stripped[:90]})
                break  # one finding per line (most specific rule wins)
    return findings


def path_definition_findings() -> list[dict]:
    """Report path definitions found outside the ``config`` package.

    Skips the sanctioned config package, this audit package (its own root
    bootstrap) and allowlisted files.
    """
    exempt = (PATH_CONFIG_PACKAGE + "/", _SELF_PKG)
    findings = []
    for path in code_files(REPO_SCAN_DIRS, (".py",)):
        relpath = rel(path)
        if relpath.startswith(exempt) or relpath in _ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(_scan_text(text, relpath))
    return sorted(findings, key=lambda f: (f["path"], f["line"]))
