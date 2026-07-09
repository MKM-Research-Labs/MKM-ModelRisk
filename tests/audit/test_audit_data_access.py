# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Data-access audit (coding rule R6): store reached only via src/database."""
from __future__ import annotations

from audit.data_access import _scan_text, data_access_findings


def test_flags_sql_execute_driver_and_connection():
    text = (
        "import sqlite3\n"
        "cur.execute('DELETE FROM t')\n"
        "rows = conn.execute(q)\n"
        "engine = create_engine(url)\n"
    )
    kinds = {f["kind"] for f in _scan_text(text, "m.py")}
    assert kinds == {"driver_import", "sql", "execute", "connection"}


def test_ignores_sql_in_comments_and_docstrings():
    text = (
        '"""Example: SELECT id FROM users."""\n'
        "# INSERT INTO audit VALUES (1)\n"
        "x = 1\n"
    )
    assert _scan_text(text, "m.py") == []


def test_prose_is_not_mistaken_for_sql():
    # Structural SQL patterns only — English prose must not match.
    text = "update the set of gauges\ndelete_from_cache(key)\n"
    assert _scan_text(text, "m.py") == []


def test_findings_are_sorted_and_carry_location():
    findings = data_access_findings()
    assert findings == sorted(findings, key=lambda f: (f["path"], f["line"]))
    for f in findings:
        assert {"path", "line", "kind", "snippet"} <= set(f)
        # The sanctioned package and the auditor itself are never reported.
        assert not f["path"].startswith(("src/database/", "audit/"))
