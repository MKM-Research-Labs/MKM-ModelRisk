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

"""Provenance tracing — scans data files for an entity ID across the pipeline."""


def _trace_data(lineage, data_type, data_id):
    """Trace a data_type/data_id through the pipeline by searching data files.

    Scans actual JSON files and directories for the entity ID, returning
    a list of provenance steps with file locations and context.
    Supports: Gauge, Property, Trade (PRS), Counterparty.
    """
    from pathlib import Path

    from config import config

    input_dir = Path(config.get_input_dir())
    classifiers_dir = Path(config.get_classifiers_dir())
    blotter_dir = Path(config.get_trading_dir())

    trace = []

    def _add(step, file_path, role, context=""):
        """Append a trace entry."""
        # Make path relative to input_dir for display
        try:
            rel = str(Path(file_path).relative_to(input_dir.parent.parent))
        except ValueError:
            rel = str(file_path)
        trace.append({
            "step": step,
            "file": rel,
            "role": role,
            "context": context,
        })

    def _search_json(path, entity_id):
        """Check if entity_id appears anywhere in a JSON file."""
        try:
            text = path.read_text(errors="ignore")
            return entity_id in text
        except Exception:
            return False

    def _search_dir_files(dir_path, entity_id):
        """Check if entity_id appears as a filename stem or in file contents."""
        if not dir_path.is_dir():
            return []
        hits = []
        for f in dir_path.iterdir():
            if entity_id in f.stem:
                hits.append(f)
            elif f.suffix == ".json" and f.stat().st_size < 50_000_000:
                if _search_json(f, entity_id):
                    hits.append(f)
        return hits

    # ── Gauge trace ──────────────────────────────────────────────────
    if data_type.lower() == "gauge":
        # Step 1: gauge.json (master data)
        gauge_path = input_dir / "gauge.json"
        if gauge_path.exists() and _search_json(gauge_path, data_id):
            _add("gauges", gauge_path, "origin",
                 "Master gauge record (CDM FloodGauge)")

        # Step 4: gaugehd/ (historical daily)
        hd_dir = input_dir / "gaugehd"
        if hd_dir.is_dir():
            for f in hd_dir.glob(f"*{data_id}*"):
                _add("gaugehd", f, "derived",
                     "Historical daily observations")
                break

        # Step 5: gaugets/ (time series)
        ts_file = input_dir / "gaugets" / f"{data_id}.json"
        if ts_file.exists():
            _add("stressm", ts_file, "derived",
                 "168h storm simulation time series")

        # Step 5: stressm/ (storm sequences — split per-gauge directory)
        sg_dir = input_dir / "sequence_gauge"
        sg_legacy = input_dir / "sequence_gauge_summary.json"
        if sg_dir.is_dir():
            # Search per-gauge file matching data_id
            sg_file = sg_dir / f"{data_id}.json"
            if sg_file.exists():
                _add("stressm", sg_file, "derived",
                     "Per-sequence peak water levels & flood flags")
            elif (sg_dir / "_index.json").exists() and _search_json(
                    sg_dir / "_index.json", data_id):
                _add("stressm", sg_dir / "_index.json", "derived",
                     "Per-sequence peak water levels & flood flags")
        elif sg_legacy.exists() and _search_json(sg_legacy, data_id):
            _add("stressm", sg_legacy, "derived",
                 "Per-sequence peak water levels & flood flags")

        # Step 6: gaugehc.json (hazard curves)
        hc_path = input_dir / "gaugehc.json"
        if hc_path.exists() and _search_json(hc_path, data_id):
            _add("hazard", hc_path, "derived",
                 "GEV hazard curve (return periods & probabilities)")

        # Classifiers
        clf_path = classifiers_dir / f"{data_id}.joblib"
        if clf_path.exists():
            _add("classifiers", clf_path, "derived",
                 "Trained GBM flood classifier")
        summary_path = classifiers_dir / "training_summary.json"
        if summary_path.exists() and _search_json(summary_path, data_id):
            _add("classifiers", summary_path, "derived",
                 "Classifier metrics (AUC, accuracy, thresholds)")

        # Blotter: market state
        ms_path = blotter_dir / "market_state.json"
        if ms_path.exists() and _search_json(ms_path, data_id):
            _add("blotter", ms_path, "consumed",
                 "Hazard term structure (yield curve per trigger)")

        # PRS trades referencing this gauge
        prs_dir = input_dir / "prs"
        if prs_dir.is_dir():
            trade_hits = _search_dir_files(prs_dir, data_id)
            for th in trade_hits[:5]:  # cap at 5
                _add("blotter", th, "consumed",
                     "PRS trade referencing gauge in basket")

    # ── Property trace ───────────────────────────────────────────────
    elif data_type.lower() == "property":
        prop_path = input_dir / "property.json"
        if prop_path.exists() and _search_json(prop_path, data_id):
            _add("properties", prop_path, "origin",
                 "Master property record (CDM PropertyHeader)")

        # Mortgage
        mtg_path = input_dir / "loan.json"
        if mtg_path.exists() and _search_json(mtg_path, data_id):
            _add("mortgages", mtg_path, "derived",
                 "Linked mortgage (LTV, amortisation, terms)")

        # propertyts/
        pts_file = input_dir / "propertyts" / f"{data_id}.json"
        if pts_file.exists():
            _add("propertyts", pts_file, "derived",
                 "Flood event time series (storm impacts)")

        # propertyhc.json
        phc_path = input_dir / "propertyhc.json"
        if phc_path.exists() and _search_json(phc_path, data_id):
            _add("propertyhc", phc_path, "derived",
                 "Property hazard curve (interpolated from gauges)")

    # ── Trade trace ──────────────────────────────────────────────────
    elif data_type.lower() in ("trade", "prs"):
        prs_file = input_dir / "prs" / f"{data_id}.json"
        if prs_file.exists():
            _add("blotter", prs_file, "origin",
                 "PRS trade confirmation (CDM PhysicalSwap)")

        # Trade marks
        marks_path = blotter_dir / "trade_marks.json"
        if marks_path.exists() and _search_json(marks_path, data_id):
            _add("blotter", marks_path, "consumed",
                 "Trade close-out mark / settlement")

        # EOD snapshots
        eod_dir = blotter_dir / "eod"
        if eod_dir.is_dir():
            eod_hits = _search_dir_files(eod_dir, data_id)
            for eh in eod_hits[:3]:
                _add("blotter", eh, "consumed",
                     "EOD snapshot (P&L, position)")

    # ── Counterparty trace ───────────────────────────────────────────
    elif data_type.lower() == "counterparty":
        ctpy_path = input_dir / "counterparty.json"
        if ctpy_path.exists() and _search_json(ctpy_path, data_id):
            _add("counterparties", ctpy_path, "origin",
                 "Counterparty master record (CDM Party)")

        # PRS trades referencing this counterparty
        prs_dir = input_dir / "prs"
        if prs_dir.is_dir():
            trade_hits = _search_dir_files(prs_dir, data_id)
            for th in trade_hits[:5]:
                _add("blotter", th, "consumed",
                     "PRS trade with this counterparty")

    # ── Generic fallback ─────────────────────────────────────────────
    else:
        # Scan all JSON files in input_dir (non-recursive, capped)
        for f in sorted(input_dir.glob("*.json"))[:20]:
            if _search_json(f, data_id):
                _add("unknown", f, "found",
                     f"ID found in {f.name}")

    return trace
