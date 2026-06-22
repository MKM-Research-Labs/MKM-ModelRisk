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

"""Subsection 4.2: copyright/license-header governance audit.

An audit check — not a model — sitting next to the coverage (Section 3) and
__init__.py (Subsection 4.1) audits.  Every first-party ``.py``/``.js`` file
must begin with the exact 19-line MKM license header from
``docs/shared/copyright.py`` (after an optional shebang).

The scan/repair logic lives here (``is_compliant`` / ``fix_text`` / ``fix_repo``)
and is exercised by the self-healing audit test in
``tests/commands/test_copyright_headers_report.py`` (which repairs in place under
``app.py test``).  ``_build_copyright_headers`` renders the read-only compliance
section for the consolidated audit report.
"""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .._constants import NAVY, _TBL_STYLE_BASE, _root

# Single source of truth for the canonical license text.
_CANONICAL_SOURCE = ('docs', 'shared', 'copyright.py')

# Directories never descended: vendored code, caches, the ``data`` symlink to
# the shared SSD, and sibling/nested git worktrees under .claude / .claire.
_PRUNE_DIRS = {
    '.git', '.claude', '.claire', 'worktrees',
    '__pycache__', 'node_modules', '.venv', 'venv',
    'data', 'dist', 'build', '.pytest_cache', '.mypy_cache', '.ruff_cache',
}

# Substrings (case-insensitive) marking an existing — but possibly wrong —
# license block, so we replace a header and never a file's first real comment.
_LICENSE_MARKERS = ('mkm research labs', 'copyright (c)', 'all rights reserved')

# Source extensions in scope, mapped to their line-comment prefix.
_COMMENT_CHAR = {'.py': '#', '.js': '//'}


# ---------------------------------------------------------------------------
# Canonical header
# ---------------------------------------------------------------------------
def canonical_source_path(root: Path) -> Path:
    return Path(root).joinpath(*_CANONICAL_SOURCE)


def load_canonical_py(root: Path):
    """Canonical header as a list of ``#``-prefixed lines, read verbatim from
    copyright.py (intentional trailing whitespace preserved)."""
    text = canonical_source_path(root).read_text(encoding='utf-8')
    return text.splitlines()


def _to_js(py_lines):
    out = []
    for ln in py_lines:
        if ln == '':
            out.append('//')
        elif ln.startswith('# '):
            out.append('// ' + ln[2:])
        elif ln == '#':
            out.append('//')
        else:
            out.append(ln)  # defensive: canonical is all comments/blanks
    return out


def canonical_lines(root: Path, ext: str):
    py = load_canonical_py(root)
    return py if ext == '.py' else _to_js(py)


# ---------------------------------------------------------------------------
# Compliance check + repair
# ---------------------------------------------------------------------------
def is_compliant(text: str, canon) -> bool:
    """True when *text* begins with the canonical header, allowing an optional
    shebang and an optional single blank line after it."""
    lines = text.splitlines()
    i = 0
    if lines and lines[0].startswith('#!'):
        i = 1
        if i < len(lines) and lines[i] == '':
            i += 1
    return lines[i:i + len(canon)] == list(canon)


def fix_text(text: str, canon, ext: str):
    """Return ``(new_text, old_header)`` when *text* is non-compliant, else
    ``(None, None)``.  An existing license block is replaced; otherwise the
    header is inserted.  A shebang and any non-license leading comment survive;
    ``old_header`` is the replaced block ('' when none was present)."""
    if is_compliant(text, canon):
        return None, None

    lines = text.splitlines()
    comment_char = _COMMENT_CHAR[ext]

    shebang = None
    idx = 0
    if lines and lines[0].startswith('#!'):
        shebang = lines[0]
        idx = 1

    k = idx
    while k < len(lines):
        stripped = lines[k].strip()
        if stripped == '' or stripped.startswith(comment_char):
            k += 1
        else:
            break
    leading = lines[idx:k]
    has_license = any(
        any(m in ln.lower() for m in _LICENSE_MARKERS) for ln in leading
    )

    if has_license:
        old_header = '\n'.join(leading).strip()
        body = lines[k:]
    else:
        old_header = ''
        body = lines[idx:]

    while body and body[0].strip() == '':
        body.pop(0)

    out = []
    if shebang is not None:
        out.append(shebang)
        out.append('')
    out.extend(canon)
    if body:
        out.append('')
        out.extend(body)
    return '\n'.join(out) + '\n', old_header


def iter_source_files(root: Path):
    """Yield ``(path, ext)`` for every in-scope .py/.js file under *root*,
    pruning vendored/cache/worktree dirs and skipping the canonical source."""
    root = Path(root)
    canon_src = canonical_source_path(root).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for name in filenames:
            ext = os.path.splitext(name)[1]
            if ext not in _COMMENT_CHAR:
                continue
            path = Path(dirpath) / name
            if path.resolve() == canon_src:
                continue
            yield path, ext


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def fix_repo(root: Path, apply: bool = True) -> dict:
    """Scan every in-scope file under *root*, repairing non-compliant headers.

    ``apply=True`` writes the rewrites to disk; ``apply=False`` is a dry run
    that reports what *would* change without touching anything.  Returns
    per-file records: each non-compliant file is reported as (a) wrong/missing,
    (b) replaced, (c) now compatible.
    """
    root = Path(root)
    canon_py = load_canonical_py(root)
    canon_js = _to_js(canon_py)

    fixed, remaining = [], []
    already_compliant = 0
    scanned = 0

    for path, ext in iter_source_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        canon = canon_py if ext == '.py' else canon_js
        if is_compliant(text, canon):
            already_compliant += 1
            continue

        new_text, old_header = fix_text(text, canon, ext)
        rec = {
            'file': _rel(path, root),
            'old_header': old_header or '(no header present)',
            'had_wrong_header': True,
        }
        if apply and new_text is not None:
            path.write_text(new_text, encoding='utf-8')
            rec['now_compliant'] = is_compliant(new_text, canon)
            fixed.append(rec)
        else:
            rec['now_compliant'] = False
            remaining.append(rec)

    return {
        'scanned': scanned,
        'already_compliant': already_compliant,
        'fixed': fixed,
        'remaining': remaining,
    }


# ---------------------------------------------------------------------------
# Full-audit subsection (read-only render)
# ---------------------------------------------------------------------------
def _build_copyright_headers(styles) -> list:
    """4.2 — report .py/.js header compliance.  Read-only (dry) scan; the
    self-healing test repairs the tree, so in steady state this is PASS."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.2 Copyright Header Audit', styles['h3']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Policy: every first-party <b>.py</b> and <b>.js</b> file must begin '
        'with the exact 19-line MKM Research Labs license header defined in '
        '<b>docs/shared/copyright.py</b> (after an optional shebang). The audit '
        'test is self-healing — a wrong or missing header is rewritten in place '
        'and recorded as (a) wrong, (b) replaced, (c) now compatible.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        scan = fix_repo(_root, apply=False)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run copyright-header audit: {exc}', styles['body']))
        return elems

    remaining = scan['remaining']
    elems.append(Paragraph(
        f'Files scanned: <b>{scan["scanned"]}</b> &nbsp;|&nbsp; '
        f'Compliant: <b>{scan["already_compliant"]}</b> &nbsp;|&nbsp; '
        f'Non-compliant: <b>{len(remaining)}</b>.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not remaining:
        elems.append(Paragraph(
            'Every scanned .py/.js file carries the canonical header. '
            '<b>PASS</b>', styles['body']))
        return elems

    elems.append(Paragraph(
        f'{len(remaining)} file(s) are not compliant (showing up to 25). The '
        'audit test (tests/commands/test_copyright_headers_report.py) repairs '
        'these under <b>app.py test</b>.', styles['body']))
    elems.append(Spacer(1, 2 * mm))
    data = [[
        Paragraph('<b>File (relative to project root)</b>', styles['tbl_hdr']),
        Paragraph('<b>Existing header (first line)</b>', styles['tbl_hdr']),
    ]]
    for r in remaining[:25]:
        rel = r['file']
        if len(rel) > 58:
            rel = '…' + rel[-56:]
        old_lines = (r.get('old_header') or '').splitlines()
        old0 = old_lines[0] if old_lines else '(no header present)'
        if len(old0) > 58:
            old0 = old0[:56] + '…'
        data.append([
            Paragraph(rel, styles['tbl_cell']),
            Paragraph(old0, styles['tbl_cell']),
        ])
    tbl = Table(data, colWidths=[96 * mm, 72 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
    ]))
    elems.append(tbl)
    return elems
