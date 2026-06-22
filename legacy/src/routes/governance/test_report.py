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

"""
Test report routes — run the test suite and serve structured failure data.

Endpoints:
  POST /governance/test-report/run      Run pytest, save results to audit dir.
  GET  /governance/test-report/summary  Return most recent saved results.
  GET  /governance/test-report/output   Return live stdout buffer while running.
"""

import json
import os
import subprocess
import sys
import threading
from datetime import datetime

from flask import jsonify

from . import governance_bp
from ._constants import AUDIT_REPORTS_DIR

_REPORT_FILE = os.path.join(AUDIT_REPORTS_DIR, "test_failures_report.json")
# Web-UI test-run log is not part of the `app.py test` audit artefacts —
# keep it out of the audit root, under audit/archive/.
_LOG_FILE    = os.path.join(AUDIT_REPORTS_DIR, "archive", "test_run.log")
_LOCK = threading.Lock()
_running = False
_output_lines = []          # live stdout buffer
_output_lock = threading.Lock()


def _append_output(line: str):
    with _output_lock:
        _output_lines.append(line)
        # Keep last 2000 lines to avoid unbounded growth
        if len(_output_lines) > 2000:
            del _output_lines[:200]


def _stream_proc(proc):
    """Read stdout from a subprocess line-by-line into the live buffer."""
    for raw in proc.stdout:
        line = raw.rstrip('\n')
        _append_output(line)
    proc.wait()


def _run_and_save():
    """Run full audit evidence package and save structured results to audit dir."""
    global _running
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    collector_script = os.path.join(project_root, '_run_test_report.py')

    script = r"""
import sys, json, os
sys.path.insert(0, '.')
sys.path.insert(0, 'src')
from docs.models.test_results.generator.collector import TestResultCollector
import pytest
from datetime import datetime

collector = TestResultCollector()
pytest.main(['tests/', '-q', '--tb=short', '--no-header'], plugins=[collector])

results   = collector.results
failures  = [r for r in results if r['outcome'] == 'failed']
passed    = [r for r in results if r['outcome'] == 'passed']
skipped   = [r for r in results if r['outcome'] == 'skipped']

report = {
    'generated_at': datetime.now().isoformat(),
    'summary': {'total': len(results), 'passed': len(passed),
                'failed': len(failures), 'skipped': len(skipped)},
    'failures': failures,
}

out_path = sys.argv[1]
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w') as f:
    json.dump(report, f, indent=2)
print(f'Report: {len(failures)} failures / {len(results)} tests')
"""
    with open(collector_script, 'w') as f:
        f.write(script)

    try:
        os.makedirs(AUDIT_REPORTS_DIR, exist_ok=True)
        with _output_lock:
            _output_lines.clear()

        _append_output('=' * 60)
        _append_output('MKM Research Labs — Audit Evidence Package')
        _append_output('=' * 60)
        _append_output(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        _append_output('')

        # 1. Full audit: junit.xml, coverage, PDFs
        _append_output('Step 1/2  Running full test suite + generating audit PDFs ...')
        _append_output('  (pytest + coverage + test_report.pdf + code_analysis.pdf + code_duplication.pdf)')
        _append_output('')
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        proc1 = subprocess.Popen(
            [sys.executable, '-u', 'app.py', 'test', '--audit', '--pdf'],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        _stream_proc(proc1)

        _append_output('')
        _append_output('Step 2/2  Building failure report for UI panel ...')
        _append_output('')

        # 2. Failure collector → test_failures_report.json
        proc2 = subprocess.Popen(
            [sys.executable, '-u', collector_script, _REPORT_FILE],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        _stream_proc(proc2)

        _append_output('')
        _append_output('=' * 60)
        _append_output('Audit run complete.')
        _append_output('=' * 60)

    except Exception as exc:
        _append_output(f'ERROR: {exc}')
    finally:
        if os.path.isfile(collector_script):
            os.remove(collector_script)
        # Save full terminal output to log file in audit directory
        try:
            with _output_lock:
                lines = list(_output_lines)
            os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
            with open(_LOG_FILE, 'w') as f:
                f.write('\n'.join(lines))
        except Exception:
            pass
        _running = False


@governance_bp.route("/governance/test-report/run", methods=["POST"])
def run_test_report():
    """Trigger a pytest run in the background and save structured results."""
    global _running
    with _LOCK:
        if _running:
            return jsonify({"status": "running",
                            "message": "Test run already in progress."}), 202
        _running = True

    t = threading.Thread(target=_run_and_save, daemon=True)
    t.start()
    return jsonify({"status": "started",
                    "message": "Test run started."}), 202


@governance_bp.route("/governance/test-report/output", methods=["GET"])
def test_report_output():
    """Return live stdout buffer — polled by the UI terminal popup."""
    with _output_lock:
        lines = list(_output_lines)
    return jsonify({
        "running": _running,
        "lines": lines,
    })


@governance_bp.route("/governance/test-report/summary", methods=["GET"])
def test_report_summary():
    """Return the most recent test report: summary + failures."""
    if not os.path.isfile(_REPORT_FILE):
        return jsonify({
            "status": "not_found",
            "running": _running,
        })

    with open(_REPORT_FILE) as f:
        data = json.load(f)

    return jsonify({
        "status": "ok",
        "running": _running,
        "generated_at": data.get("generated_at", ""),
        "summary": data.get("summary", {}),
        "failures": data.get("failures", []),
    })
