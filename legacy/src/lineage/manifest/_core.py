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
Data lineage manifest — records pipeline step execution with content hashes.

Each step records its inputs, outputs, parameters, and timing so that
downstream consumers can verify data freshness (BCBS 239 Principle 3).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
try:
    from config import config as _cfg
    _project_root = (
        Path(_cfg.get_project_root())
        if hasattr(_cfg, "get_project_root")
        else Path(_cfg.project_root)
    )
except (ImportError, AttributeError):
    _project_root = Path(__file__).resolve().parents[2]

LINEAGE_PATH = _project_root / "data" / "data_lineage.json"

from lineage.manifest._topology import (
    DEPENDENCY_GRAPH,
    EXTERNAL_INPUTS,
    OPTIONAL_STEPS,
    STEP_IO,
)

# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------
from config.port import LINEAGE_CHUNK_SIZE as _CHUNK  # 64 KB


def hash_file(path: Path) -> str:
    """SHA-256 of a single file, streamed in 64 KB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_directory(dir_path: Path, pattern: str = "*.json") -> tuple:
    """Aggregate hash of sorted(filename + ':' + file_hash) in *dir_path*.

    Returns (hex_digest, file_count).
    """
    h = hashlib.sha256()
    files = sorted(dir_path.glob(pattern))
    for fp in files:
        if fp.is_file():
            h.update(f"{fp.name}:{hash_file(fp)}".encode())
    return h.hexdigest(), len(files)

# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    """Load the lineage manifest, or return an empty skeleton."""
    if LINEAGE_PATH.exists():
        try:
            with open(LINEAGE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Corrupt lineage manifest, resetting: %s", exc)
    return {"runs": {}, "steps": {}}


def save_manifest(manifest: dict) -> None:
    """Atomic write — write to temp then rename."""
    LINEAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(LINEAGE_PATH.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2)
        os.replace(tmp, str(LINEAGE_PATH))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def get_current_run_id() -> str:
    """Generate a run ID from the current timestamp."""
    return datetime.now().strftime("run-%Y%m%d-%H%M%S")


def _hash_artifact(path: Path) -> dict:
    """Hash a file or directory, returning metadata dict."""
    if path.is_dir():
        digest, count = hash_directory(path)
        return {"hash": digest, "file_count": count, "type": "directory"}
    if path.is_file():
        return {"hash": hash_file(path), "type": "file"}
    return {"hash": None, "type": "missing"}


def pre_hash_inputs(inputs: dict) -> dict:
    """Hash input artifacts *before* a pipeline step runs.

    Call this before the step executes, then pass the result as
    ``input_hashes`` to :func:`record_step`.  This is essential for
    steps that mutate their own input files (e.g. ``synthetic_gauges``
    overwrites ``gauge.json``, ``hazard`` writes back to ``gaugets/``).
    """
    return {k: _hash_artifact(Path(v)) for k, v in inputs.items()}


def record_step(
    step_name: str,
    generator: str,
    inputs: dict,
    outputs: dict,
    parameters: dict,
    elapsed_seconds: float,
    status: str = "success",
    run_id: str | None = None,
    input_hashes: dict | None = None,
) -> dict:
    """Record a pipeline step execution in the manifest.

    *inputs* and *outputs* map logical names to Path objects.

    If *input_hashes* is provided it is used directly (pre-computed hashes
    captured **before** the step ran, which is essential for steps that
    mutate their own input files).  Otherwise inputs are hashed now.

    Returns the step entry that was written.
    """
    run_id = run_id or get_current_run_id()
    manifest = load_manifest()

    if input_hashes is None:
        input_hashes = {k: _hash_artifact(Path(v)) for k, v in inputs.items()}
    output_hashes = {k: _hash_artifact(Path(v)) for k, v in outputs.items()}

    import os as _os
    import socket as _socket

    entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "user": _os.environ.get("USER", "unknown"),
        "hostname": _socket.gethostname(),
        "generator": generator,
        "status": status,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "parameters": parameters,
        "inputs": input_hashes,
        "outputs": output_hashes,
    }

    manifest["steps"][step_name] = entry
    manifest["runs"].setdefault(run_id, []).append(step_name)
    save_manifest(manifest)
    return entry


# ---------------------------------------------------------------------------
# Manifest repair
# ---------------------------------------------------------------------------

def repair_manifest(data_dir: str | Path | None = None) -> dict:
    """Re-hash all on-disk artifacts and rebuild a consistent manifest.

    Walks every step in ``STEP_IO`` in topological order.  For each step
    whose outputs exist on disk, hashes all inputs and outputs and writes
    (or overwrites) the manifest entry so that the recorded hashes match
    the current state of the files.  Steps whose outputs are missing are
    skipped with a warning.

    Existing metadata (run_id, timestamp, generator, parameters) is
    preserved when the step already has a manifest entry; otherwise
    sensible defaults are used.

    Returns a summary dict: ``{"repaired": [...], "skipped": [...]}``.
    """
    from graphlib import TopologicalSorter

    if data_dir is None:
        try:
            from config import PortfolioConfig
            data_dir = Path(PortfolioConfig().get_input_dir())
        except (ImportError, AttributeError):
            catchment = os.getenv("MKM_CATCHMENT", "thames")
            data_dir = Path(__file__).resolve().parents[2] / "data" / "input" / catchment
    else:
        data_dir = Path(data_dir)

    manifest = load_manifest()
    run_id = datetime.now().strftime("repair-%Y%m%d-%H%M%S")
    ts_now = datetime.now().isoformat()

    # Topological order
    sorter = TopologicalSorter(DEPENDENCY_GRAPH)
    topo_order = list(sorter.static_order())

    repaired: list[str] = []
    skipped: list[str] = []

    for step_name in topo_order:
        io = STEP_IO.get(step_name)
        if io is None:
            continue

        # Check all outputs exist
        all_outputs_present = True
        for out in io["outputs"]:
            path = data_dir / out
            if out.endswith("/"):
                if not path.is_dir() or not any(path.iterdir()):
                    all_outputs_present = False
                    break
            else:
                if not path.is_file():
                    all_outputs_present = False
                    break

        if not all_outputs_present:
            skipped.append(step_name)
            continue

        # Hash inputs
        input_hashes = {}
        for inp in io["inputs"]:
            path = data_dir / inp
            input_hashes[inp] = _hash_artifact(path)

        # Hash outputs
        output_hashes = {}
        for out in io["outputs"]:
            path = data_dir / out
            output_hashes[out] = _hash_artifact(path)

        # Preserve existing metadata or use defaults
        existing = manifest.get("steps", {}).get(step_name, {})
        entry = {
            "run_id": existing.get("run_id", run_id),
            "timestamp": existing.get("timestamp", ts_now),
            "generator": existing.get("generator", "unknown"),
            "status": "success",
            "elapsed_seconds": existing.get("elapsed_seconds", 0.0),
            "parameters": existing.get("parameters", {}),
            "inputs": input_hashes,
            "outputs": output_hashes,
        }

        manifest["steps"][step_name] = entry
        repaired.append(step_name)

    # Update runs index
    manifest["runs"][run_id] = repaired
    save_manifest(manifest)

    return {"repaired": repaired, "skipped": skipped}
