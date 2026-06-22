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
Lineage queries — trace individual data points and file provenance.

Supports BCBS 239 Principle 7 (accuracy) by providing point-in-time
traceability from any output back to its source inputs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lineage.manifest import (
    DEPENDENCY_GRAPH,
    STEP_IO,
    load_manifest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _output_to_step() -> dict[str, str]:
    """Map output filename -> producing step."""
    return {
        out: step
        for step, io in STEP_IO.items()
        for out in io["outputs"]
    }


def _input_to_step() -> dict[str, list[str]]:
    """Map input filename -> list of consuming steps."""
    mapping: dict[str, list[str]] = {}
    for step, io in STEP_IO.items():
        for inp in io["inputs"]:
            mapping.setdefault(inp, []).append(step)
    return mapping


def _walk_upstream(step_name: str, visited: set | None = None) -> list[str]:
    """Recursively collect upstream steps in dependency order."""
    visited = visited or set()
    if step_name in visited:
        return []
    visited.add(step_name)
    result: list[str] = []
    for dep in DEPENDENCY_GRAPH.get(step_name, []):
        result.extend(_walk_upstream(dep, visited))
    result.append(step_name)
    return result

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def trace_data_point(data_type: str, data_id: str) -> list[dict]:
    """Build a provenance chain for a logical data point.

    *data_type* is one of ``"gauge_id"``, ``"property_id"``, ``"storm_id"``.
    Returns a list of dicts describing each pipeline step that touched the
    data point, ordered from source to final output.
    """
    type_to_steps: dict[str, list[str]] = {
        "gauge_id":    ["gauges", "gaugehd", "stressm", "hazard"],
        "property_id": ["properties", "propertyts", "propertytsd", "propertytse",
                        "propertyhc", "propertyshd", "propertyshe"],
        "storm_id":    ["stressm", "propertyts"],
    }
    steps = type_to_steps.get(data_type, [])
    manifest = load_manifest()
    chain: list[dict] = []

    for step in steps:
        entry = manifest.get("steps", {}).get(step)
        chain.append({
            "step": step,
            "data_type": data_type,
            "data_id": data_id,
            "recorded": entry is not None,
            "run_id": entry.get("run_id") if entry else None,
            "timestamp": entry.get("timestamp") if entry else None,
            "status": entry.get("status") if entry else None,
        })

    return chain


def get_file_lineage(file_path: str) -> dict:
    """Determine which step produced *file_path* and who consumes it.

    *file_path* should be a filename or directory name as it appears in
    ``STEP_IO`` (e.g. ``"gauge.json"`` or ``"gaugets/"``).
    """
    output_map = _output_to_step()
    input_map = _input_to_step()
    manifest = load_manifest()

    producer = output_map.get(file_path)
    consumers = input_map.get(file_path, [])

    producer_entry = (
        manifest.get("steps", {}).get(producer) if producer else None
    )

    return {
        "file": file_path,
        "produced_by": producer,
        "producer_run_id": (
            producer_entry.get("run_id") if producer_entry else None
        ),
        "producer_timestamp": (
            producer_entry.get("timestamp") if producer_entry else None
        ),
        "consumed_by": consumers,
    }


def get_step_lineage(step_name: str) -> dict:
    """Return upstream and downstream trees for *step_name*."""
    upstream = _walk_upstream(step_name)
    # Remove the step itself from upstream list
    upstream = [s for s in upstream if s != step_name]

    downstream: list[str] = []
    for step, deps in DEPENDENCY_GRAPH.items():
        if step_name in deps:
            downstream.append(step)

    manifest = load_manifest()
    entry = manifest.get("steps", {}).get(step_name)

    return {
        "step": step_name,
        "upstream": upstream,
        "downstream": downstream,
        "last_run": entry.get("run_id") if entry else None,
        "last_timestamp": entry.get("timestamp") if entry else None,
        "inputs": list(STEP_IO.get(step_name, {}).get("inputs", [])),
        "outputs": list(STEP_IO.get(step_name, {}).get("outputs", [])),
    }
