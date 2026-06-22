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

"""Path attributes and methods for the PortfolioConfig singleton."""

import os
import sys
from pathlib import Path


class PortfolioPaths:
    """Path attributes and methods for the PortfolioConfig singleton."""

    def _init_paths(self, catchment_id: str) -> None:
        """Initialise all path attributes. Call once from PortfolioConfig.__init__."""
        # config/path/ package is at: root/config/path/ → root = parents[2]
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.src_root = self.project_root / 'src'
        self.port_dir = self.src_root / 'port'

        # Data directories under data/
        # Test-only override: when MKM_CATCHMENT_INPUT_OVERRIDE points at a
        # fully-resolved catchment dir, use it instead of the real one. This
        # lets the e2e suite run the Flask subprocess against a tmp copy of
        # data/input/<catchment>/ so mutating endpoints never touch the shared
        # file tree (even if the suite is SIGKILLed mid-run). All derived
        # directories (blotter, eod, classifiers, prs, stressm, gaugehd,
        # gaugets) compute from self.input_dir and follow automatically.
        override = os.getenv('MKM_CATCHMENT_INPUT_OVERRIDE')
        if override:
            self.input_dir = Path(override)
        else:
            self.input_dir = self.project_root / 'data' / 'input' / catchment_id
        self.results_dir = self.project_root / 'data' / 'output' / 'results'

        # Catchment definitions under data/
        self.catchments_dir = self.project_root / 'data' / 'catch'

        # Source directories under src/
        self.cdm_dir = self.port_dir / 'cdm'
        self.src_dir = self.port_dir / 'src'

        self.visual_dir = self.src_root / 'visual'
        self.core_dir = self.visual_dir / 'core'
        self.layer_dir = self.visual_dir / 'layer'
        self.interactivity_dir = self.visual_dir / 'interactivity'
        self.popups_dir = self.visual_dir / 'popups'
        self.utils_dir = self.visual_dir / 'utils'

        # Create directories if needed
        self.input_dir.mkdir(exist_ok=True, parents=True)
        self.results_dir.mkdir(exist_ok=True, parents=True)

    def _setup_paths(self) -> None:
        """Add necessary paths to sys.path for imports."""
        self.data_root = self.project_root / 'data'
        paths_to_add = [
            self.project_root,
            self.src_root,
            self.data_root,
            self.port_dir,
            self.cdm_dir,
            self.src_dir,
            self.visual_dir,
            self.core_dir,
            self.layer_dir,
            self.interactivity_dir,
            self.popups_dir,
            self.utils_dir,
        ]

        for path in paths_to_add:
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)

    # ------------------------------------------------------------------
    # get_* directory accessors
    # ------------------------------------------------------------------

    def get_input_dir(self) -> Path:
        """Get input directory."""
        return self.input_dir

    def get_input_root(self) -> Path:
        """Root directory holding every catchment's input (``data/input``)."""
        return self.project_root / 'data' / 'input'

    def get_gaugehd_dir(self) -> Path:
        """Get gauge historical daily data directory."""
        gaugehd_dir = self.input_dir / 'gaugehd'
        gaugehd_dir.mkdir(exist_ok=True, parents=True)
        return gaugehd_dir

    def get_gaugets_dir(self) -> Path:
        """Get gauge timeseries directory (per-gauge storm simulation files)."""
        gaugets_dir = self.input_dir / 'gaugets'
        gaugets_dir.mkdir(exist_ok=True, parents=True)
        return gaugets_dir

    def get_stressm_dir(self) -> Path:
        """Get multi-storm stress data directory (storm sequences, gauge summaries).

        Path: data/input/<catchment>/stressm/
        Note: classifiers have moved to get_classifiers_dir().
        """
        stressm_dir = self.input_dir / 'stressm'
        stressm_dir.mkdir(exist_ok=True, parents=True)
        return stressm_dir

    def get_classifiers_dir(self) -> Path:
        """Get flood classifier directory (GBM .joblib models per gauge).

        Separated from stressm so classifiers are clearly distinct from
        storm sequence data.  Path: data/input/<catchment>/classifiers/
        """
        cls_dir = self.input_dir / 'classifiers'
        cls_dir.mkdir(exist_ok=True, parents=True)
        return cls_dir

    def get_reports_dir(self, report_type: str = None) -> Path:
        """Get reports directory, optionally for a specific report type.

        PRS trade files are stored under data/input/<catchment>/prs/ so they
        are tracked by git.  All other report types (UI-generated) live under
        data/output/.
        """
        if report_type == 'prs':
            prs_dir = self.input_dir / 'prs'
            prs_dir.mkdir(exist_ok=True, parents=True)
            return prs_dir
        base = self.project_root / 'data' / 'output'
        if report_type:
            d = base / report_type
            d.mkdir(exist_ok=True, parents=True)
            return d
        base.mkdir(exist_ok=True, parents=True)
        return base

    def get_property_reports_dir(self) -> Path:
        """Get property reports directory."""
        d = self.project_root / 'data' / 'output' / 'property'
        d.mkdir(exist_ok=True, parents=True)
        return d

    def get_gauge_reports_dir(self) -> Path:
        """Get gauge reports directory."""
        d = self.project_root / 'data' / 'output' / 'gauge'
        d.mkdir(exist_ok=True, parents=True)
        return d

    def get_output_dir(self) -> Path:
        """Get output directory for UI-generated reports."""
        return self.project_root / 'data' / 'output'

    def get_results_dir(self) -> Path:
        """Get results directory."""
        d = self.project_root / 'data' / 'output' / 'results'
        d.mkdir(exist_ok=True, parents=True)
        return d

    def get_trading_dir(self) -> Path:
        """Get trading data directory (market state, trade marks, EOD snapshots).

        Now lives under data/input/<catchment>/blotter/ so that trading
        desk data is git-tracked and available on fresh clones.
        """
        trading_dir = self.input_dir / 'blotter'
        trading_dir.mkdir(exist_ok=True, parents=True)
        return trading_dir

    def get_eod_dir(self) -> Path:
        """Get EOD snapshots directory."""
        eod_dir = self.get_trading_dir() / 'eod'
        eod_dir.mkdir(exist_ok=True, parents=True)
        return eod_dir

    def get_project_root(self) -> Path:
        """Get project root directory."""
        return self.project_root

    def get_governance_data_dir(self) -> Path:
        """Version-controlled governance data directory.

        Governance metadata (model inventory, MRC meetings, audit log, BCBS239
        assessment, RACI, bibliography, document manifest + uploads) is
        repo-level content and lives in the git tree, NOT under data/ (the
        shared, per-deployment data area). Kept beside the governance docs
        generators under docs/models/.

        Test-only override: when MKM_GOVERNANCE_DATA_OVERRIDE points at a
        directory, use it instead of the real one. This lets the e2e suite run
        the Flask subprocess against a tmp copy so mutating governance
        endpoints (MRC + document uploads) never write into the version-
        controlled tree, even if the suite is SIGKILLed mid-run.
        """
        override = os.getenv('MKM_GOVERNANCE_DATA_OVERRIDE')
        if override:
            return Path(override)
        return self.project_root / 'docs' / 'models' / 'governance_data'

    def get_input_path(self, filename: str) -> Path:
        """Get path to file in input directory."""
        return self.input_dir / filename

    def get_results_path(self, filename: str) -> Path:
        """Get path to file in results directory."""
        return self.results_dir / filename
