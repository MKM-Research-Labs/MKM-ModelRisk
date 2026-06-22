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

"""Internal helpers for lineage validation — hashing, producer lookup."""

from __future__ import annotations

import logging
from pathlib import Path

from lineage.manifest import (
    DEPENDENCY_GRAPH,
    STEP_IO,
    hash_directory,
    hash_file,
)

logger = logging.getLogger(__name__)

_MISSING = object()  # sentinel: hash key not present at all


def _output_step_map() -> dict:
    """Map each output filename to the step that produces it.

    When multiple steps produce the same artifact (e.g. ``gauges`` and
    ``synthetic_gauges`` both output ``gauge.json``), the *last* writer
    in topological order wins — that step's recorded hash is the one
    downstream consumers should match.
    """
    from graphlib import TopologicalSorter

    sorter = TopologicalSorter(DEPENDENCY_GRAPH)
    topo_order = list(sorter.static_order())

    mapping: dict[str, str] = {}
    for step in topo_order:
        io = STEP_IO.get(step)
        if io is None:
            continue
        for out in io["outputs"]:
            mapping[out] = step      # later writers overwrite earlier ones
    return mapping


def _find_producer(step_name: str, artifact: str) -> str | None:
    """Find the correct producer of *artifact* for *step_name*.

    When multiple steps output the same file (e.g. ``gauge.json`` is
    written by both ``gauges`` and ``synthetic_gauges``), the producer
    is the **latest upstream dependency** of *step_name* that outputs
    the artifact.  This ensures each consumer is validated against the
    version of the file it actually consumed at pipeline runtime.
    """
    from graphlib import TopologicalSorter

    # All transitive dependencies of this step
    deps: set[str] = set()
    queue = list(DEPENDENCY_GRAPH.get(step_name, []))
    while queue:
        dep = queue.pop()
        if dep not in deps:
            deps.add(dep)
            queue.extend(DEPENDENCY_GRAPH.get(dep, []))

    # Among dependencies, find all that produce this artifact
    candidates = []
    sorter = TopologicalSorter(DEPENDENCY_GRAPH)
    topo_order = list(sorter.static_order())

    for step in topo_order:
        if step in deps:
            io = STEP_IO.get(step, {})
            if artifact in io.get("outputs", []):
                candidates.append(step)

    # Last in topo order = latest writer among our dependencies
    return candidates[-1] if candidates else None


def _current_hash(artifact_name: str, manifest_step: dict):
    """Look up the recorded hash for *artifact_name* in a step's outputs.

    Returns the hash string, ``None`` when the key is explicitly null,
    or ``_MISSING`` when the entry or hash key is absent entirely.
    """
    entry = manifest_step.get("outputs", {}).get(artifact_name)
    if entry and isinstance(entry, dict):
        return entry.get("hash", _MISSING)
    return _MISSING


def _resolve_data_dir() -> Path:
    """Resolve the pipeline data directory for the active catchment."""
    try:
        from config import PortfolioConfig
        return Path(PortfolioConfig().get_input_dir())
    except (ImportError, AttributeError):
        import os
        catchment = os.getenv("MKM_CATCHMENT", "thames")
        return Path(__file__).resolve().parents[3] / "data" / "input" / catchment


def _live_hash(artifact: str, data_dir: Path | None = None) -> str | None:
    """Hash an artifact on disk, returning None if it doesn't exist."""
    if data_dir is None:
        data_dir = _resolve_data_dir()
    path = data_dir / artifact
    if path.is_dir() and any(path.iterdir()):
        digest, _ = hash_directory(path)
        return digest
    if path.is_file():
        return hash_file(path)
    return None


def _outputs_exist(step_name: str, data_dir: Path) -> bool:
    """Check whether all outputs of a step exist on disk (non-empty)."""
    io = STEP_IO.get(step_name)
    if io is None:
        return False
    for output in io["outputs"]:
        path = data_dir / output
        if output.endswith("/"):
            if not path.is_dir() or not any(path.iterdir()):
                return False
        else:
            if not path.is_file():
                return False
    return True
