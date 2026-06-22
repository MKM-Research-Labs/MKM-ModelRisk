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

"""Colours, paths, and governance constants for the data lineage report."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / 'src'))

try:
    from reportlab.lib import colors
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Colours — consistent with full_audit
# ---------------------------------------------------------------------------

NAVY = colors.HexColor('#1A237E')
STEEL = colors.HexColor('#37474F')
BLUE = colors.HexColor('#1565C0')
GREEN = colors.HexColor('#2E7D32')
AMBER = colors.HexColor('#E65100')
RED = colors.HexColor('#B71C1C')
LIGHT_BG = colors.HexColor('#F5F5F5')
HEADER_BG = colors.HexColor('#E8EAF6')

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

from config import config
AUDIT_DIR = config.get_reports_dir('audit')
OUTPUT_PDF = AUDIT_DIR / 'data_lineage_report.pdf'
LINEAGE_PATH = _root / 'data' / 'data_lineage.json'

# ---------------------------------------------------------------------------
# Staleness threshold — aligned with governance route
# ---------------------------------------------------------------------------

STALE_HOURS = 72   # 3 days
RETENTION_DAYS = 365  # 1 year minimum

# ---------------------------------------------------------------------------
# Step ownership — BCBS 239 Principle 2 (clear responsibility)
# ---------------------------------------------------------------------------

STEP_OWNERS = {
    'gauges':             'Data Engineering',
    'properties':         'Data Engineering',
    'synthetic_gauges':   'Quantitative Analytics',
    'mortgages':          'Data Engineering',
    'gaugehd':        'Quantitative Analytics',
    'stressm':        'Quantitative Analytics',
    'hazard':         'Quantitative Analytics',
    'propertyts':     'Quantitative Analytics',
    'propertytsd':    'Quantitative Analytics',
    'propertytse':    'Quantitative Analytics',
    'propertyhc':     'Quantitative Analytics',
    'propertyshd':    'Quantitative Analytics',
    'propertyshe':    'Quantitative Analytics',
    'propertytsb':    'Quantitative Analytics',
    'propertybri':    'Quantitative Analytics',
    'property_peril_ts': 'Quantitative Analytics',
    'propertywin':    'Quantitative Analytics',
    'propertyfaw':    'Quantitative Analytics',
    'propertyfow':    'Quantitative Analytics',
    'propertybow':    'Quantitative Analytics',
    'propertybaw':    'Quantitative Analytics',
    'counterparties': 'Data Engineering',
    'blotter':        'Trading / Risk',
    'typhoon':          'Quantitative Analytics',
    'commercial':       'Data Engineering',
    'commercialts':     'Quantitative Analytics',
    'commercialtsd':    'Quantitative Analytics',
    'commercialtse':    'Quantitative Analytics',
    'commercialhc':     'Quantitative Analytics',
    'commercialshd':    'Quantitative Analytics',
    'commercialshe':    'Quantitative Analytics',
    'commercialtsb':    'Quantitative Analytics',
    'commercialbri':    'Quantitative Analytics',
    'commercial_peril_ts': 'Quantitative Analytics',
    'commercialwin':    'Quantitative Analytics',
    'commercialfaw':    'Quantitative Analytics',
    'commercialfow':    'Quantitative Analytics',
    'commercialbow':    'Quantitative Analytics',
    'commercialbaw':    'Quantitative Analytics',
    'fire':             'Quantitative Analytics',
    'seismic':          'Quantitative Analytics',
}

# ---------------------------------------------------------------------------
# BCBS principle mapping for reconciliation checks
# ---------------------------------------------------------------------------

FAILURE_METADATA = {
    'test_gauge_id_consistency': {
        'principle': 'P3 (Accuracy)',
        'description': 'Every gauge in gauge.json has a matching hazard curve; '
                       'no orphan IDs in gaugehc.json.',
        'remediation': 'Re-run python app.py port to regenerate gauge and '
                       'hazard curve data.',
    },
    'test_trade_gauge_references': {
        'principle': 'P3, P4 (Completeness)',
        'description': 'Every traded gauge_id exists in the gauge master file.',
        'remediation': 'Re-run python app.py port to regenerate trade blotter '
                       'with current gauge data.',
    },
    'test_trade_hazard_curves': {
        'principle': 'P3, P4 (Completeness)',
        'description': 'Every traded gauge_id has an associated hazard curve.',
        'remediation': 'Re-run python app.py port to regenerate hazard curves.',
    },
    'test_property_id_consistency': {
        'principle': 'P3 (Accuracy)',
        'description': 'Property time-series files reference valid property IDs.',
        'remediation': 'Re-run python app.py port to regenerate property '
                       'time-series.',
    },
    'test_storm_id_consistency': {
        'principle': 'P3 (Accuracy)',
        'description': 'All storm IDs in time-series originate from storm '
                       'sequences.',
        'remediation': 'Re-run python app.py port to regenerate stress/storm '
                       'data.',
    },
    'test_classifier_gauge_alignment': {
        'principle': 'P3, P7 (Comprehensiveness)',
        'description': 'Classifier model files reference current gauge IDs.',
        'remediation': 'Retrain classifiers via the gauge classifier UI.',
    },
    'test_manifest_hash_verification': {
        'principle': 'P3 (Integrity)',
        'description': 'Recorded output hashes match current file content on '
                       'disk.',
        'remediation': 'Re-run the affected pipeline step to update manifest '
                       'hashes.',
    },
    'test_no_stale_inputs': {
        'principle': 'P3, P6 (Timeliness)',
        'description': 'No pipeline step consumes inputs whose SHA-256 hash '
                       'differs from the upstream producer\'s current output '
                       'hash — i.e. upstream data has not changed since this '
                       'step last ran.',
        'remediation': 'Re-run python app.py port to regenerate stale inputs '
                       'before using these data for risk reporting.',
    },
    'test_deterministic_ids': {
        'principle': 'P3, P7 (Clarity)',
        'description': 'Gauge IDs are derived from location, not randomly '
                       'generated.',
        'remediation': 'Regenerate gauge data with deterministic ID scheme.',
    },
}
