# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Subsection 4.3: path-definition governance audit.

An audit check — not a model — sitting beside the copyright-header (4.2) and
hard-coding (Section 5) audits.  Policy: **every filesystem path definition
must be housed in the** ``config`` **package.**  Modules elsewhere obtain
directories from the config accessors (``config.get_project_root()``,
``config.get_input_dir()``, ``config.get_output_dir()``, …) instead of
hand-deriving the project root or hard-coding ``data/`` paths.

The scan logic (``scan_repo`` / ``scan_text``) is exercised by the gate test in
``tests/commands/test_path_definitions_report.py`` (zero-tolerance: it fails on
any non-allowlisted finding), and ``_build_path_definitions`` renders the
read-only compliance section for the consolidated audit report.

What is flagged (outside ``config`` — the sanctioned home from
``config.path.registry.SANCTIONED_PACKAGE``):

* ``root_walk`` — deriving an ancestor directory by hand, e.g.
  ``Path(__file__).resolve().parents[2]`` or
  ``os.path.dirname(os.path.dirname(__file__))``.  Use
  ``config.get_project_root()``.
* ``data_literal`` — a string literal naming a ``data/`` sub-tree, e.g.
  ``"data/output"`` or ``"data/input/thames"``.  Use the matching accessor.
* ``data_segment`` — building a ``data/`` path segment-by-segment, e.g.
  ``root / "data" / "input"`` or ``os.path.join(root, "data")``.

The roots and sub-trees are read from ``config.path.registry`` so the policy
stays single-sourced.
"""

import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from config.path.registry import DATA_SUBDIRS, PROJECT_ROOT_DIRS, SANCTIONED_PACKAGE

from .._constants import NAVY, _TBL_STYLE_BASE, _root

# Directories never descended: the sanctioned config package, tests (which may
# legitimately build tmp paths), vendored code, caches, the ``data`` symlink to
# the shared SSD, infra, and sibling/nested git worktrees.
_PRUNE_DIRS = {
    SANCTIONED_PACKAGE,                       # config/ — the sanctioned home
    'tests',                                  # test fixtures build their own paths
    '.git', '.claude', '.claire', 'worktrees',
    '__pycache__', 'node_modules', '.venv', 'venv',
    'data', 'logs', 'docker', 'dist', 'build',
    '.pytest_cache', '.mypy_cache', '.ruff_cache',
}

# First-party .py files that genuinely cannot use a config accessor and are
# exempt by explicit, justified registration (mirrors the hard-coding audit's
# precision-constant allowlist).  Each entry is a repo-relative POSIX path
# mapped to the reason it is unavoidable.
_ALLOWLIST = {
    # Bootstrap: this module derives the repo root to put src/ on sys.path
    # *before* it can import config, so it cannot use config to find itself.
    'docs/models/full_audit/_constants.py':
        'audit bootstrap — derives root to import config (chicken-and-egg)',
}

# ---------------------------------------------------------------------------
# Detection patterns (built from the registry so the policy is single-sourced)
# ---------------------------------------------------------------------------

# Deriving an ancestor directory from __file__ by hand.
_ROOT_WALK_RE = re.compile(
    r'Path\(__file__\)[^#\n]*\.parents?\b'          # Path(__file__)....parent[s]
    r'|os\.path\.dirname\([^#\n]*__file__'          # os.path.dirname(... __file__)
)

# A string literal that *starts* with a data/ sub-tree, e.g. "data/output" or
# "./data/input/thames".  Anchoring to the start of the literal (after an
# optional ./ or ../ or leading /) keeps URLs like "https://host/data/output"
# and incidental substrings out of scope.
_data_subdirs = '|'.join(re.escape(s) for s in DATA_SUBDIRS)
_DATA_LITERAL_RE = re.compile(
    r"""['"](?:\.\.?)?/?data/(?:""" + _data_subdirs + r')\b'
)

# Building a project root dir as a path segment in a genuine path context:
# pathlib division (``root / "data"``) or os.path.join (``join(root, "data")``).
_root_dirs = '|'.join(re.escape(d) for d in PROJECT_ROOT_DIRS)
_DATA_SEGMENT_RE = re.compile(
    r"""/\s*['"](?:""" + _root_dirs + r""")['"]"""          # root / "data"
    r"""|os\.path\.join\([^)\n]*['"](?:""" + _root_dirs + r""")['"]"""  # join(.., "data")
)

# Precedence: most specific kind wins so each line yields a single finding.
_RULES = (
    ('root_walk', _ROOT_WALK_RE),
    ('data_literal', _DATA_LITERAL_RE),
    ('data_segment', _DATA_SEGMENT_RE),
)


def iter_source_files(root: Path):
    """Yield every in-scope first-party ``.py`` file under *root*.

    Prunes the sanctioned config package, tests, vendored/cache/worktree dirs
    and the shared ``data`` symlink, and skips this scanner module itself
    (whose source contains the very patterns it searches for)."""
    root = Path(root)
    self_path = Path(__file__).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for name in filenames:
            if not name.endswith('.py'):
                continue
            path = Path(dirpath) / name
            if path.resolve() == self_path:
                continue
            yield path


def _rel(path: Path, root: Path) -> str:
    try:
        return Path(path).relative_to(root).as_posix()
    except ValueError:
        return Path(path).as_posix()


def scan_text(text: str):
    """Return path-definition findings for one file's *text*.

    Each finding is ``{'line', 'kind', 'snippet'}``.  Comment lines and the
    interiors of triple-quoted blocks are skipped so prose and examples in
    docstrings are not mistaken for live path construction."""
    findings = []
    in_doc = None  # active triple-quote delimiter, or None
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()

        # Track (best-effort) triple-quoted blocks and skip their interiors.
        if in_doc:
            if in_doc in line:
                in_doc = None
            continue
        delim = next((d for d in ('"""', "'''") if stripped.startswith(d)), None)
        if delim is not None:
            # An odd delimiter count means the block stays open past this line;
            # an even count (e.g. a one-line """docstring""") is self-contained.
            if line.count(delim) % 2 == 1:
                in_doc = delim
            continue
        if stripped.startswith('#'):
            continue

        for kind, rx in _RULES:
            if rx.search(line):
                findings.append({'line': i, 'kind': kind,
                                 'snippet': stripped[:90]})
                break  # one finding per line (most specific rule wins)
    return findings


def scan_repo(root: Path = None) -> dict:
    """Scan the first-party tree for path definitions outside ``config``.

    Returns ``{'scanned', 'findings', 'allowlisted', 'files_with_findings'}``
    where ``findings`` are actionable violations (gate fails if non-empty) and
    ``allowlisted`` are present-but-registered exceptions, reported separately.
    """
    root = Path(root) if root is not None else _root
    findings, allowlisted = [], []
    scanned = 0
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        rel = _rel(path, root)
        bucket = allowlisted if rel in _ALLOWLIST else findings
        for f in scan_text(text):
            rec = {'file': rel, **f}
            if rel in _ALLOWLIST:
                rec['reason'] = _ALLOWLIST[rel]
            bucket.append(rec)

    files = sorted({f['file'] for f in findings})
    return {
        'scanned': scanned,
        'findings': findings,
        'allowlisted': allowlisted,
        'files_with_findings': files,
    }


# ---------------------------------------------------------------------------
# Full-audit subsection (read-only render)
# ---------------------------------------------------------------------------
_KIND_LABEL = {
    'root_walk': 'Hand-derived project root',
    'data_literal': 'Hardcoded data/ path literal',
    'data_segment': 'Hardcoded data/ path segment',
}


def _build_path_definitions(styles) -> list:
    """4.3 — report path definitions found outside the config package."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.3 Path-Definition Audit', styles['h3']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Policy: every filesystem path definition must be housed in the '
        '<b>config</b> package. First-party modules obtain directories from the '
        'config accessors (<b>config.get_project_root()</b>, '
        '<b>config.get_input_dir()</b>, <b>config.get_output_dir()</b>, …) rather '
        'than hand-deriving the project root or hard-coding <b>data/</b> paths. '
        'The owned roots are declared once in <b>config/path/registry.py</b>. '
        'This is a zero-tolerance gate (tests/commands/'
        'test_path_definitions_report.py): any non-allowlisted finding fails the '
        'build.', styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        scan = scan_repo()
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run path-definition audit: {exc}', styles['body']))
        return elems

    findings = scan['findings']
    elems.append(Paragraph(
        f'Files scanned: <b>{scan["scanned"]}</b> &nbsp;|&nbsp; '
        f'Violations: <b>{len(findings)}</b> in '
        f'<b>{len(scan["files_with_findings"])}</b> file(s) &nbsp;|&nbsp; '
        f'Registered exceptions: <b>{len(scan["allowlisted"])}</b>.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not findings:
        elems.append(Paragraph(
            'Every path definition lives in the config package. <b>PASS</b>',
            styles['body']))
        return elems

    elems.append(Paragraph(
        f'{len(findings)} path definition(s) found outside config (showing up '
        'to 30). Migrate each to the matching config accessor.', styles['body']))
    elems.append(Spacer(1, 2 * mm))
    data = [[
        Paragraph('<b>File</b>', styles['tbl_hdr']),
        Paragraph('<b>Line</b>', styles['tbl_hdr']),
        Paragraph('<b>Kind</b>', styles['tbl_hdr']),
        Paragraph('<b>Snippet</b>', styles['tbl_hdr']),
    ]]
    for r in findings[:30]:
        rel = r['file']
        if len(rel) > 42:
            rel = '…' + rel[-40:]
        data.append([
            Paragraph(rel, styles['tbl_cell']),
            Paragraph(str(r['line']), styles['tbl_cell_r']),
            Paragraph(_KIND_LABEL.get(r['kind'], r['kind']), styles['tbl_cell']),
            Paragraph(r['snippet'][:48], styles['tbl_cell']),
        ])
    tbl = Table(data, colWidths=[52 * mm, 12 * mm, 44 * mm, 60 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
    ]))
    elems.append(tbl)
    return elems
