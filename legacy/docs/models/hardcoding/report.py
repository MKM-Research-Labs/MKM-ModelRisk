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

"""Entry point: scan src/ and write the hard-coding audit PDF."""

from pathlib import Path

from .scanners import collect_all
from .pdf import create_pdf_report


def main():
    here = Path(__file__).resolve().parent           # docs/models/hardcoding/
    root = here.parent.parent.parent                 # project root

    src_dir   = root / 'src'
    from config import config
    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'hardcoding_report.pdf'

    print("Scanning src/ for hard-coded parameters...")
    findings = collect_all(src_dir, root)

    caps_action   = [f for f in findings['allcaps'] if not f['precision_ok']]
    total_action = (
        len(findings['duplicates'])
        + len(caps_action)
        + len(findings['infra'])
        + len(findings['inline'])
    )
    print(f"  {findings['files_scanned']} files scanned")
    print(f"  {len(findings['duplicates'])} duplicate constants")
    print(f"  {len([f for f in findings['allcaps'] if not f['precision_ok']])} "
          f"ALL_CAPS outside config ({len([f for f in findings['allcaps'] if f['precision_ok']])} "
          f"precision-ok)")
    print(f"  {len(findings['infra'])} infrastructure literals")
    print(f"  {len(findings['inline'])} inline simulation literals")
    print(f"  {total_action} total action items")

    create_pdf_report(findings, output_path, root)
