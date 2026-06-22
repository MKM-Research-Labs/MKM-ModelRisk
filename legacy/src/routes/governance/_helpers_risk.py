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

"""Document discovery and risk calculation helpers for governance routes."""

import hashlib
import os
from datetime import datetime

from . import _constants


def _stable_id(path):
    """Generate a short stable ID from a file path."""
    return hashlib.md5(path.encode()).hexdigest()[:8]


def _pdf_entry(filepath, description, source):
    """Build a document-style dict for a discovered PDF."""
    filename = os.path.basename(filepath)
    try:
        size = os.path.getsize(filepath)
    except OSError:
        size = 0
    return {
        "id": _stable_id(filepath),
        "filename": filename,
        "description": description,
        "size": size,
        "source": source,
    }


_AUDIT_LABELS = {
    "full_audit_report.pdf": "Full Audit Report",
    "test_report.pdf": "Test Results Report",
    "code_duplication_report.pdf": "Code Duplication Report",
    "hardcoding_report.pdf": "Hard-Coding Parameter Audit",
    "embedded_js_report.pdf": "Embedded JS/CSS Audit",
    "data_lineage_report.pdf": "Data Lineage Report (BCBS 239)",
    "large_file_report.pdf": "Code Modularisation Analysis",
    "init_audit_report.pdf": "__init__.py Substantive-Code Audit",
    "model_risk_report.pdf": "Model Risk Report",
}


def _discover_audit_docs():
    """Scan data/output/audit/ for generated PDF reports."""
    audit_dir = _constants.AUDIT_REPORTS_DIR
    if not os.path.isdir(audit_dir):
        return []
    results = []
    for entry in sorted(os.scandir(audit_dir), key=lambda e: e.name):
        if entry.is_file() and entry.name.endswith(".pdf"):
            label = _AUDIT_LABELS.get(entry.name, entry.name.replace("_", " ").replace(".pdf", "").title())
            results.append(_pdf_entry(entry.path, label, "audit"))
    return results


_MODEL_PDF_LABELS = {
    "test_results.pdf": "Test Results",
    "analysis.pdf": "Model Analysis",
}


def _discover_model_docs():
    """Scan docs/models/ for per-model documentation PDFs."""
    docs_dir = str(_constants._docs_dir)
    if not os.path.isdir(docs_dir):
        return []

    # Build reverse lookup: directory name → model ID
    dir_to_id = {v: k for k, v in _constants._MODEL_DOC_DIRS.items()}

    results = []
    for model_dir in sorted(os.scandir(docs_dir), key=lambda e: e.name):
        if not model_dir.is_dir():
            continue
        model_id = dir_to_id.get(model_dir.name, model_dir.name)
        model_label = model_dir.name.replace("_", " ").title()
        for entry in sorted(os.scandir(model_dir.path), key=lambda e: e.name):
            if entry.is_file() and entry.name.endswith(".pdf"):
                kind = _MODEL_PDF_LABELS.get(entry.name, "Documentation")
                desc = f"{model_label} — {kind}" if entry.name in _MODEL_PDF_LABELS else f"{model_label} — {entry.name.replace('.pdf', '').replace('_', ' ').title()}"
                results.append(_pdf_entry(entry.path, desc, "model"))
    return results


def _calculate_risk_rating(model):
    """Calculate composite risk rating from 5 weighted factors.

    Returns dict with calculated_rating, calculated_score, and component_scores.
    """
    vq = model.get("validation_questions", [])

    # 1. validation_coverage (30%): fraction of questions fully Addressed
    addressed = sum(1 for q in vq if q.get("status") == "Addressed")
    applicable = sum(1 for q in vq if q.get("status") != "Not Applicable")
    coverage = addressed / max(applicable, 1)

    # 2. remediation_health (25%): penalise open and overdue items
    # remediation_steps may be list-of-dicts (structured) or list-of-strings
    # (legacy/freeform). Only dict entries can have a status/due_date.
    today = datetime.now().strftime("%Y-%m-%d")
    rem = model.get("remediation_steps") or []
    rem_dicts = [r for r in rem if isinstance(r, dict)]
    open_count = sum(1 for r in rem_dicts if r.get("status") == "Open")
    overdue_count = sum(
        1 for r in rem_dicts
        if r.get("status") == "Open" and r.get("due_date") and r["due_date"] < today
    )
    rem_score = max(0.0, min(1.0, 1.0 - 0.15 * open_count - 0.25 * overdue_count))

    # 3. review_currency (20%): is the review schedule current
    next_review = model.get("next_review_date")
    if next_review:
        days_to = (datetime.strptime(next_review, "%Y-%m-%d") - datetime.now()).days
        if days_to < 0:
            review_score = 0.0
        elif days_to <= 30:
            review_score = 0.5
        else:
            review_score = 1.0
    else:
        review_score = 0.0

    # 4. assumption_risk (15%): high-impact assumptions
    assumptions = model.get("assumptions", [])
    high_assumptions = sum(1 for a in assumptions if a.get("impact") == "High")
    assumption_score = max(0.0, min(1.0, 1.0 - 0.2 * high_assumptions))

    # 5. limitation_risk (10%): high-impact limitations
    limitations = model.get("limitations", [])
    high_limitations = sum(1 for lim in limitations if lim.get("impact") == "High")
    limitation_score = max(0.0, min(1.0, 1.0 - 0.2 * high_limitations))

    # Weighted composite
    composite = (
        coverage * 0.30
        + rem_score * 0.25
        + review_score * 0.20
        + assumption_score * 0.15
        + limitation_score * 0.10
    )

    if composite >= 0.75:
        rating = "Acceptable"
    elif composite >= 0.45:
        rating = "Conditional"
    else:
        rating = "Unacceptable"

    return {
        "calculated_rating": rating,
        "calculated_score": round(composite, 3),
        "component_scores": {
            "validation_coverage": round(coverage, 3),
            "remediation_health": round(rem_score, 3),
            "review_currency": round(review_score, 3),
            "assumption_risk": round(assumption_score, 3),
            "limitation_risk": round(limitation_score, 3),
        },
    }


def _vq_summary(model):
    """Return validation question coverage string like '3/9'."""
    vq = model.get("validation_questions", [])
    addressed = sum(1 for q in vq if q.get("status") == "Addressed")
    applicable = sum(1 for q in vq if q.get("status") != "Not Applicable")
    return f"{addressed}/{applicable}"
