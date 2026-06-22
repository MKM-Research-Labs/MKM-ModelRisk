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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Path constants and validation constants for governance routes."""

import os

from config import config

_data_dir = str(config.get_project_root() / "data")
_output_dir = str(config.get_output_dir())
_docs_dir = str(config.get_project_root() / "docs" / "models")

# Governance metadata is version-controlled repo content, NOT shared data/.
# It lives under docs/models/governance_data/ (see config.get_governance_data_dir).
_gov_dir = str(config.get_governance_data_dir())

INVENTORY_PATH = os.path.join(_gov_dir, "model_inventory.json")
AUDIT_LOG_PATH = os.path.join(_gov_dir, "model_audit_log.json")
MRC_MEETINGS_PATH = os.path.join(_gov_dir, "mrc_meetings.json")
MRC_UPLOADS_DIR = os.path.join(_gov_dir, "mrc_uploads")
BCBS239_PATH = os.path.join(_gov_dir, "bcbs239_assessment.json")
RACI_PATH = os.path.join(_gov_dir, "raci_matrix.json")
BIBLIOGRAPHY_PATH = os.path.join(_gov_dir, "bibliography.json")
GOV_DOCUMENTS_PATH = os.path.join(_gov_dir, "governance_documents.json")
GOV_DOCUMENTS_DIR = os.path.join(_gov_dir, "governance_docs")
AUDIT_REPORTS_DIR = os.path.join(_output_dir, "audit")
# Lineage manifests are pipeline-generated data-about-the-data and remain in data/.
LINEAGE_PATH = os.path.join(_data_dir, "data_lineage.json")
FIELD_LINEAGE_PATH = os.path.join(_data_dir, "field_lineage_registry.json")

# Model ID → docs directory name (for serving per-model PDFs)
_MODEL_DOC_DIRS = {
    'MKM-SI-001': 'storm_intensity',
    'MKM-SG-001': 'storm_gauge',
    'MKM-GH-001': 'gev_hazard',
    'MKM-PR-001': 'prs_pricing',
    'MKM-DD-001': 'flood_risk',
    'MKM-PV-001': 'property_valuation',
    'MKM-MP-001': 'mortgage_pricer',
    'MKM-RA-001': 'risk_assessment',
    'MKM-DE-001': 'delta_engine',
    'MKM-SP-001': 'spatial_model',
    'MKM-IP-001': 'insurance_premium',
    'MKM-FC-001': 'flood_classifier',
    'MKM-SS-001': 'storm_multi',
    'MKM-GHD-001': 'gaugehd_synthetic',
    'MKM-ST-001': 'stressm_pipeline',
    'MKM-PF-001': 'property_flood_response',
    'MKM-FPO-001': 'flood_poly',
    'MKM-BRI-001': 'bri_resilience',
    'MKM-FIRE-001': 'fire_resilience',
}

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_UPLOAD_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'png', 'jpg', 'jpeg',
}

VALID_VQ_STATUSES = ["Addressed", "Partially Addressed", "Not Addressed", "Not Applicable"]
VALID_RISK_RATINGS = ["Acceptable", "Conditional", "Unacceptable"]
VALID_RACI_ROLE_IDS = ["operations_lead", "model_owner", "peer_model_owners", "leadership"]

EDITABLE_FIELDS = {
    "rag_rating": {"type": "choice", "options": ["Green", "Amber", "Red"]},
    "owner": {"type": "text"},
    "model_owner_role": {"type": "text"},
    "lifecycle_stage": {
        "type": "choice",
        "options": ["Development", "Validation", "Production", "Retired"],
    },
    "peer_reviewer": {"type": "text"},
    "last_review_date": {"type": "date"},
    "next_review_date": {"type": "date"},
    "mrc_signoff_date": {"type": "date"},
    "recertification_date": {"type": "date"},
    "validation_status": {
        "type": "choice",
        "options": ["Initial", "Pending", "Validated", "Conditionally Approved", "Rejected"],
    },
    "review_frequency": {
        "type": "choice",
        "options": ["Monthly", "Quarterly", "Semi-annual", "Annual"],
    },
}

_BCBS239_SCORE_STATUS = {
    1: "Non-compliant",
    2: "Materially Non-compliant",
    3: "Largely Compliant",
    4: "Fully Compliant",
}
