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

"""Entry point: run jscpd, analyse, and write the PDF report."""

import sys
from datetime import datetime


def main():
    # Resolve through the package namespace so callers (and tests) can patch
    # _run_jscpd / AUDIT_DIR / OUTPUT_PDF on the package itself.
    import docs.models.duplication as pkg

    print('Running jscpd on src/ …')
    try:
        report = pkg._run_jscpd()
    except Exception as e:
        print(f'ERROR running jscpd: {e}')
        sys.exit(1)

    print('Analysing results …')
    analysis = pkg._analyse(report)
    total = analysis['total']
    print(f"  Files: {total.get('sources', 0)}  |  "
          f"Lines: {total.get('lines', 0):,}  |  "
          f"Clones: {analysis['num_clones']}  |  "
          f"Dup%: {total.get('percentage', 0):.1f}%")

    print('Generating PDF …')
    run_at = datetime.now()
    pdf_bytes = pkg._make_pdf(analysis, run_at)

    pkg.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    pkg.OUTPUT_PDF.write_bytes(pdf_bytes)
    print(f'PDF saved → {pkg.OUTPUT_PDF}')
    print(f'Size: {len(pdf_bytes) / 1024:.1f} KB')
