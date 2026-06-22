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

"""On-demand single-asset PRS recompute — the instant "re-depth" shortcut.

For a property edit that only moves the flood threshold (FloorLevelMeters or
BRIFloodScore), recompute the PRS spread decomposition WITHOUT re-running the
flood propagation. Spike 1 established that each stored event's
``attenuated_wse_m`` (the property peak water-surface elevation) is independent
of floor / ground / BRI, and that the batch's flood depth is exactly
``max(0, attenuated_wse_m − threshold)``. So a new floor just re-thresholds the
stored water levels:

    new_depth_i = max(0, attenuated_wse_m_i − (threshold + Δfloor))

The threshold is read back from the data itself (``attenuated_wse_m − depth`` on
any flooded event — constant per file, validated to 0.0000 spread), so we never
reconstruct it from metadata (which is wrong for the SHD mode). Counting uses the
shared ``is_prs_flood`` and the spread is the same ``count / num_storms × 10000``
the batch uses, so the pricing stays single-source.

Returns ``None`` (→ caller falls back to the scoped-subprocess oracle) for edits
or data this shortcut cannot reproduce exactly: ground-level edits (mode-specific
geometry) and compound/pulse events (stored peak WSE is lossy when not flooded).
"""

from __future__ import annotations

import json
from pathlib import Path

from models.floodrisk.depth_damage import bri_floor_uplift, is_prs_flood

# The four decomposition modes (normal / synthetic-elevation / synthetic-distance
# / BRI-adjusted-floor) and the per-asset timeseries directory each lives in.
MODES = ("property", "she", "shd", "bri")
PROPERTY_MODE_DIRS = {
    "property": "propertyts", "she": "propertytse",
    "shd": "propertytsd", "bri": "propertytsb",
}
COMMERCIAL_MODE_DIRS = {
    "property": "commercialts", "she": "commercialtse",
    "shd": "commercialtsd", "bri": "commercialtsb",
}
MODE_DIRS_BY_ASSET = {"property": PROPERTY_MODE_DIRS, "commercial": COMMERCIAL_MODE_DIRS}
# mode -> spread_decomposition key.
DECOMP_KEY = {
    "property": "property_spread_bps",
    "she": "she_spread_bps",
    "shd": "shd_spread_bps",
    "bri": "bri_spread_bps",
}


def _has_compound(ts: dict) -> bool:
    return any(e.get("compound") for e in ts.get("flood_events", []))


def _threshold(ts: dict) -> float:
    """Current flood threshold (metres AOD) for a mode's timeseries file.

    Derived from the data — ``attenuated_wse_m − flood_depth_m`` on any flooded
    event — which is exactly the effective threshold the batch used and is
    constant per file (validated). Falls back to stored geometry only when no
    event floods (then a raise stays dry anyway).
    """
    for e in ts.get("flood_events", []):
        if e.get("flood_depth_m", 0) > 0:
            return e["attenuated_wse_m"] - e["flood_depth_m"]
    return ts.get("elevation_m", 0.0) + ts.get("floor_level_m", 0.0)


def severe_count(ts: dict, delta_m: float) -> int:
    """Severe-flood count after shifting the flood threshold by ``delta_m``."""
    threshold = _threshold(ts) + delta_m
    n = 0
    for e in ts.get("flood_events", []):
        new_depth = max(0.0, e["attenuated_wse_m"] - threshold)
        # Use the shared predicate so the trigger rule stays single-source.
        if is_prs_flood({"flooded": new_depth > 0,
                         "exceeded_severe": e.get("exceeded_severe", False)}):
            n += 1
    return n


def mode_deltas(field: str, old, new):
    """Per-mode floor-threshold shift (metres) for a CDM edit.

    Returns ``None`` when the shortcut cannot handle the field exactly (ground
    level, or anything that is not a pure floor move) — the caller then uses the
    subprocess oracle.
    """
    if old is None or new is None:
        return None
    if field.endswith("FloorLevelMeters") and "BRIAdjusted" not in field:
        d = float(new) - float(old)          # floor enters every mode identically
        return {m: d for m in MODES}
    if field.endswith("BRIFloodScore"):
        d = bri_floor_uplift(float(new)) - bri_floor_uplift(float(old))
        return {"bri": d}                    # only the BRI-adjusted floor moves
    return None


def recompute_decomposition(prop_id: str, field: str, old, new, *,
                            ts_root, before_decomp: dict, num_storms: int,
                            mode_dirs: dict = PROPERTY_MODE_DIRS):
    """Recomputed ``spread_decomposition`` after the edit, or ``None`` to fall back.

    ``ts_root`` is the directory holding the asset's timeseries dirs (the read-only
    baseline or a sandbox workspace); ``mode_dirs`` maps each mode to its dir
    (property vs commercial). ``before_decomp`` seeds the gauge spread (unchanged)
    and any stages the edit does not touch.
    """
    deltas = mode_deltas(field, old, new)
    if deltas is None or not num_storms:
        return None
    after = dict(before_decomp or {})
    for mode, delta in deltas.items():
        path = Path(ts_root) / mode_dirs[mode] / f"{prop_id}.json"
        if not path.exists():
            continue
        ts = json.loads(path.read_text())
        if _has_compound(ts):
            return None                      # lossy for compound events → oracle
        count = severe_count(ts, delta)
        after[DECOMP_KEY[mode]] = round((count / num_storms) * 10000, 2)
    return after
