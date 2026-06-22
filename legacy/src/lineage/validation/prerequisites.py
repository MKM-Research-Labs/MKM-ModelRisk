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

"""Prerequisite resolution — determine which pipeline steps need re-running."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from lineage.validation._helpers import _outputs_exist
from lineage.validation.freshness import check_inputs_fresh


def resolve_prerequisites(
    target_steps: list[str],
    data_dir: Path | str | None = None,
) -> list[str]:
    """Return prerequisite steps that need to run before *target_steps*,
    in topological order.

    A prerequisite needs to run if:
    - It has never been recorded in the manifest AND its outputs are
      missing/empty on disk, OR
    - Its inputs are stale (producer hashes changed since last run).

    Skips steps whose outputs already exist on disk even without a
    manifest entry (handles pre-lineage data).

    Args:
        target_steps: Step names the user wants to execute.
        data_dir:     Root data directory (e.g. ``data/input/thames``).

    Returns:
        Ordered list of prerequisite step names that need to run first.
        Empty list if everything is fresh.
    """
    from graphlib import TopologicalSorter
    import lineage.validation as _val

    DEPENDENCY_GRAPH = _val.DEPENDENCY_GRAPH

    if data_dir is not None:
        data_dir = Path(data_dir)

    # 1. Collect transitive prerequisites (excluding targets themselves)
    targets = set(target_steps)
    needed: set[str] = set()
    queue: deque[str] = deque()
    for t in target_steps:
        queue.extend(DEPENDENCY_GRAPH.get(t, []))
    while queue:
        dep = queue.popleft()
        if dep not in needed:
            needed.add(dep)
            queue.extend(DEPENDENCY_GRAPH.get(dep, []))
    # Remove targets — we only want prerequisites, not the steps themselves
    needed -= targets

    if not needed:
        return []

    # 2. Filter to only those that are stale or missing
    manifest = _val.load_manifest()
    stale: list[str] = []

    for step in needed:
        step_entry = manifest.get("steps", {}).get(step)
        if step_entry is None:
            # Never recorded — check if outputs exist on disk
            if data_dir and _outputs_exist(step, data_dir):
                continue  # files present, assume OK
            stale.append(step)
        else:
            # Recorded — check if inputs are still fresh
            fresh, _ = check_inputs_fresh(step)
            if not fresh:
                stale.append(step)

    if not stale:
        return []

    # 3. Topological sort of stale steps
    ts = TopologicalSorter()
    for step in stale:
        deps_in_stale = [d for d in DEPENDENCY_GRAPH.get(step, [])
                         if d in stale]
        ts.add(step, *deps_in_stale)

    return list(ts.static_order())
