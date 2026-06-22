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

"""Data-access audit — zero-tolerance DB-access gate + tracked file-I/O report.

Sits with the other audit-report tests (test_path_definitions_report.py,
test_copyright_headers_report.py, …) and runs under ``app.py test``.

Policy: **all database access goes through the one ``src/database`` utility
package.** ``TestDataAccessGate`` is the enforcement gate — it fails if any
first-party module outside ``src/database`` contains raw SQL, a cursor
``.execute(``, a SQL-driver/ORM import, or a connection handle. It is green by
construction today (no Postgres backend exists yet) and must stay green as the
backend lands inside its private modules.

``TestDataAccessReport`` surfaces the **non-gating** direct-file-I/O backlog —
the un-migrated readers that still touch ``data/input`` directly — so its size
is visible but never fails CI. ``TestDataAccessScanLogic`` pins detect/skip
behaviour, and ``TestDataAccessSection`` smoke-tests the report builder.
"""

from pathlib import Path

from docs.models.full_audit.sections_tests import data_access as scanner

# tests/commands/test_data_access_report.py -> repo root
ROOT = Path(__file__).resolve().parents[2]


class TestDataAccessGate:
    """Repo-wide zero-tolerance enforcement of the DB-access policy."""

    def test_some_files_scanned(self):
        scan = scanner.scan_repo(ROOT)
        assert scan['scanned'] > 0

    def test_no_db_access_outside_database(self):
        scan = scanner.scan_repo(ROOT)
        findings = scan['db_access_findings']
        if findings:
            files = sorted({f['file'] for f in findings})
            lines = [
                f"  {f['file']}:{f['line']}  [{f['kind']}]  {f['snippet']}"
                for f in findings[:40]
            ]
            extra = '' if len(findings) <= 40 else f"\n  … +{len(findings) - 40} more"
            raise AssertionError(
                f"{len(findings)} database-access finding(s) outside src/database "
                f"across {len(files)} file(s).\n"
                "All SQL / ORM / driver imports / connection+cursor handles must "
                "live in the src/database package; every other module accesses "
                "data through the database public API (database.get_*/save_*).\n"
                + '\n'.join(lines) + extra
            )

    def test_allowlist_entries_are_minimal_and_present(self):
        """Every allowlisted file must still exist and actually contain a
        db-access finding — stale exemptions are not allowed to accumulate."""
        scan = scanner.scan_repo(ROOT)
        present = {a['file'] for a in scan['allowlisted']}
        for rel in scanner._ALLOWLIST:
            assert (ROOT / rel).exists(), f"allowlisted file missing: {rel}"
            assert rel in present, (
                f"allowlisted file no longer contains a db-access finding — "
                f"remove the exemption: {rel}"
            )


class TestDataAccessReport:
    """The direct-file-I/O migration backlog is tracked, not gated."""

    def test_file_io_backlog_is_reported(self):
        """The scan reports a file-I/O backlog (a list of files); it never fails
        the build. This documents the remaining JSON->repository migration."""
        scan = scanner.scan_repo(ROOT)
        assert isinstance(scan['file_io_files'], list)
        # Visible in -s output; intentionally non-asserting on the count.
        print(f"\n[data-access] direct file-I/O backlog: "
              f"{len(scan['file_io_files'])} file(s) outside src/database still "
              f"read/write the data tree directly.")

    def test_backlog_excludes_sanctioned_and_tests(self):
        scan = scanner.scan_repo(ROOT)
        for rel in scan['file_io_files']:
            assert not rel.startswith('src/database/'), rel
            assert not rel.startswith('tests/'), rel


class TestDataAccessScanLogic:
    """Pure detect/skip behaviour against synthetic input (no repo scan)."""

    def test_flags_raw_sql_select(self):
        f = scanner.scan_text('q = "SELECT id FROM port_artifact WHERE x = 1"\n')
        assert [x['kind'] for x in f['db_access']] == ['sql']

    def test_flags_insert_into(self):
        f = scanner.scan_text('cur = "INSERT INTO artifact (k) VALUES (1)"\n')
        assert any(x['kind'] == 'sql' for x in f['db_access'])

    def test_flags_execute(self):
        f = scanner.scan_text('cursor.execute(sql, params)\n')
        assert [x['kind'] for x in f['db_access']] == ['execute']

    def test_flags_driver_import(self):
        f = scanner.scan_text('import psycopg2\n')
        assert [x['kind'] for x in f['db_access']] == ['driver_import']

    def test_flags_sqlalchemy_from_import(self):
        f = scanner.scan_text('from sqlalchemy import create_engine\n')
        assert any(x['kind'] == 'driver_import' for x in f['db_access'])

    def test_flags_connection_handle(self):
        f = scanner.scan_text('engine = create_engine(url)\n')
        assert [x['kind'] for x in f['db_access']] == ['connection']

    def test_ignores_sql_words_in_prose_comment(self):
        f = scanner.scan_text('# select the right row from the cache, then update\n')
        assert f['db_access'] == []

    def test_ignores_identifier_with_sql_word(self):
        f = scanner.scan_text('delete_from_cache(key)\n')
        assert f['db_access'] == []

    def test_skips_docstring_interior(self):
        text = '"""\nExample: SELECT x FROM y; cursor.execute(q)\n"""\n'
        assert scanner.scan_text(text)['db_access'] == []

    def test_file_io_only_with_data_context(self):
        # open() alone (no data-tree reference) is not backlog
        assert scanner.scan_text('with open(path) as f:\n    pass\n')['file_io'] == []
        # open() in a file that references the data tree IS backlog
        text = 'p = config.get_input_dir() / "x.json"\nwith open(p) as f:\n    pass\n'
        assert len(scanner.scan_text(text)['file_io']) == 1

    def test_flags_json_load_and_glob_with_context(self):
        text = 'd = config.get_input_dir()\njson.load(open(d / "a.json"))\nd.glob("*.json")\n'
        kinds = [x['kind'] for x in scanner.scan_text(text)['file_io']]
        assert kinds == ['file_io', 'file_io']


class TestDataAccessScanRepo:
    """scan_repo behaviour against a synthetic tree (the repo itself is green,
    so the with-findings + edge-case branches need explicit exercise)."""

    def test_finds_synthetic_db_access(self, tmp_path):
        (tmp_path / "bad.py").write_text('q = "SELECT x FROM y"\ncursor.execute(q)\n')
        scan = scanner.scan_repo(tmp_path)
        kinds = {f['kind'] for f in scan['db_access_findings']}
        assert {'sql', 'execute'} <= kinds

    def test_allowlisted_file_is_exempt(self, tmp_path, monkeypatch):
        (tmp_path / "bad.py").write_text('cursor.execute(q)\n')
        monkeypatch.setattr(scanner, "_ALLOWLIST", {"bad.py": "test exemption"})
        scan = scanner.scan_repo(tmp_path)
        assert scan['db_access_findings'] == []
        assert any(a['file'] == 'bad.py' for a in scan['allowlisted'])

    def test_skips_sanctioned_database_package(self, tmp_path):
        pkg = tmp_path / "src" / "database"
        pkg.mkdir(parents=True)
        (pkg / "pg.py").write_text('cursor.execute("SELECT 1")\n')
        scan = scanner.scan_repo(tmp_path)
        assert scan['db_access_findings'] == []

    def test_unreadable_file_is_skipped(self, tmp_path):
        (tmp_path / "binary.py").write_bytes(b'\xff\xfe not utf8 \x80\n')
        scan = scanner.scan_repo(tmp_path)  # must not raise
        assert isinstance(scan['scanned'], int)

    def test_collects_data_context_file_io(self, tmp_path):
        (tmp_path / "reader.py").write_text(
            'd = config.get_input_dir()\njson.load(open(d / "a.json"))\n')
        scan = scanner.scan_repo(tmp_path)
        assert 'reader.py' in scan['file_io_files']

    def test_rel_for_path_outside_root(self, tmp_path):
        from pathlib import Path as _P
        assert scanner._rel(_P("/elsewhere/y.py"), tmp_path) == "/elsewhere/y.py"


class TestDataAccessSection:
    """Smoke-test the full-audit subsection builder."""

    def test_builds_section_elements(self):
        from docs.models.full_audit.styles import _styles
        elems = scanner._build_data_access(_styles())
        assert elems  # produces flowables without raising

    def test_renders_findings_when_present(self, monkeypatch):
        """The ``if db:`` render branch — exercised with synthetic findings."""
        from docs.models.full_audit.styles import _styles
        monkeypatch.setattr(scanner, "scan_repo", lambda root=None: {
            'scanned': 1,
            'db_access_findings': [
                {'file': 'x.py', 'line': 3, 'kind': 'sql', 'snippet': 'SELECT'}],
            'file_io_findings': [], 'file_io_files': [], 'allowlisted': [],
        })
        elems = scanner._build_data_access(_styles())
        assert elems
