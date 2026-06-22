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

"""Oracle check for recompute.py — validate the instant shortcut against the
REAL generator for an actual floor edit.

For a chosen property and a floor change, compare:
  * shortcut  — recompute.severe_count over the stored timeseries (no re-run);
  * oracle    — the actual PropertyTimeSeriesGenerator re-run with the edited
                FloorLevelMeters, in a temp workspace (MKM_CATCHMENT_INPUT_OVERRIDE),
                so nothing touches data/.

Run:  python tools/cdm_property_editor/_recompute_oracle.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parent.parent
SRC_DIR = REPO_ROOT / "src"
for _p in (str(SRC_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from models.floodrisk.depth_damage import is_prs_flood  # noqa: E402

import recompute  # noqa: E402  (same dir)

THAMES = REPO_ROOT / "data" / "input" / "thames"
# Inputs the property timeseries generator reads (everything EXCEPT property.json,
# which we edit, and the property* OUTPUT dirs, which it writes).
INPUT_LINKS = ["gauge.json", "storm_sequences.json", "storm_control.json",
               "gaugets", "sequence_gauge", "gaugehd"]


def _count_severe(ts_path: Path) -> int:
    ts = json.loads(ts_path.read_text())
    return sum(1 for e in ts.get("flood_events", []) if is_prs_flood(e))


def _pick_property():
    """A property with a healthy severe-flood count, and its current floor."""
    prop_json = json.loads((THAMES / "property.json").read_text())
    floors = {}
    for r in prop_json["properties"]:
        ph = r["PropertyHeader"]
        pid = ph["Header"]["PropertyID"]
        floors[pid] = ph["Construction"].get("FloorLevelMeters", 0.0)
    best, best_n = None, -1
    for f in (THAMES / "propertyts").glob("PROP-*.json"):
        n = _count_severe(f)
        if n > best_n:
            best, best_n = f.stem, n
    return best, floors[best], best_n


def _oracle_count(prop_id: str, new_floor: float) -> int:
    """Re-run the REAL ts generator with the edited floor; return severe count."""
    work = Path(tempfile.mkdtemp(prefix="recompute_oracle_"))
    try:
        for name in INPUT_LINKS:
            src = THAMES / name
            if src.exists():
                (work / name).symlink_to(src)
        # edited property.json (copy, not symlink)
        prop_json = json.loads((THAMES / "property.json").read_text())
        for r in prop_json["properties"]:
            if r["PropertyHeader"]["Header"]["PropertyID"] == prop_id:
                r["PropertyHeader"]["Construction"]["FloorLevelMeters"] = new_floor
        (work / "property.json").write_text(json.dumps(prop_json))

        code = (
            "import os,sys\n"
            f"os.environ['MKM_CATCHMENT_INPUT_OVERRIDE']=r'{work}'\n"
            "os.environ['MKM_CATCHMENT']='thames'\n"
            f"sys.path[:0]=[r'{SRC_DIR}',r'{REPO_ROOT}']\n"
            "from config import config\n"
            "from port.src.property import propertyts\n"
            "propertyts.PropertyTimeSeriesGenerator("
            "output_dir=config.get_input_dir(), mode='normal', verbose=False).generate()\n"
        )
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, timeout=600)
        out = work / "propertyts" / f"{prop_id}.json"
        if not out.exists():
            raise RuntimeError(f"generator produced no output\nSTDERR:\n{r.stderr[-2000:]}")
        return _count_severe(out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    num_storms = json.loads((THAMES / "propertyhc.json").read_text())["metadata"]["num_storms"]
    pid, floor, base_n = _pick_property()
    print(f"property {pid}: floor={floor} m, baseline severe floods={base_n}, num_storms={num_storms}\n")

    print(f"{'edit':>14} | {'shortcut':>8} | {'oracle':>7} | match")
    print("-" * 48)
    all_ok = True
    for dfloor in (0.0, 0.5, 1.0, 2.0, -0.5):
        new_floor = round(floor + dfloor, 4)
        ts = json.loads((THAMES / "propertyts" / f"{pid}.json").read_text())
        short = recompute.severe_count(ts, dfloor)
        orc = _oracle_count(pid, new_floor)
        ok = short == orc
        all_ok &= ok
        print(f"{('Δ%+.2f m' % dfloor):>14} | {short:>8} | {orc:>7} | {'OK' if ok else 'MISMATCH'}")
    print("\nRESULT:", "ALL MATCH ✓" if all_ok else "MISMATCH ✗")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
