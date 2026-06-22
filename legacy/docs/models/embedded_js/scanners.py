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

"""Source-tree scan passes for the embedded JS/CSS audit.

Front-end assets must live in companion ``.js`` / ``.css`` files under
``src/static/`` and be loaded at render time, not authored as Python string
literals.  These passes flag the three ways JS/CSS leaks into ``.py`` files.
"""

import re
from pathlib import Path

# Top-level dirs scanned by the repo-wide audit (all non-test source). Mirrors
# the modularisation report's scope so the two audits cover the same tree.
from docs.models.project._constants import REPO_SCAN_DIRS

# The audit tooling itself contains <script>…</script> as a *regex literal*
# (this module's _SCRIPT_RE) and similar markup in its PDF builder, so it would
# self-report a false positive. Exclude this package from its own scan.
_SELF_PKG = Path(__file__).resolve().parent  # docs/models/embedded_js

# A ``<script>`` body must contain at least this many JavaScript lines before
# it is flagged.  This deliberately lets through the accepted thin wrapper
# (``<script>window.__X_CONFIG = {cfg};\n{js_code}</script>``), whose body is a
# single ``window.__`` assignment plus a ``{...}`` interpolation read from disk.
MIN_JS_LINES = 3

# A ``<style>`` body must contain at least this many non-trivial CSS lines.
MIN_CSS_LINES = 3

# A run of JS lines outside any ``<script>``/``<style>`` tag must reach this
# length before it is reported as a JS "factory" string (e.g. pdf_viewer.py).
MIN_FACTORY_LINES = 8

# Tokens that are strong signals of JavaScript and rarely appear in Python.
# ``var``/``const``/``let``/``function(``/``=>`` are not Python; ``document.``,
# ``window.``, ``querySelector`` etc. are DOM APIs.
_JS_TOKEN_RE = re.compile(
    r'document\.'
    r'|window\.'
    r'|addEventListener'
    r'|querySelector'
    r'|getElementById'
    r'|\.innerHTML'
    r'|\.appendChild'
    r'|\.createElement'
    r'|\.forEach\('
    r'|console\.(log|error|warn)'
    r'|\bvar\s+\w'
    r'|\bconst\s+\w'
    r'|\blet\s+\w'
    r'|\bfunction\s*\('
    r'|=>\s*[{(]'
)

_SCRIPT_RE = re.compile(r'<script\b([^>]*)>(.*?)</script>', re.DOTALL | re.IGNORECASE)
_STYLE_RE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
_CSS_LINE_RE = re.compile(r'[{}]|[\w-]+\s*:\s*[^;]+;')


def _src_files(src_dir: Path):
    for p in sorted(src_dir.rglob('*.py')):
        if '__pycache__' in p.parts:
            continue
        # Skip the audit tooling itself (see _SELF_PKG above).
        if _SELF_PKG in p.resolve().parents:
            continue
        yield p


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _line_of(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def _count_js_lines(body: str) -> int:
    return sum(1 for line in body.splitlines() if _JS_TOKEN_RE.search(line))


def _count_css_lines(body: str) -> int:
    n = 0
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(('/*', '*', '//')):
            continue
        if _CSS_LINE_RE.search(stripped):
            n += 1
    return n


def scan_inline_scripts(src_dir: Path, root: Path):
    """Inline ``<script>`` blocks whose body is hand-written JavaScript.

    External CDN includes (``<script src=...></script>`` with an empty body)
    and the thin config-injection wrapper are not flagged.
    """
    results = []
    for path in _src_files(src_dir):
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        for m in _SCRIPT_RE.finditer(text):
            attrs, body = m.group(1), m.group(2)
            if 'src=' in attrs.lower() and not body.strip():
                continue  # external include — allowed
            js_lines = _count_js_lines(body)
            if js_lines >= MIN_JS_LINES:
                results.append({
                    'file': _rel(path, root),
                    'line': _line_of(text, m.start()),
                    'end_line': _line_of(text, m.end()),
                    'js_lines': js_lines,
                })
    return results


def scan_inline_styles(src_dir: Path, root: Path):
    """Inline ``<style>`` blocks containing CSS authored in Python."""
    results = []
    for path in _src_files(src_dir):
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        for m in _STYLE_RE.finditer(text):
            css_lines = _count_css_lines(m.group(1))
            if css_lines >= MIN_CSS_LINES:
                results.append({
                    'file': _rel(path, root),
                    'line': _line_of(text, m.start()),
                    'end_line': _line_of(text, m.end()),
                    'css_lines': css_lines,
                })
    return results


def _covered_lines(text: str):
    """Set of 1-based line numbers inside any <script>/<style> block."""
    covered = set()
    for pattern in (_SCRIPT_RE, _STYLE_RE):
        for m in pattern.finditer(text):
            start = _line_of(text, m.start())
            end = _line_of(text, m.end())
            covered.update(range(start, end + 1))
    return covered


def scan_js_factories(src_dir: Path, root: Path):
    """Large runs of JavaScript built in a Python string with no <script> tag.

    Catches modules that assemble a JS fragment as a return value (e.g. a
    panel factory) without ever wrapping it in ``<script>`` tags, so the
    ``<script>`` scan above never sees it.  A short gap of non-JS lines is
    tolerated so blank lines / comments inside the run do not split it.
    """
    GAP_TOLERANCE = 2
    results = []
    for path in _src_files(src_dir):
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        covered = _covered_lines(text)
        lines = text.splitlines()

        run_start = None
        run_js = 0
        gap = 0
        for idx, line in enumerate(lines, 1):
            is_js = (idx not in covered) and bool(_JS_TOKEN_RE.search(line))
            if is_js:
                if run_start is None:
                    run_start = idx
                run_js += 1
                gap = 0
                run_end = idx
            elif run_start is not None:
                gap += 1
                if gap > GAP_TOLERANCE:
                    if run_js >= MIN_FACTORY_LINES:
                        results.append({
                            'file': _rel(path, root),
                            'line': run_start,
                            'end_line': run_end,
                            'js_lines': run_js,
                        })
                    run_start, run_js, gap = None, 0, 0
        if run_start is not None and run_js >= MIN_FACTORY_LINES:
            results.append({
                'file': _rel(path, root),
                'line': run_start,
                'end_line': run_end,
                'js_lines': run_js,
            })
    return results


def collect_all(src_dir: Path, root: Path) -> dict:
    scripts = scan_inline_scripts(src_dir, root)
    styles = scan_inline_styles(src_dir, root)
    factories = scan_js_factories(src_dir, root)
    flagged = {f['file'] for f in scripts + styles + factories}
    return {
        'scripts': scripts,
        'styles': styles,
        'factories': factories,
        'files_scanned': sum(1 for _ in _src_files(src_dir)),
        'files_flagged': len(flagged),
    }


def collect_all_repo(root: Path, scan_dirs=REPO_SCAN_DIRS) -> dict:
    """Run the embedded JS/CSS scan across all non-test source dirs under
    *root* (src/, app/, config/, tools/, docs/ + root-level files), merging the
    findings. The audit tooling excludes itself via ``_src_files``.

    This is the repo-wide counterpart to ``collect_all`` (single dir).
    """
    merged = {'scripts': [], 'styles': [], 'factories': [], 'files_scanned': 0}
    # Scan only the explicit non-test dirs — never `root` itself, whose rglob
    # would pull in tests/, .venv, .claude worktrees and the data symlink.
    seen_dirs = set()
    for d in scan_dirs:
        base = root / d
        if not base.is_dir():
            continue
        key = base.resolve()
        if key in seen_dirs:
            continue
        seen_dirs.add(key)
        part = collect_all(base, root)
        merged['scripts'].extend(part['scripts'])
        merged['styles'].extend(part['styles'])
        merged['factories'].extend(part['factories'])
        merged['files_scanned'] += part['files_scanned']
    flagged = {f['file'] for f in
               merged['scripts'] + merged['styles'] + merged['factories']}
    merged['files_flagged'] = len(flagged)
    return merged
