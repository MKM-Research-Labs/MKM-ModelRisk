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

"""Shared pdflatex compilation wrapper."""

import os
import subprocess
import sys


def compile_pdf(output_dir, tex_filename):
    """Compile a LaTeX file to PDF via pdflatex (two passes for TOC).

    Returns the PDF path on success, or exits on failure.
    """
    print('Compiling PDF...')
    for _ in range(2):
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_filename],
            cwd=output_dir,
            capture_output=True,
            text=True,
        )
    pdf_path = os.path.join(output_dir, tex_filename.replace('.tex', '.pdf'))
    if os.path.isfile(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f'PDF generated: {pdf_path} ({size_kb:.0f} KB)')
        return pdf_path
    else:
        print('PDF compilation failed.')
        print(result.stdout[-2000:] if result.stdout else '')
        print(result.stderr[-2000:] if result.stderr else '')
        sys.exit(1)
