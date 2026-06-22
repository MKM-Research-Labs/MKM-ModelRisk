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

"""Locate and run jscpd, returning its parsed JSON report."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from ._paths import SRC_DIR, MIN_LINES, MIN_TOKENS


def _find_node_env() -> tuple[str, dict]:
    """Locate jscpd binary and return (path, env) with node on PATH.

    Python venvs and pyenv can strip nvm/node from PATH, so we search
    common locations and ensure the env passed to subprocess includes
    the directory containing both node and jscpd.
    """
    import os
    env = os.environ.copy()

    found = shutil.which('jscpd')
    if found and shutil.which('node'):
        return found, env

    # Search common nvm install locations (newest version first)
    home = Path.home()
    for nvm_bin in sorted(home.glob('.nvm/versions/node/*/bin'), reverse=True):
        candidate = nvm_bin / 'jscpd'
        if candidate.exists():
            env['PATH'] = str(nvm_bin) + os.pathsep + env.get('PATH', '')
            return str(candidate), env

    # Try npm global bin directory
    for npm_cmd in ['npm', '/usr/local/bin/npm', '/opt/homebrew/bin/npm']:
        try:
            result = subprocess.run(
                [npm_cmd, 'root', '-g'], capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                bin_dir = Path(result.stdout.strip()).parent / 'bin'
                npm_bin = bin_dir / 'jscpd'
                if npm_bin.exists():
                    env['PATH'] = str(bin_dir) + os.pathsep + env.get('PATH', '')
                    return str(npm_bin), env
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return 'jscpd', env  # fall back


def _run_jscpd() -> dict:
    """Run jscpd and return parsed JSON report."""
    jscpd_bin, node_env = _find_node_env()
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            jscpd_bin, str(SRC_DIR),
            '--format', 'python,javascript',
            '--min-lines', str(MIN_LINES),
            '--min-tokens', str(MIN_TOKENS),
            '--reporters', 'json',
            '--output', tmpdir,
            '--ignore', '**/node_modules/**,**/__pycache__/**,**/*.pyc',
            '--silent',
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                env=node_env)
        report_path = Path(tmpdir) / 'jscpd-report.json'
        if report_path.exists():
            with open(report_path) as f:
                return json.load(f)
        raise RuntimeError(
            f"jscpd did not produce report.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


def _jscpd_version() -> str:
    try:
        jscpd_bin, node_env = _find_node_env()
        r = subprocess.run([jscpd_bin, '--version'], capture_output=True, text=True,
                           timeout=5, env=node_env)
        return r.stdout.strip() or r.stderr.strip() or '?'
    except Exception:
        return '?'
