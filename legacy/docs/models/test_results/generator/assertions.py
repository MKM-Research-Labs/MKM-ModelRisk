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

"""Extract assertion expressions from test source files."""

import ast
import os

_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def _extract_assertions(file_path, test_class, test_name):
    """Parse a test file and extract assert statements as acceptance criteria."""
    base_name = test_name.split('[')[0]

    try:
        full_path = os.path.join(_project_root, file_path)
        with open(full_path) as f:
            source = f.read()
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    assertions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name != base_name:
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    try:
                        expr = ast.get_source_segment(source, child.test)
                        if expr:
                            assertions.append(expr.strip())
                    except Exception:
                        pass
    return assertions


def build_criteria_cache(results):
    """Build a cache of assertion expressions for all tests."""
    cache = {}
    for r in results:
        key = (r['file'], r['class'], r['name'])
        if key not in cache:
            cache[key] = _extract_assertions(r['file'], r['class'], r['name'])
    return cache
