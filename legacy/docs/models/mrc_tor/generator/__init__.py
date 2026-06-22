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
Generate MRC Terms of Reference PDF using LaTeX.

Produces a formal Terms of Reference document for the Model Risk Committee
following the governance framework from the Handbook of Model Risk
Management for Vendors (Kelly, Mattimore 2025).

Usage:
    python -m docs.models.mrc_tor.generator
    python -m docs.models.mrc_tor.generator --pdf
"""

import argparse
import os

from .document import generate_document
from .compiler import compile_pdf

_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def main():
    parser = argparse.ArgumentParser(
        description='Generate MRC Terms of Reference')
    parser.add_argument('--pdf', action='store_true',
                        help='Compile to PDF via pdflatex')
    args = parser.parse_args()

    os.makedirs(_output_dir, exist_ok=True)
    tex_path = os.path.join(_output_dir, 'mrc_terms_of_reference.tex')

    content = generate_document()
    with open(tex_path, 'w') as f:
        f.write(content)
    print(f'LaTeX written: {tex_path}')

    if args.pdf:
        compile_pdf(_output_dir, 'mrc_terms_of_reference.tex')


if __name__ == '__main__':
    main()
