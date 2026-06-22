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

"""Copyright-header audit — self-heal, logic and full-audit section tests.

Sits with the other audit-report tests (test_embedded_js_report.py, …).

``TestCopyrightHeadersRepo`` runs the header fixer across the whole repository:
any ``.py``/``.js`` file whose header is missing or differs from
``docs/shared/copyright.py`` is rewritten in place, then the test asserts every
file is compliant.  It repairs before asserting, so it is self-healing — the
rewrite simply surfaces as a git diff, which is the signal a header was wrong.

``TestCopyrightHeaderLogic`` pins the detect/replace/insert behaviour with
synthetic input (``tmp``-style, no repo mutation), and ``TestCopyrightSection``
smoke-tests the full-audit subsection builder.
"""

from pathlib import Path

from docs.models.full_audit.sections_tests import copyright_headers as scanners

# tests/commands/test_copyright_headers_report.py -> repo root
ROOT = Path(__file__).resolve().parents[2]


class TestCopyrightHeadersRepo:
    """Repo-wide self-heal + compliance assertion (runs under app.py test)."""

    def test_canonical_header_loads(self):
        canon = scanners.load_canonical_py(ROOT)
        assert len(canon) >= 19
        assert 'MKM Research Labs' in canon[0]
        assert 'All rights reserved' in canon[0]

    def test_all_headers_compliant_after_fix(self):
        findings = scanners.fix_repo(ROOT, apply=True)
        assert findings['scanned'] > 0
        # Every fix was verified compliant immediately after the rewrite...
        assert all(r['now_compliant'] for r in findings['fixed'])
        # ...and nothing remains non-compliant.
        assert findings['remaining'] == [], (
            f"{len(findings['remaining'])} file(s) could not be made compliant: "
            f"{[r['file'] for r in findings['remaining'][:10]]}"
        )

    def test_fix_is_idempotent(self):
        scanners.fix_repo(ROOT, apply=True)
        again = scanners.fix_repo(ROOT, apply=True)
        assert again['fixed'] == []
        assert again['remaining'] == []


class TestCopyrightHeaderLogic:
    """Pure detect/replace/insert behaviour against synthetic input."""

    def test_compliant_file_is_left_alone(self):
        canon = scanners.canonical_lines(ROOT, '.py')
        text = '\n'.join(canon) + '\n\nimport os\n'
        assert scanners.is_compliant(text, canon)
        new_text, old = scanners.fix_text(text, canon, '.py')
        assert new_text is None and old is None

    def test_inserts_header_when_missing(self):
        canon = scanners.canonical_lines(ROOT, '.py')
        new_text, old = scanners.fix_text('import os\n', canon, '.py')
        assert new_text is not None
        assert scanners.is_compliant(new_text, canon)
        assert 'import os' in new_text
        assert old == ''  # nothing replaced — header was simply absent

    def test_replaces_wrong_header(self):
        canon = scanners.canonical_lines(ROOT, '.py')
        wrong = (
            '# Copyright (c) 1999 Someone Else. All rights reserved.\n'
            '# (see LICENSE for terms)\n'
            '\n'
            'def f():\n'
            '    return 1\n'
        )
        new_text, old = scanners.fix_text(wrong, canon, '.py')
        assert new_text is not None
        assert scanners.is_compliant(new_text, canon)
        assert 'Someone Else' not in new_text   # old header gone
        assert 'def f()' in new_text            # code preserved
        assert 'Someone Else' in old            # recorded the wrong header

    def test_preserves_shebang(self):
        canon = scanners.canonical_lines(ROOT, '.py')
        new_text, _ = scanners.fix_text(
            '#!/usr/bin/env python3\nimport os\n', canon, '.py')
        assert new_text.startswith('#!/usr/bin/env python3\n')
        assert scanners.is_compliant(new_text, canon)

    def test_keeps_non_license_leading_comment(self):
        canon = scanners.canonical_lines(ROOT, '.py')
        new_text, old = scanners.fix_text(
            '# TODO: refactor this module\nimport os\n', canon, '.py')
        assert scanners.is_compliant(new_text, canon)
        assert 'TODO: refactor' in new_text     # ordinary comment preserved
        assert old == ''                          # not treated as a license block

    def test_js_header_uses_slash_prefix(self):
        canon = scanners.canonical_lines(ROOT, '.js')
        assert canon[0].startswith('// Copyright')
        new_text, _ = scanners.fix_text('const x = 1;\n', canon, '.js')
        assert new_text.startswith('// Copyright')
        assert scanners.is_compliant(new_text, canon)
        assert 'const x = 1;' in new_text

    def test_empty_file_gets_header(self):
        canon = scanners.canonical_lines(ROOT, '.py')
        new_text, _ = scanners.fix_text('', canon, '.py')
        assert scanners.is_compliant(new_text, canon)


class TestCopyrightSection:
    """The full-audit subsection builder (4.2) renders without error."""

    def test_section_builder_returns_flowables(self):
        from docs.models.full_audit.sections_tests import _build_copyright_headers
        from docs.models.full_audit.styles import _styles
        elems = _build_copyright_headers(_styles())
        assert isinstance(elems, list) and len(elems) > 0
