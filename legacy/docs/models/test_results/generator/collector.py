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

"""Pytest plugin that collects structured test results."""

import os

from .models import TEST_MODEL_MAP

_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


class TestResultCollector:
    """Pytest plugin that collects structured test results."""

    def __init__(self):
        self.results = []

    def pytest_collection_modifyitems(self, items):
        """Cache docstrings and parametrize info at collection time."""
        self._item_info = {}
        for item in items:
            doc = (item.function.__doc__ or '').strip()
            desc_line = doc.split('\n')[0] if doc else ''
            params = ''
            if hasattr(item, 'callspec') and item.callspec.params:
                params = ', '.join(
                    f'{k}={v!r}' for k, v in item.callspec.params.items()
                )
            self._item_info[item.nodeid] = {
                'docstring': doc,
                'description': desc_line,
                'params': params,
            }

    def pytest_runtest_logreport(self, report):
        if report.when == 'call' or (report.when == 'setup' and report.skipped):
            rel_path = report.fspath
            if rel_path.startswith(_project_root):
                rel_path = os.path.relpath(rel_path, _project_root)

            parts = report.nodeid.split('::')
            test_class = parts[1] if len(parts) > 2 else ''
            test_name = parts[-1]

            model_id = TEST_MODEL_MAP.get(rel_path, 'PLATFORM')

            info = getattr(self, '_item_info', {}).get(report.nodeid, {})

            result = {
                'nodeid': report.nodeid,
                'file': rel_path,
                'class': test_class,
                'name': test_name,
                'model_id': model_id,
                'outcome': report.outcome,
                'duration': round(report.duration, 4),
                'longrepr': str(report.longrepr) if report.failed else '',
                'description': info.get('description', ''),
                'docstring': info.get('docstring', ''),
                'params': info.get('params', ''),
            }
            self.results.append(result)
