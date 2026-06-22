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

"""Staleness detection — BCBS 239 Principle 6 (timeliness)."""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

import lineage.manifest as _manifest
from lineage.validation._helpers import (
    _current_hash,
    _find_producer,
    _live_hash,
    _MISSING,
    _output_step_map,
    _resolve_data_dir,
)

logger = logging.getLogger(__name__)


def check_inputs_fresh(step_name: str) -> tuple:
    """Check whether every input of *step_name* still matches its producer's
    recorded output hash.

    Returns ``(all_fresh, issues)`` where *issues* is a list of human-readable
    strings describing any mismatches.

    When a recorded hash is ``None`` (artifact was missing at recording time)
    but the file now exists on disk, falls back to a live hash comparison so
    that stale null entries don't block validation indefinitely.
    """
    # Import via the parent package so monkeypatch / mock.patch on
    # ``lineage.validation.load_manifest`` takes effect.
    import lineage.validation as _val
    manifest = _val.load_manifest()
    step_io = _val.STEP_IO.get(step_name)
    if step_io is None:
        return False, [f"Unknown step: {step_name}"]

    # Fallback map for artifacts with no dependency-graph producer
    output_map = _output_step_map()
    issues: list[str] = []
    data_dir: Path | None = None  # lazily resolved

    for inp in step_io["inputs"]:
        # External inputs (config files) are compared against disk, not a producer
        if inp in _manifest.EXTERNAL_INPUTS:
            consumer_entry = manifest.get("steps", {}).get(step_name)
            if consumer_entry is None:
                issues.append(f"Step '{step_name}' has never run")
                continue
            consumed = consumer_entry.get("inputs", {}).get(inp, {}).get("hash")
            if consumed is None:
                continue  # never recorded — skip
            if data_dir is None:
                data_dir = _resolve_data_dir()
            live = _live_hash(inp, data_dir)
            if live is not None and live != consumed:
                issues.append(
                    f"External input '{inp}' changed on disk since "
                    f"'{step_name}' last ran"
                )
            continue

        # Prefer dependency-aware producer; fall back to global map
        producer = _find_producer(step_name, inp) or output_map.get(inp)
        if producer is None:
            issues.append(f"No producer found for input '{inp}'")
            continue

        producer_entry = manifest.get("steps", {}).get(producer)
        if producer_entry is None:
            issues.append(
                f"Producer '{producer}' for input '{inp}' has never run"
            )
            continue

        recorded = _current_hash(inp, producer_entry)
        if recorded is _MISSING:
            # Hash key completely absent — no data to compare
            issues.append(
                f"No hash recorded for '{inp}' in step '{producer}'"
            )
            continue
        if recorded is None:
            # Explicitly null (artifact was missing at record time) —
            # fall back to live disk hash so stale nulls don't block forever
            if data_dir is None:
                data_dir = _resolve_data_dir()
            recorded = _live_hash(inp, data_dir)
            if recorded is None:
                issues.append(
                    f"No hash recorded for '{inp}' in step '{producer}' "
                    f"and artifact missing on disk"
                )
                continue

        # Compare with what the consumer recorded at its own run time
        consumer_entry = manifest.get("steps", {}).get(step_name)
        if consumer_entry is None:
            issues.append(f"Step '{step_name}' has never run")
            continue

        consumed = consumer_entry.get("inputs", {}).get(inp, {}).get("hash")
        if consumed is None:
            # Check if hash key exists but is explicitly null vs absent
            inp_entry = consumer_entry.get("inputs", {}).get(inp, {})
            if "hash" in inp_entry and inp_entry["hash"] is None:
                # Explicitly null — fall back to live hash
                if data_dir is None:
                    data_dir = _resolve_data_dir()
                consumed = _live_hash(inp, data_dir)
                if consumed is None:
                    issues.append(
                        f"Step '{step_name}' has no recorded hash for input "
                        f"'{inp}' and artifact missing on disk"
                    )
                    continue
            else:
                issues.append(
                    f"Step '{step_name}' has no recorded hash for input '{inp}'"
                )
                continue

        if consumed != recorded:
            issues.append(
                f"Input '{inp}' is stale: producer '{producer}' hash "
                f"changed ({consumed[:12]}.. -> {recorded[:12]}..)"
            )

    return len(issues) == 0, issues


def check_step_prerequisites(step_name: str) -> tuple:
    """Verify that all upstream steps have been recorded in the manifest.

    Returns ``(ok, missing_list)``.
    """
    import lineage.validation as _val
    manifest = _val.load_manifest()
    deps = _val.DEPENDENCY_GRAPH.get(step_name, [])
    missing = [d for d in deps if d not in manifest.get("steps", {})]
    return len(missing) == 0, missing


def get_stale_downstream(step_name: str) -> list:
    """BFS from *step_name* to find all transitive downstream steps."""
    import lineage.validation as _val
    DEPENDENCY_GRAPH = _val.DEPENDENCY_GRAPH

    reverse: dict[str, list[str]] = {k: [] for k in DEPENDENCY_GRAPH}
    for step, deps in DEPENDENCY_GRAPH.items():
        for dep in deps:
            reverse.setdefault(dep, []).append(step)

    visited: set[str] = set()
    queue: deque[str] = deque(reverse.get(step_name, []))
    result: list[str] = []

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        result.append(current)
        queue.extend(reverse.get(current, []))

    return result
