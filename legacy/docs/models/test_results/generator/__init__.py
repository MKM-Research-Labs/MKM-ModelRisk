#!/usr/bin/env python3

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
Generate LaTeX test results documentation for model governance.

Runs model-related pytest tests programmatically and produces:
  - Per-model LaTeX fragments  (<model_dir>/test_results.tex)
  - Standalone full report      (test_results/test_report.tex)

Usage:
    python -m docs.models.test_results.generator
    python -m docs.models.test_results.generator --pdf
    python -m docs.models.test_results.generator --model MP GH
"""

import argparse
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

import pytest

from .models import TEST_MODEL_MAP, MODEL_INFO, MODEL_ALIASES
from .collector import TestResultCollector
from .assertions import build_criteria_cache
from .history import update_history
from .report import write_model_fragment, generate_full_report
from .compiler import compile_model_pdf

_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def _parse_e2e_junit(junit_path):
    """Parse a JUnit XML file from E2E tests into collector-compatible dicts."""
    results = []
    if not junit_path or not os.path.exists(junit_path):
        return results

    tree = ET.parse(junit_path)
    root = tree.getroot()

    for tc in root.findall('.//testcase'):
        name = tc.get('name', '')
        classname = tc.get('classname', '')
        time_s = float(tc.get('time', '0') or '0')

        failure_el = tc.find('failure')
        if failure_el is None:
            failure_el = tc.find('error')
        skip_el = tc.find('skipped')
        if failure_el is not None:
            outcome = 'failed'
            longrepr = failure_el.get('message', '') or (failure_el.text or '')[:500]
        elif skip_el is not None:
            outcome = 'skipped'
            longrepr = ''
        else:
            outcome = 'passed'
            longrepr = ''

        # Build a nodeid compatible with the rest of the report
        file_part = classname.replace('.', '/') + '.py' if classname else 'tests/e2e/unknown.py'
        nodeid = f'{file_part}::{name}'

        results.append({
            'nodeid': nodeid,
            'file': file_part,
            'class': '',
            'name': name,
            'model_id': 'E2E-ALL',
            'outcome': outcome,
            'duration': round(time_s, 4),
            'longrepr': longrepr,
            'description': '',
            'docstring': '',
            'params': '',
        })

    return results


def run_tests(model_filter=None):
    """Run tests and return collected results."""
    test_root = os.path.join(_project_root, 'tests')

    if model_filter:
        target_ids = set()
        for alias in model_filter:
            alias_upper = alias.upper()
            if alias_upper in MODEL_ALIASES:
                target_ids.add(MODEL_ALIASES[alias_upper])
            elif alias_upper.startswith('MKM-'):
                target_ids.add(alias_upper)
            else:
                for full_id in MODEL_INFO:
                    if alias_upper in full_id:
                        target_ids.add(full_id)

        test_paths = []
        for test_file, model_id in TEST_MODEL_MAP.items():
            if model_id in target_ids:
                full_path = os.path.join(_project_root, test_file)
                if os.path.exists(full_path):
                    test_paths.append(full_path)

        if not test_paths:
            print(f'No test files found for models: {model_filter}')
            print(f'Available aliases: {", ".join(sorted(MODEL_ALIASES.keys()))}')
            return [], 0
    else:
        test_paths = [test_root]

    collector = TestResultCollector()

    # Ignore test files that depend on optional heavy libraries
    # (geopandas, etc.) which may not be installed in all environments.
    ignore_dirs = [
        os.path.join(test_root, 'visual', 'core', 'map_builder'),
        os.path.join(test_root, 'visual', 'core', 'visualizer'),
        os.path.join(test_root, 'visual', 'integration'),
        os.path.join(test_root, 'visual', 'layer'),
        os.path.join(test_root, 'visual', 'phase'),
        os.path.join(test_root, 'visual', 'popup'),
        os.path.join(test_root, 'visual', 'utils'),
        os.path.join(test_root, 'models', 'floodrisk', 'risk_analytics.py'),
        os.path.join(test_root, 'models', 'floodrisk', 'risk_visualization.py'),
        os.path.join(test_root, 'models', 'prs', 'prs_pricing.py'),
    ]
    ignore_args = []
    for p in ignore_dirs:
        if os.path.exists(p):
            ignore_args.extend(['--ignore', p])

    print('Running tests...\n')
    start = time.time()
    exit_code = pytest.main(
        [*test_paths, *ignore_args, '-v', '--tb=short', '-q', '--no-header'],
        plugins=[collector],
    )
    duration = time.time() - start
    print(f'\nTests completed in {duration:.2f}s (exit code: {exit_code})')

    return collector.results, duration


def main():
    parser = argparse.ArgumentParser(
        description='Generate LaTeX test results documentation')
    parser.add_argument('--pdf', action='store_true',
                        help='Compile LaTeX to PDF')
    parser.add_argument('--model', nargs='+',
                        help='Run only for specific model(s) (e.g. MP GH FC)')
    parser.add_argument('--git-sha', dest='git_sha', default=None,
                        help='Git commit SHA to embed in report')
    parser.add_argument('--coverage-pct', dest='coverage_pct', type=float,
                        default=None,
                        help='Line coverage percentage to embed in report')
    parser.add_argument('--e2e-junit', dest='e2e_junit', default=None,
                        help='Path to E2E JUnit XML to include in report')
    args = parser.parse_args()

    print('=' * 60)
    print('MKM Research Labs — Model Test Results Generator')
    print('=' * 60)
    print()

    results, duration = run_tests(args.model)

    # Merge E2E results from pre-collected JUnit XML (E2E tests run
    # separately via Playwright and cannot be collected by pytest.main).
    if args.e2e_junit:
        e2e_results = _parse_e2e_junit(args.e2e_junit)
        if e2e_results:
            results.extend(e2e_results)
            n_e2e = len(e2e_results)
            n_pass = sum(1 for r in e2e_results if r['outcome'] == 'passed')
            print(f'\nMerged {n_e2e} E2E browser test results '
                  f'({n_pass} passed) from {args.e2e_junit}')

    if not results:
        print('\nNo test results collected.')
        return

    run_timestamp = datetime.now()

    by_model = defaultdict(list)
    for r in results:
        by_model[r['model_id']].append(r)

    print(f'\nCollected {len(results)} test results across '
          f'{len(by_model)} model groups.\n')

    criteria_cache = build_criteria_cache(results)
    history = update_history(by_model, run_timestamp)

    print('Writing per-model LaTeX fragments:')
    for model_id, model_results in sorted(by_model.items()):
        info = MODEL_INFO.get(model_id, {'name': model_id})
        n_pass = sum(1 for r in model_results if r['outcome'] == 'passed')
        n_fail = sum(1 for r in model_results if r['outcome'] == 'failed')
        status = 'ALL PASS' if n_fail == 0 else f'{n_fail} FAILED'
        print(f'  [{model_id}] {info["name"]}: '
              f'{len(model_results)} tests, {status}')
        write_model_fragment(model_id, model_results, criteria_cache, history)

    print('\nGenerating full report:')
    report_path = generate_full_report(
        results, run_timestamp, duration, criteria_cache,
        git_sha=args.git_sha, coverage_pct=args.coverage_pct)

    if args.pdf:
        print('\nCompiling LaTeX to PDF...')

        print('\n  Per-model PDFs:')
        for model_id in sorted(by_model.keys()):
            pdf_path = compile_model_pdf(model_id, run_timestamp)
            if pdf_path:
                size_kb = os.path.getsize(pdf_path) / 1024
                print(f'    {model_id}: {pdf_path} ({size_kb:.1f} KB)')

        print('\n  Full report:')
        report_dir = os.path.dirname(report_path)
        try:
            for _ in range(2):
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode',
                     '-output-directory', report_dir, report_path],
                    capture_output=True, cwd=report_dir,
                    timeout=60,
                )
            pdf_path = report_path.replace('.tex', '.pdf')
            if os.path.exists(pdf_path):
                size_kb = os.path.getsize(pdf_path) / 1024
                print(f'    {pdf_path} ({size_kb:.1f} KB)')
            else:
                print('    PDF compilation failed. Check LaTeX log.')
                if result.stdout:
                    log = result.stdout.decode('latin-1', errors='replace')
                    for line in log.strip().split('\n')[-20:]:
                        print(f'      {line}')
        except FileNotFoundError:
            print('    pdflatex not found. Install TeX Live to compile PDFs.')
        except subprocess.TimeoutExpired:
            print('    pdflatex timed out.')

    print('\nDone.')


if __name__ == '__main__':
    main()
