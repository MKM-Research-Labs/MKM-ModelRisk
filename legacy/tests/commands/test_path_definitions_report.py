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

"""Path-definition audit — zero-tolerance gate, scan logic, full-audit section.

Sits with the other audit-report tests (test_copyright_headers_report.py,
test_embedded_js_report.py, …) and runs under ``app.py test`` (which executes
``pytest tests/``).

Policy: every filesystem path definition must be housed in the ``config``
package.  ``TestPathDefinitionsGate`` is the enforcement gate — it fails if any
first-party module outside ``config`` hand-derives the project root or
hard-codes a ``data/`` path.  ``TestPathScanLogic`` pins the detect/skip
behaviour against synthetic input, and ``TestPathSection`` smoke-tests the
full-audit subsection builder.
"""

from pathlib import Path

from docs.models.full_audit.sections_tests import path_definitions as scanner

# tests/commands/test_path_definitions_report.py -> repo root
ROOT = Path(__file__).resolve().parents[2]


class TestPathDefinitionsGate:
    """Repo-wide zero-tolerance enforcement (runs under app.py test)."""

    def test_some_files_scanned(self):
        scan = scanner.scan_repo(ROOT)
        assert scan['scanned'] > 0

    def test_no_path_definitions_outside_config(self):
        scan = scanner.scan_repo(ROOT)
        findings = scan['findings']
        # Build a readable failure list grouped by file.
        if findings:
            lines = [
                f"  {f['file']}:{f['line']}  [{f['kind']}]  {f['snippet']}"
                for f in findings[:40]
            ]
            extra = '' if len(findings) <= 40 else f"\n  … +{len(findings) - 40} more"
            raise AssertionError(
                f"{len(findings)} path definition(s) found outside the config "
                f"package across {len(scan['files_with_findings'])} file(s).\n"
                "Every filesystem path must be obtained from a config accessor "
                "(config.get_project_root() / get_input_dir() / get_output_dir() "
                "/ get_results_dir()), not hand-derived or hard-coded.\n"
                + '\n'.join(lines) + extra
            )

    def test_allowlist_entries_are_minimal_and_present(self):
        """Every allowlisted file must still exist and actually contain a path
        definition — stale exemptions are not allowed to accumulate."""
        scan = scanner.scan_repo(ROOT)
        present = {a['file'] for a in scan['allowlisted']}
        for rel in scanner._ALLOWLIST:
            assert (ROOT / rel).exists(), f"allowlisted file missing: {rel}"
            assert rel in present, (
                f"allowlisted file no longer contains a path definition — "
                f"remove the exemption: {rel}"
            )


class TestPathScanLogic:
    """Pure detect/skip behaviour against synthetic input (no repo scan)."""

    def test_flags_root_walk_parents(self):
        f = scanner.scan_text('root = Path(__file__).resolve().parents[2]\n')
        assert [x['kind'] for x in f] == ['root_walk']

    def test_flags_root_walk_dirname(self):
        f = scanner.scan_text('R = os.path.dirname(os.path.dirname(__file__))\n')
        assert any(x['kind'] == 'root_walk' for x in f)

    def test_flags_data_literal(self):
        f = scanner.scan_text('OUT = "data/output"\n')
        assert [x['kind'] for x in f] == ['data_literal']

    def test_flags_data_segment(self):
        f = scanner.scan_text("p = root / 'data' / 'input'\n")
        assert [x['kind'] for x in f] == ['data_segment']

    def test_root_walk_takes_precedence_over_segment(self):
        # A single line that both root-walks and adds a data segment yields one
        # finding, tagged with the most specific kind.
        f = scanner.scan_text(
            'd = Path(__file__).resolve().parents[2] / "data" / "input"\n')
        assert [x['kind'] for x in f] == ['root_walk']

    def test_ignores_plain_file_attributes(self):
        # .name / .stem / bare Path(__file__) are not ancestor derivation.
        assert scanner.scan_text('n = Path(__file__).name\n') == []
        assert scanner.scan_text('s = Path(__file__).stem\n') == []

    def test_ignores_comments(self):
        assert scanner.scan_text('# uses data/output via Path(__file__).parent\n') == []

    def test_ignores_docstring_interior(self):
        text = (
            'def f():\n'
            '    """Loads data/output from Path(__file__).parents[1]."""\n'
            '    return 1\n'
        )
        assert scanner.scan_text(text) == []

    def test_unrelated_paths_not_flagged(self):
        # URLs, non-owned dirs and metadata strings are out of scope.
        assert scanner.scan_text('URL = "https://example.com/data/output"\n') == []
        assert scanner.scan_text('s = "static/js/app.js"\n') == []


class TestPathSection:
    """The full-audit subsection builder (4.3) renders without error."""

    def test_section_builder_returns_flowables(self):
        from docs.models.full_audit.sections_tests import _build_path_definitions
        from docs.models.full_audit.styles import _styles
        elems = _build_path_definitions(_styles())
        assert isinstance(elems, list) and len(elems) > 0
