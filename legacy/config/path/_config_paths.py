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

"""Path methods for the lightweight Config class."""

import os
from pathlib import Path


class ConfigPaths:
    """Path methods for the simple Config class."""

    def _get_project_root(self) -> Path:
        """Get project root directory."""
        env_root = os.getenv('MKM_PROJECT_ROOT')
        if env_root:
            return Path(env_root)

        current = Path(__file__).resolve().parent.parent.parent  # config/path/ → root
        markers = ['setup.py', 'pyproject.toml', '.git', 'requirements.txt']

        for _ in range(10):
            if any((current / m).exists() for m in markers):
                return current
            if current.parent == current:
                break
            current = current.parent

        return Path(__file__).resolve().parent.parent.parent

    def _get_catchment_input_dir(self) -> Path:
        """Get catchment-specific input directory."""
        catchment = os.getenv('MKM_CATCHMENT', 'thames')
        return self._get_project_root() / os.getenv('MKM_INPUT_DIR', 'data/input') / catchment

    def get_input_dir(self) -> Path:
        """Get input data directory."""
        return self._get_project_root() / os.getenv('MKM_INPUT_DIR', 'data/input')

    def get_output_dir(self) -> Path:
        """Get output directory for UI-generated reports."""
        return self._get_project_root() / os.getenv('MKM_OUTPUT_DIR', 'data/output')

    def get_reports_dir(self, report_type: str = None) -> Path:
        """Get reports directory, optionally for a specific report type."""
        base = self._get_project_root() / 'data' / 'output'
        if report_type:
            return base / report_type
        return base

    def get_property_reports_dir(self) -> Path:
        """Get property reports directory."""
        return self._get_project_root() / 'data' / 'output' / 'property'

    def get_gauge_reports_dir(self) -> Path:
        """Get gauge reports directory."""
        return self._get_project_root() / 'data' / 'output' / 'gauge'

    def get_results_dir(self) -> Path:
        """Get results directory."""
        return self._get_project_root() / 'data' / 'output' / 'results'

    def get_project_root(self) -> Path:
        """Get project root directory (public accessor)."""
        return self._get_project_root()

    def get_governance_data_dir(self) -> Path:
        """Version-controlled governance data directory.

        Governance metadata (model inventory, MRC meetings, audit log, BCBS239
        assessment, RACI, bibliography, document manifest + uploads) is
        repo-level content and lives in the git tree, NOT under data/ (the
        shared, per-deployment data area). Kept beside the governance docs
        generators under docs/models/.

        Test-only override: MKM_GOVERNANCE_DATA_OVERRIDE redirects this to a
        tmp dir so the e2e Flask subprocess never writes into the version-
        controlled tree.
        """
        override = os.getenv('MKM_GOVERNANCE_DATA_OVERRIDE')
        if override:
            return Path(override)
        return self._get_project_root() / 'docs' / 'models' / 'governance_data'
