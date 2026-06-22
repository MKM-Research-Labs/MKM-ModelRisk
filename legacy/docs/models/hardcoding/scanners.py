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

"""Source-tree scan passes for the hard-coding parameter audit."""

import ast
import re
from collections import defaultdict
from pathlib import Path


def _src_files(src_dir: Path):
    for p in sorted(src_dir.rglob('*.py')):
        if '__pycache__' in p.parts:
            continue
        if p.name == '__init__.py':
            continue
        yield p


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def _parse_module_constants(path: Path):
    """Return (name, value, lineno) for every module-level assignment."""
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError:
        return []
    results = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            value = _extract_value(node.value)
            if value is not None:
                results.append((target.id, value, node.lineno))
    return results


def _extract_value(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _extract_value(node.operand)
        if isinstance(inner, (int, float)):
            return -inner
    if isinstance(node, ast.List):
        items = [_extract_value(el) for el in node.elts]
        if all(i is not None for i in items):
            return items
    if isinstance(node, ast.Tuple):
        items = [_extract_value(el) for el in node.elts]
        if all(i is not None for i in items):
            return tuple(items)
    if isinstance(node, ast.Dict):
        keys = [_extract_value(k) for k in node.keys]
        vals = [_extract_value(v) for v in node.values]
        if all(k is not None for k in keys) and all(v is not None for v in vals):
            return dict(zip(keys, vals))
    return None


def _is_allcaps(name: str) -> bool:
    return name == name.upper() and '_' in name and len(name) > 3


def _is_numeric_or_aggregate(value) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if isinstance(value, (list, tuple)):
        return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    if isinstance(value, dict):
        return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value.values())
    return False


# Constants that are mathematical precision values rather than domain
# parameters — they may legitimately live close to the formula that uses them.
_PRECISION_CONSTANTS = {
    'LOG_EPS',    # numerical underflow guard in log transform
    'BUMP_1BP',   # 1 bp bump for numerical differentiation
    'MIN_SLOPE',  # hydraulic minimum slope tied to Manning formula
}


def scan_duplicate_constants(src_dir: Path, root: Path):
    """Constants with the same ALL_CAPS name defined in 2+ src/ files."""
    by_name = defaultdict(list)
    for path in _src_files(src_dir):
        if path.name == 'config.py':
            continue
        for name, value, lineno in _parse_module_constants(path):
            if _is_allcaps(name) and _is_numeric_or_aggregate(value):
                by_name[name].append((_rel(path, root), lineno, value))

    results = []
    for name, locs in sorted(by_name.items()):
        if len(locs) > 1:
            results.append({'name': name, 'count': len(locs), 'locations': locs})
    return results


def scan_allcaps_outside_config(src_dir: Path, root: Path):
    """Module-level ALL_CAPS numeric constants in non-config src/ files."""
    results = []
    for path in _src_files(src_dir):
        if path.name == 'config.py':
            continue
        rel = _rel(path, root)
        for name, value, lineno in _parse_module_constants(path):
            if not _is_allcaps(name):
                continue
            if not _is_numeric_or_aggregate(value):
                continue
            is_precision = name in _PRECISION_CONSTANTS
            results.append({
                'file': rel, 'line': lineno, 'name': name,
                'value': repr(value)[:60], 'precision_ok': is_precision,
            })
    return results


def scan_infrastructure_literals(src_dir: Path, root: Path):
    """Hardcoded IP addresses or the server port (5013) in src/ files."""
    IP_RE = re.compile(
        r"'(127\.0\.0\.1|0\.0\.0\.0|localhost)'"
        r'|"(127\.0\.0\.1|0\.0\.0\.0|localhost)"'
    )
    PORT_RE = re.compile(r'\b5013\b')

    results = []
    for path in _src_files(src_dir):
        if path.name == 'config.py':
            continue
        rel = _rel(path, root)
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if IP_RE.search(line):
                results.append({'file': rel, 'line': i, 'kind': 'host',
                                 'snippet': stripped[:80]})
            elif PORT_RE.search(line):
                results.append({'file': rel, 'line': i, 'kind': 'port',
                                 'snippet': stripped[:80]})
    return results


def scan_inline_simulation_literals(src_dir: Path, root: Path):
    """Simulation parameters assigned as bare numeric literals (not constants)."""
    # Only flag non-trivial values (>= 2) to avoid zero/unit defaults.
    PARAM_RE = re.compile(
        r'\b(n_hours|num_hours|n_frames|n_days|n_steps'
        r'|duration_h|window_h|horizon_h'
        r'|top_n|max_n|top_storms|max_storms'
        r')\s*=\s*([2-9]\d*|\d{2,})'
    )

    results = []
    for path in _src_files(src_dir):
        if path.name == 'config.py':
            continue
        rel = _rel(path, root)
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            m = PARAM_RE.search(line)
            if m:
                results.append({'file': rel, 'line': i,
                                 'param': m.group(1), 'value': m.group(2),
                                 'snippet': stripped[:80]})
    return results


def collect_all(src_dir: Path, root: Path) -> dict:
    return {
        'duplicates':   scan_duplicate_constants(src_dir, root),
        'allcaps':      scan_allcaps_outside_config(src_dir, root),
        'infra':        scan_infrastructure_literals(src_dir, root),
        'inline':       scan_inline_simulation_literals(src_dir, root),
        'files_scanned': sum(1 for _ in _src_files(src_dir)),
    }
