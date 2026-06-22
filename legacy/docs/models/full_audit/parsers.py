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

"""JUnit / coverage XML parsers and git SHA lookup for the full audit report."""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from ._constants import _root


def _parse_junit(junit_path: Path) -> dict:
    """Parse JUnit XML into summary dict."""
    result = {
        'total': 0, 'passed': 0, 'failed': 0,
        'errors': 0, 'skipped': 0, 'time_s': 0.0,
        'by_package': {},
    }
    if not junit_path.exists():
        return result

    tree = ET.parse(str(junit_path))
    root = tree.getroot()

    # Handle both <testsuites> wrapper and bare <testsuite>
    suites = root.findall('.//testsuite')
    if not suites and root.tag == 'testsuite':
        suites = [root]

    pkg_counts: dict = defaultdict(lambda: {'total': 0, 'fail': 0, 'skip': 0})

    for suite in suites:
        total = int(suite.get('tests', 0))
        fail = int(suite.get('failures', 0))
        err = int(suite.get('errors', 0))
        skip = int(suite.get('skipped', 0))
        t = float(suite.get('time', 0))

        result['total'] += total
        result['failed'] += fail + err
        result['skipped'] += skip
        result['time_s'] += t

        # Package from test classnames
        for tc in suite.findall('testcase'):
            classname = tc.get('classname', '')
            # e.g. "tests.models.hazard.TestGEV" → "models.hazard"
            parts = classname.split('.')
            if len(parts) >= 3 and parts[0] == 'tests':
                pkg = parts[1]
            elif len(parts) >= 2:
                pkg = parts[0]
            else:
                pkg = 'other'

            is_skip = tc.find('skipped') is not None
            is_fail = (tc.find('failure') is not None or
                       tc.find('error') is not None)

            pkg_counts[pkg]['total'] += 1
            if is_fail:
                pkg_counts[pkg]['fail'] += 1
            if is_skip:
                pkg_counts[pkg]['skip'] += 1

    result['passed'] = result['total'] - result['failed'] - result['skipped']
    result['by_package'] = dict(pkg_counts)
    return result


def _parse_coverage(cov_path: Path) -> dict:
    """Parse coverage.xml into summary + per-package breakdown."""
    result = {
        'line_rate': 0.0,
        'lines_valid': 0,
        'lines_covered': 0,
        'by_package': [],   # list of (pkg_name, rate, valid, covered)
    }
    if not cov_path.exists():
        return result

    tree = ET.parse(str(cov_path))
    root = tree.getroot()

    result['line_rate'] = float(root.get('line-rate', 0))
    result['lines_valid'] = int(root.get('lines-valid', 0))
    result['lines_covered'] = int(root.get('lines-covered', 0))

    pkg_rows = []
    for pkg in root.findall('.//package'):
        name = pkg.get('name', '').lstrip('.')
        if not name:
            continue
        rate = float(pkg.get('line-rate', 0))
        valid = sum(int(c.get('lines-valid', 0))
                    for c in pkg.findall('classes/class'))
        covered = sum(int(c.get('lines-covered', 0))
                      for c in pkg.findall('classes/class'))
        if valid == 0:
            # Fall back: count lines from class elements
            valid = sum(len(c.findall('.//line')) for c in pkg.findall('classes/class'))
            covered = sum(
                sum(1 for ln in c.findall('.//line') if ln.get('hits', '0') != '0')
                for c in pkg.findall('classes/class')
            )
        if valid > 0:
            pkg_rows.append((name, rate * 100, valid, covered))

    pkg_rows.sort(key=lambda x: x[1])   # ascending by coverage rate
    result['by_package'] = pkg_rows
    return result


def _git_sha() -> str:
    import subprocess
    try:
        r = subprocess.run(['git', 'rev-parse', 'HEAD'],
                           capture_output=True, text=True,
                           cwd=str(_root), timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()[:12]
    except Exception:
        pass
    return 'unknown'
