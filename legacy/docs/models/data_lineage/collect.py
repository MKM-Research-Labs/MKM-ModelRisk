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

"""Verdict helpers and pipeline data collection for the data lineage report."""

import json

from ._constants import GREEN, AMBER, RED


# ---------------------------------------------------------------------------
# Overall verdict helpers
# ---------------------------------------------------------------------------

def _compute_verdict(chain_result: dict, lineage_results: dict) -> str:
    """Derive overall BCBS 239 verdict from chain + test results.

    Most conservative status wins.
    """
    chain_ok = chain_result.get('is_consistent', False)
    tests_failed = lineage_results.get('failed', 0)
    tests_total = lineage_results.get('total', 0)
    missing = len(chain_result.get('missing_steps', []))

    if chain_ok and tests_failed == 0 and tests_total > 0 and missing == 0:
        return 'COMPLIANT'
    if not chain_ok or missing > 0 or (tests_total > 0 and
                                        tests_failed > tests_total * 0.5):
        return 'NON-COMPLIANT'
    return 'PARTIALLY COMPLIANT'


def _compute_health(chain_result: dict, lineage_results: dict) -> str:
    """Pipeline health badge — worst-case wins."""
    chain_ok = chain_result.get('is_consistent', False)
    tests_failed = lineage_results.get('failed', 0)
    tests_total = lineage_results.get('total', 0)
    stale = len(chain_result.get('stale_steps', []))

    if chain_ok and tests_failed == 0 and stale == 0:
        return 'CONSISTENT'
    if not chain_ok:
        return 'INCONSISTENT'
    return 'DEGRADED'


def _health_colour(health: str):
    """Colour for pipeline health badge."""
    return {'CONSISTENT': GREEN, 'DEGRADED': AMBER,
            'INCONSISTENT': RED}.get(health, RED)


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def _load_manifest() -> dict:
    import docs.models.data_lineage as pkg
    if pkg.LINEAGE_PATH.exists():
        try:
            with open(pkg.LINEAGE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"runs": {}, "steps": {}}


def _load_lineage_results() -> dict:
    """Load data_lineage_results.json from audit dir (produced by test run)."""
    import docs.models.data_lineage as pkg
    p = pkg.AUDIT_DIR / 'data_lineage_results.json'
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def collect_all() -> dict:
    """Collect all lineage data for the report."""
    import docs.models.data_lineage as pkg

    # Import the lineage modules
    try:
        from lineage.manifest import DEPENDENCY_GRAPH, STEP_IO
        from lineage.validation import validate_full_chain
    except ImportError:
        # Fallback — define locally
        DEPENDENCY_GRAPH = {}
        STEP_IO = {}
        validate_full_chain = lambda: {
            "is_consistent": False,
            "stale_steps": [],
            "missing_steps": list(DEPENDENCY_GRAPH.keys()),
            "details": {},
        }

    manifest = pkg._load_manifest()
    steps = manifest.get("steps", {})
    runs = manifest.get("runs", {})

    # Validation
    try:
        chain_result = validate_full_chain()
    except Exception:
        chain_result = {
            "is_consistent": False,
            "stale_steps": [],
            "missing_steps": list(DEPENDENCY_GRAPH.keys()),
            "details": {"error": ["Validation could not be run"]},
        }

    # Consistency test results
    lineage_results = pkg._load_lineage_results()

    # Per-step freshness from manifest timestamps
    step_details = []
    for step_name in DEPENDENCY_GRAPH:
        entry = steps.get(step_name, {})
        deps = DEPENDENCY_GRAPH.get(step_name, [])
        io = STEP_IO.get(step_name, {})
        is_stale = step_name in chain_result.get("stale_steps", [])
        is_missing = step_name in chain_result.get("missing_steps", [])

        step_details.append({
            "step": step_name,
            "dependencies": deps,
            "inputs": io.get("inputs", []),
            "outputs": io.get("outputs", []),
            "generator": entry.get("generator", ""),
            "run_id": entry.get("run_id", ""),
            "timestamp": entry.get("timestamp", ""),
            "elapsed_s": entry.get("elapsed_seconds", 0),
            "status": "missing" if is_missing else ("stale" if is_stale else "fresh"),
            "hash_status": entry.get("status", ""),
            "parameters": entry.get("parameters", {}),
            "input_hashes": entry.get("inputs", {}),
            "output_hashes": entry.get("outputs", {}),
        })

    return {
        "manifest": manifest,
        "graph": DEPENDENCY_GRAPH,
        "step_io": STEP_IO,
        "chain_result": chain_result,
        "lineage_results": lineage_results,
        "step_details": step_details,
        "num_runs": len(runs),
        "num_steps": len(DEPENDENCY_GRAPH),
        "num_recorded": len(steps),
    }
