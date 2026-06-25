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
"""Console coding-rule audit report: ``python -m audit``."""
from __future__ import annotations

from config.audit import COVERAGE_MINIMUM

from audit.duplication import duplication_report
from audit.embedded_js import embedded_js_findings
from audit.hardcoding import hardcoding_findings
from audit.init_files import init_file_findings
from audit.large_files import large_source_files, large_test_files


def _print_section(title: str, findings: list[dict], formatter) -> int:
    mark = "OK " if not findings else "!! "
    print(f"\n{mark}{title} — {len(findings)} finding(s)")
    for item in findings:
        print("     " + formatter(item))
    return len(findings)


def build_report() -> dict:
    """Collect every audit's findings into one dict (used by tests and the CLI)."""
    return {
        "large_source_files": large_source_files(),
        "large_test_files": large_test_files(),
        "hardcoding": hardcoding_findings(),
        "embedded_js": embedded_js_findings(),
        "init_files": init_file_findings(),
        "duplication": duplication_report(),
    }


def main() -> int:
    report = build_report()
    print("MKM-ModelRisk — coding-rule audit")
    print("=" * 50)
    total = 0
    total += _print_section("R2 large source files (>300)", report["large_source_files"],
                            lambda f: f"{f['lines']:>4}  {f['path']}")
    total += _print_section("R2 large test files (>400)", report["large_test_files"],
                            lambda f: f"{f['lines']:>4}  {f['path']}")
    total += _print_section("R1 hardcoded parameters", report["hardcoding"],
                            lambda f: f"{f['path']}:{f['line']}  {f['kind']} {f['name']}")
    total += _print_section("R7 embedded JavaScript / CSS", report["embedded_js"],
                            lambda f: f"{f['path']}:{f['line']}  {f['kind']} ({f['js_lines']} js lines)")
    total += _print_section("R4 substantive __init__.py", report["init_files"],
                            lambda f: f"{f['path']}  fns={f['functions']} classes={f['classes']}")
    dup = report["duplication"]
    if dup.get("available"):
        print(f"\n.. Duplicate code — {dup['percentage']}% ({dup['clones']} clones, "
              f"{dup['duplicated_lines']} lines)")
    else:
        print("\n.. Duplicate code — jscpd not installed, skipped")
    print(f"\n.. Coverage gate — enforced at {COVERAGE_MINIMUM}% via pyproject fail_under")
    print("=" * 50)
    print(f"{'PASS' if total == 0 else 'FINDINGS'}: {total} gated finding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
