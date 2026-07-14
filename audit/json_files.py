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
"""JSON-file audit (coding rule R6): source should not persist to ``.json`` files.

MKM-ModelRisk keeps its state in the Postgres event store, so first-party source
should neither read nor write ``.json`` files on disk. This audit tracks the
json->Postgres migration backlog: every ``.json`` file touch under the source
tree is a finding, split by kind so the remaining ones are visible.

A finding is:

* ``load``  — a ``json.load(`` call (file deserialisation).
* ``dump``  — a ``json.dump(`` call (file serialisation).
* ``path``  — a ``.json`` path literal used in a filesystem context (``open``,
  ``Path(...)``, ``read_text``/``write_text``, ``glob`` …). A bare ``.json``
  string with no I/O around it — a filename constant, a type-label table — is
  not flagged, so the audit does not report its own naming machinery.

Comment lines and triple-quoted blocks are skipped so prose and examples in
docstrings are not mistaken for real I/O. This audit package is excluded (its own
source contains the very patterns it searches for), as are config/manifest
artefacts registered in ``JSON_IO_ALLOWLIST``. Reported rather than gated for now.
"""
from __future__ import annotations

import re

from config.audit import JSON_IO_ALLOWLIST, REPO_SCAN_DIRS

from audit._walk import code_files, rel

_SELF_PKG = "audit/"

_LOAD_RE = re.compile(r"\bjson\.load\s*\(")
_DUMP_RE = re.compile(r"\bjson\.dump\s*\(")
_JSON_LITERAL_RE = re.compile(r"""['"][^'"]*\.json['"]""")
# Filesystem intent on a line: only then is a bare ``.json`` literal real I/O
# (rather than a filename constant or a lookup-table value).
_FS_CONTEXT_RE = re.compile(
    r"\b(?:open|read_text|read_bytes|write_text|write_bytes|glob|iterdir|Path)\s*\("
    r"|\bos\.path\b|\bjson\.load\b|\bjson\.dump\b")

# Most specific first: a line calling json.load/json.dump is classified as such
# even when it also mentions a ``.json`` literal.
_CALL_RULES = (
    ("load", _LOAD_RE),
    ("dump", _DUMP_RE),
)


def _allowlisted(line: str) -> bool:
    """True if the line only touches an allowlisted config/manifest ``.json``."""
    return any(name in line for name in JSON_IO_ALLOWLIST)


def _classify(line: str) -> str | None:
    """The finding kind for one code line, or ``None`` when it is not JSON I/O."""
    for kind, rx in _CALL_RULES:
        if rx.search(line):
            return kind
    if _JSON_LITERAL_RE.search(line) and _FS_CONTEXT_RE.search(line):
        return "path"
    return None


def _scan_text(text: str, path: str) -> list[dict]:
    """JSON-file findings for one file's *text* (comments/docstrings skipped)."""
    out = []
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
        if stripped.startswith("#") or _allowlisted(line):
            continue
        kind = _classify(line)
        if kind is not None:
            out.append({"path": path, "line": index, "kind": kind,
                        "snippet": stripped[:90]})
    return out


def json_file_findings() -> list[dict]:
    """Report ``.json`` file I/O found under the source tree.

    Skips this audit package (its source contains the patterns it searches for)
    and allowlisted config/manifest files.
    """
    findings = []
    for path in code_files(REPO_SCAN_DIRS, (".py",)):
        relpath = rel(path)
        if relpath.startswith(_SELF_PKG):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(_scan_text(text, relpath))
    return sorted(findings, key=lambda f: (f["path"], f["line"]))
