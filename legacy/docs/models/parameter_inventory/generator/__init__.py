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
Generate LaTeX parameter inventory for model governance.

Produces a single PDF cataloguing all hard-coded input parameters
across the analytical model codebase.

Usage:
    python -m docs.models.parameter_inventory.generator
    python -m docs.models.parameter_inventory.generator --pdf
"""

import argparse
import os

from .parameters import get_parameter_sections
from .latex import generate_document
from .compiler import compile_pdf

_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def main():
    parser = argparse.ArgumentParser(
        description='Generate LaTeX parameter inventory')
    parser.add_argument('--pdf', action='store_true',
                        help='Compile LaTeX to PDF')
    args = parser.parse_args()

    print('=' * 60)
    print('MKM Research Labs — Parameter Inventory Generator')
    print('=' * 60)
    print()

    # Generate LaTeX
    sections = get_parameter_sections()
    content = generate_document(sections)
    os.makedirs(_output_dir, exist_ok=True)
    tex_path = os.path.join(_output_dir, 'parameter_inventory.tex')

    with open(tex_path, 'w') as f:
        f.write(content)
    print(f'  LaTeX written: {tex_path}')

    if args.pdf:
        compile_pdf(_output_dir, tex_path)

    print('\nDone.')


if __name__ == '__main__':
    main()
