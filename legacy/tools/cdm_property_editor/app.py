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
Standalone CDM Asset Review — side tool.

A self-contained Flask app for browsing the asset CDMs as a governance-style
workspace: a top tab bar (Gauges · Properties · Commercials · Mortgage ·
Commercial Loan), a left-hand list of every record in the active tab, and a
per-row review icon that opens the full CDM record in a centered modal with
section tabs. It is schema-driven: each tab's form structure comes straight
from the canonical CDM schema for that asset class.

This is a sandbox tool, deliberately isolated from the production scene:
  * It reads/writes ONLY sandbox copies under
    ``tools/cdm_property_editor/data/<asset>_sandbox.json``.
  * Each sandbox is seeded once from the existing simulated thames portfolio
    under ``data/input/thames/``. The real ``data/`` tree is never modified.

Run:
    source .venv/bin/activate
    python tools/cdm_property_editor/app.py
    # then open http://127.0.0.1:5057
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# --- Locate the repo and make the CDM schemas importable --------------------
TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parent.parent
SRC_DIR = REPO_ROOT / "src"
# Importing the CDM schemas pulls in the wider `port` package whose __init__
# chain reaches the top-level `config` package at the repo root — so both
# must be importable.
for _p in (str(SRC_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from port.cdm.asset.commercial.schema import COMMERCIAL_SCHEMA  # noqa: E402
from port.cdm.asset.loan.schema import MORTGAGE_SCHEMA  # noqa: E402
from port.cdm.asset.residential.schema import PROPERTY_SCHEMA  # noqa: E402
from port.cdm.ctpy._schema import COUNTERPARTY_SCHEMA  # noqa: E402
from port.cdm.gauge.schema import GAUGE_SCHEMA  # noqa: E402
from lineage.field_usage import AMBER_PREFIXES, EXACT_FIELDS, TIER_META  # noqa: E402
from lineage.field_usage.resolve import classify  # noqa: E402
from cdm_edit import descriptor_at, schema_specs, validate_value  # noqa: E402

from recompute import MODE_DIRS_BY_ASSET, recompute_decomposition  # noqa: E402

# The PRS waterfall is rendered by the main app's own renderer
# (src/static/js/property/phc_basis_waterfall.js) — reused here as a shared
# utility rather than duplicated, so the tool's PRS Waterfall tab is the exact
# same chart as the production basis-explorer right panel.
SHARED_WATERFALL_JS = SRC_DIR / "static" / "js" / "property" / "phc_basis_waterfall.js"

CATCHMENT = "thames"
INPUT_DIR = REPO_ROOT / "data" / "input" / CATCHMENT
GOLDEN_PROPERTY = REPO_ROOT / "tests" / "port" / "cdm" / "golden" / "property.json"
SANDBOX_DIR = TOOL_DIR / "data"
AUDIT_FILE = SANDBOX_DIR / "audit_log.json"
# No authentication yet — every amendment is attributed to a placeholder user
# until real users / sign-in arrive.
AUDIT_USER = "Placeholder User"


# --- Per-asset summary builders (the left-list row + modal header card) ------
def _addr(loc: dict) -> str:
    bits = [loc.get("BuildingNumber"), loc.get("StreetName"),
            loc.get("TownCity"), loc.get("Postcode")]
    return " ".join(str(b) for b in bits if b)


def _type_class(t: str | None) -> str:
    return {"residential": "badge-residential", "commercial": "badge-commercial",
            "industrial": "badge-industrial"}.get(t or "", "badge-na")


def _coords(lat, lon) -> dict:
    """Normalise a lat/lon pair to floats, or None when absent/invalid."""
    try:
        return {"lat": float(lat), "lon": float(lon)}
    except (TypeError, ValueError):
        return {"lat": None, "lon": None}


def _sum_gauge(r: dict) -> dict:
    g = r.get("FloodGauge", {})
    h = g.get("Header", {})
    loc = g.get("Location", {})
    return {"id": h.get("GaugeID"), "sub": h.get("GaugeName") or "—",
            "tag": h.get("CatchmentID") or "gauge", "tagClass": "badge-industrial",
            "value": None,
            **_coords(loc.get("GaugeLatitude"), loc.get("GaugeLongitude"))}


def _sum_property(r: dict) -> dict:
    h = r.get("PropertyHeader", {})
    hd = h.get("Header", {})
    loc = h.get("Location", {})
    return {"id": hd.get("PropertyID") or hd.get("UPRN"), "sub": _addr(loc),
            "tag": hd.get("propertyType"), "tagClass": _type_class(hd.get("propertyType")),
            "value": h.get("Valuation", {}).get("PropertyValue"),
            **_coords(loc.get("LatitudeDegrees"), loc.get("LongitudeDegrees"))}


def _sum_commercial(r: dict) -> dict:
    a = r.get("CommercialAsset", {})
    hd = a.get("Header", {})
    loc = a.get("Location", {})
    ct = a.get("CommercialAttributes", {}).get("CommercialType")
    return {"id": hd.get("PropertyID") or hd.get("UPRN"), "sub": _addr(loc),
            "tag": ct or "commercial", "tagClass": "badge-commercial",
            "value": a.get("Valuation", {}).get("PropertyValue"),
            **_coords(loc.get("LatitudeDegrees"), loc.get("LongitudeDegrees"))}


def _sum_loan(r: dict, root: str = "RLoan") -> dict:
    ln = r.get(root, {})
    h = ln.get("Header", {})
    cur = ln.get("CurrentStatus", {})
    fin = ln.get("FinancialTerms", {})
    sub = ("Property " + h.get("PropertyID")) if h.get("PropertyID") else "—"
    return {"id": h.get("RLoanID") or h.get("MortgageID"), "sub": sub,
            "tag": cur.get("AccountStatus") or "loan", "tagClass": "badge-status",
            "value": cur.get("OutstandingBalance") or fin.get("OriginalLoan")}


def _sum_commercial_loan(r: dict) -> dict:
    s = _sum_loan(r, root="Mortgage")
    meta = r.get("_commercial_meta", {})
    bits = [meta.get("commercial_type"), meta.get("borrower_type")]
    extra = " · ".join(b for b in bits if b)
    if extra:
        s["sub"] = extra
    return s


def _sum_counterparty(r: dict) -> dict:
    party = r.get("CounterpartySet", {}).get("Party", {})
    contact = party.get("ContactInformation", {})
    loc = " ".join(b for b in [contact.get("City"), contact.get("Country")] if b)
    return {"id": party.get("PartyID"), "sub": party.get("PartyName") or "—",
            "tag": loc or "counterparty", "tagClass": "badge-na", "value": None}


# --- Asset registry: drives the top tabs and every endpoint ------------------
# Order here is the top-tab order in the UI.
ASSETS: dict[str, dict] = {
    "gauge": {
        "label": "Gauges", "schema": GAUGE_SCHEMA, "file": "gauge.json",
        "container": "flood_gauges", "summary": _sum_gauge,
    },
    "property": {
        "label": "Properties", "schema": PROPERTY_SCHEMA, "file": "property.json",
        "container": "properties", "summary": _sum_property,
        "golden": GOLDEN_PROPERTY,
    },
    "commercial": {
        "label": "Commercials", "schema": COMMERCIAL_SCHEMA, "file": "commercial.json",
        "container": "commercial_assets", "summary": _sum_commercial,
    },
    "mortgage": {
        "label": "Mortgage", "schema": MORTGAGE_SCHEMA, "file": "loan.json",
        "container": "loans", "summary": _sum_loan,
    },
    "commercial_loan": {
        "label": "Commercial Loan",
        # commercial_loan records wrap the loan under a legacy "Mortgage" key
        # whose inner sections are identical to the RLoan schema.
        "schema": {"Mortgage": MORTGAGE_SCHEMA["RLoan"]},
        "file": "commercial_loan.json", "container": "commercial_loans",
        "summary": _sum_commercial_loan,
    },
    "counterparty": {
        "label": "Counterparty", "schema": COUNTERPARTY_SCHEMA,
        "file": "counterparty.json", "container": "counterparties",
        "summary": _sum_counterparty,
    },
}

# Per-asset hazard-curve files carrying the per-storm damage detail. Keyed by
# the same record id used in the item lists. Only flood-bearing assets appear.
HC_CONFIG: dict[str, dict] = {
    "property": {"file": "propertyhc.json", "container": "property_hazard_curves"},
    "commercial": {"file": "commercialhc.json", "container": "property_hazard_curves"},
}

# Fire / seismic model outputs. Both are commercial-only (keyed by CPROP id) and
# carry per-asset outcome distributions rather than per-event lists.
FIRE_FILE = INPUT_DIR / "fire" / "fire.json"
SEISMIC_FILE = INPUT_DIR / "seismic" / "seismic.json"
# Seismic damage states DS0..DS3; DS3 is the collapse state (no_collapse counts
# DS0+DS1+DS2). See src/models/seismic/damage.py.
SEISMIC_DS_LABELS = ["None", "Slight", "Moderate", "Collapse"]

# Lazy caches (read-only reference data; never written back).
_CACHE: dict = {}


def _model_assets(cache_key: str, path: Path) -> tuple:
    """(model_id, {asset_id: record}) for a fire/seismic model output file."""
    if cache_key not in _CACHE:
        model, amap = None, {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            model = doc.get("metadata", {}).get("model")
            for a in doc.get("assets", []):
                amap[a.get("asset_id")] = a
        _CACHE[cache_key] = (model, amap)
    return _CACHE[cache_key]


def _storm_type_index() -> dict:
    """sequence_id -> {type (cluster), intensity}; built once from storm_sequences."""
    if "storm_types" not in _CACHE:
        idx = {}
        p = INPUT_DIR / "storm_sequences.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as fh:
                for s in json.load(fh).get("sequences", []):
                    idx[s.get("sequence_id")] = {
                        "type": s.get("sequence_type"),
                        "intensity": s.get("intensity_category"),
                    }
        _CACHE["storm_types"] = idx
    return _CACHE["storm_types"]


def _hc_record(asset: str, rid: str) -> dict | None:
    cfg = HC_CONFIG.get(asset)
    if not cfg:
        return None
    key = f"hc_{asset}"
    if key not in _CACHE:
        p = INPUT_DIR / cfg["file"]
        if p.exists():
            with open(p, "r", encoding="utf-8") as fh:
                _CACHE[key] = json.load(fh).get(cfg["container"], {})
        else:
            _CACHE[key] = {}  # no hazard-curve file (e.g. catchment ran no commercial)
    return _CACHE[key].get(rid)


app = Flask(__name__)
# Preserve the curated CDM key order (schema + records) instead of
# alphabetising it — the section/field order is meaningful.
app.json.sort_keys = False


# --- Sandbox plumbing -------------------------------------------------------
def _sandbox_file(asset: str) -> Path:
    return SANDBOX_DIR / f"{asset}_sandbox.json"


def _seed_source(asset: str) -> Path:
    """Prefer the simulated thames file; fall back to a golden fixture if set."""
    cfg = ASSETS[asset]
    primary = INPUT_DIR / cfg["file"]
    if primary.exists():
        return primary
    golden = cfg.get("golden")
    if golden and Path(golden).exists():
        return Path(golden)
    raise FileNotFoundError(
        f"No seed source for '{asset}'. Tried {primary}"
        + (f" and {golden}" if golden else "")
        + " (is the data SSD mounted?)"
    )


def _ensure_sandbox(asset: str) -> Path:
    """Seed the asset sandbox from the simulated portfolio on first use."""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    sb = _sandbox_file(asset)
    if not sb.exists():
        shutil.copyfile(_seed_source(asset), sb)
    return sb


def _load_doc(asset: str):
    """The full sandbox document (so edits can be written back intact)."""
    with open(_ensure_sandbox(asset), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_doc(asset: str, doc) -> None:
    """Write the document back to the sandbox (never to data/)."""
    with open(_sandbox_file(asset), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)


def _records_of(doc, asset: str) -> list:
    if isinstance(doc, list):
        return doc
    return doc.get(ASSETS[asset]["container"]) or []


def _records(asset: str) -> list:
    return _records_of(_load_doc(asset), asset)


def _set_nested(rec: dict, path: str, value) -> None:
    """Set ``rec`` at a dotted ``path`` (the record root is the section key)."""
    node = rec
    segs = path.split(".")
    for seg in segs[:-1]:
        node = node.setdefault(seg, {})
    node[segs[-1]] = value


def _get_nested(rec: dict, path: str):
    node = rec
    for seg in path.split("."):
        if not isinstance(node, dict) or seg not in node:
            return None
        node = node[seg]
    return node


def _load_audit() -> list:
    if not AUDIT_FILE.exists():
        return []
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []


def _append_audit(entries: list) -> None:
    if not entries:
        return
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    log = _load_audit()
    log.extend(entries)
    with open(AUDIT_FILE, "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2)


def _record_id(asset: str, rec: dict) -> str:
    return ASSETS[asset]["summary"](rec).get("id") or ""


# --- Routes -----------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/assets")
def api_assets():
    """Top-tab list: key + label, in display order."""
    return jsonify([{"key": k, "label": v["label"]} for k, v in ASSETS.items()])


@app.route("/api/lineage")
def api_lineage():
    """Field-usage lineage: RED/AMBER/GREEN tiers + downstream chains.

    Served whole (small) so the front end can colour every field box and open
    the per-field lineage popup without a round-trip per field. Matching mirrors
    lineage.field_usage.resolve: exact path, then AMBER prefix, else GREEN.
    """
    return jsonify({
        "tiers": TIER_META,
        "exact": EXACT_FIELDS,
        "amberPrefixes": [{"prefix": p, "entry": e} for p, e in AMBER_PREFIXES],
    })


@app.route("/api/<asset>/schema")
def api_schema(asset: str):
    cfg = ASSETS.get(asset)
    if not cfg:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    return jsonify({"sections": list(cfg["schema"].keys()), "schema": cfg["schema"]})


@app.route("/api/<asset>/edit-spec")
def api_edit_spec(asset: str):
    """Per-field editor specs (input widget, menu options, numeric bounds).

    Keyed by dotted path from the record root, so the editor builds the right
    widget for each field and the same bounds the server enforces on commit.
    """
    cfg = ASSETS.get(asset)
    if not cfg:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    return jsonify(schema_specs(cfg["schema"]))


@app.route("/api/<asset>/items")
def api_items(asset: str):
    if asset not in ASSETS:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    cfg = ASSETS[asset]
    return jsonify([cfg["summary"](r) for r in _records(asset)])


@app.route("/api/<asset>/items/<rid>")
def api_item(asset: str, rid: str):
    if asset not in ASSETS:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    for rec in _records(asset):
        if _record_id(asset, rec) == rid:
            return jsonify(rec)
    return jsonify({"error": f"{asset} '{rid}' not found"}), 404


def _baseline_value(asset: str, rid: str, path: str):
    """The field value in the read-only data/ baseline (pre-sandbox edits).

    The recompute applies the change relative to the baseline (which the stored
    timeseries reflects), so before/after is always original-vs-current.
    """
    src = _seed_source(asset)
    if not src.exists():
        return None
    doc = json.loads(src.read_text())
    rec = next((r for r in _records_of(doc, asset) if _record_id(asset, r) == rid), None)
    return _get_nested(rec, path) if rec else None


def _num_storms(asset: str) -> int | None:
    cfg = HC_CONFIG.get(asset)
    p = INPUT_DIR / cfg["file"] if cfg else None
    if p and p.exists():
        return json.loads(p.read_text()).get("metadata", {}).get("num_storms")
    return None


def _maybe_recompute(asset: str, rid: str, target: dict, changed: dict) -> dict | None:
    """RED-gated before/after PRS recompute for a committed edit.

    Returns ``None`` when no RED field changed. For a RED change, returns the
    instant before/after spread decomposition (shortcut), or a not-supported
    note (gauge-threshold / ground edits → "needs a full re-run", deferred).
    Property and commercial assets are priced; others have no hazard curve.
    """
    if asset not in MODE_DIRS_BY_ASSET:
        return None
    for path in changed:
        if classify(path) != "RED":
            continue
        before = (_hc_record(asset, rid) or {}).get("spread_decomposition")
        num = _num_storms(asset)
        if not before or not num:
            return {"supported": False, "tier": "RED", "field": path,
                    "reason": "No hazard curve for this asset yet."}
        after = recompute_decomposition(
            rid, path, _baseline_value(asset, rid, path), _get_nested(target, path),
            ts_root=INPUT_DIR, before_decomp=before, num_storms=num,
            mode_dirs=MODE_DIRS_BY_ASSET[asset])
        if after is None:
            return {"supported": False, "tier": classify(path), "field": path,
                    "reason": "This edit needs a full portfolio re-run, "
                              "not an instant recompute."}
        return {"supported": True, "tier": "RED", "field": path,
                "before": before, "after": after}
    return None


# Assets the tool can CREATE (zero-portfolio / add). Maps the minted id + the
# catchment tag onto the right CDM paths so the record joins the thames pool.
NEW_ASSET: dict[str, dict] = {
    "property": {"id_path": "PropertyHeader.Header.PropertyID", "prefix": "PROP-",
                 "catchment_path": "PropertyHeader.Header.CatchmentID"},
    "commercial": {"id_path": "CommercialAsset.Header.PropertyID", "prefix": "CPROP-",
                   "catchment_path": "CommercialAsset.Header.CatchmentID"},
}


@app.route("/api/<asset>/items", methods=["POST"])
def api_create(asset: str):
    """Create a new asset record in the SANDBOX (never data/) — the add path.

    Body: ``{"changes": {dotted_path: value, ...}}`` (same shape as the editor).
    Mints the id, tags the catchment, validates every field, appends and audits
    the creation. Returns the new id so the UI can open it.
    """
    if asset not in ASSETS:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    cfg = NEW_ASSET.get(asset)
    if cfg is None:
        return jsonify({"error": f"Creating '{asset}' records is not supported yet."}), 400

    schema = ASSETS[asset]["schema"]
    changes = (request.get_json(silent=True) or {}).get("changes", {})
    coerced, errors = {}, {}
    for path, raw in changes.items():
        if raw in (None, ""):
            continue  # skip blanks — a new record need not fill every field
        descriptor = descriptor_at(schema, path)
        if descriptor is None:
            errors[path] = "not an editable schema field"
            continue
        ok, value, err = validate_value(path, descriptor, raw)
        if ok:
            coerced[path] = value
        else:
            errors[path] = err
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400

    new_id = cfg["prefix"] + uuid.uuid4().hex[:8]
    rec: dict = {}
    _set_nested(rec, cfg["id_path"], new_id)
    _set_nested(rec, cfg["catchment_path"], CATCHMENT)
    for path, value in coerced.items():
        _set_nested(rec, path, value)

    doc = _load_doc(asset)
    if isinstance(doc, list):
        doc.append(rec)
    else:
        doc.setdefault(ASSETS[asset]["container"], []).append(rec)
    _save_doc(asset, doc)
    _append_audit([{
        "timestamp": datetime.now().isoformat(timespec="seconds"), "user": AUDIT_USER,
        "asset": asset, "asset_label": ASSETS[asset]["label"], "record_id": new_id,
        "field": "(record)", "field_label": "Created record", "old": None, "new": new_id,
    }])
    return jsonify({"status": "success", "id": new_id, "record": rec})


@app.route("/api/<asset>/items/<rid>", methods=["PUT"])
def api_update(asset: str, rid: str):
    """Commit edited field values to the SANDBOX copy (never to data/).

    Body: ``{"changes": {dotted_path: new_value, ...}}``. Each change is
    validated/coerced against its schema descriptor (menu membership, numeric
    bounds, type). On any error nothing is written and the per-field errors are
    returned with 400.
    """
    if asset not in ASSETS:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    schema = ASSETS[asset]["schema"]
    changes = (request.get_json(silent=True) or {}).get("changes", {})
    if not isinstance(changes, dict):
        return jsonify({"error": "changes must be an object"}), 400

    coerced, errors = {}, {}
    for path, raw in changes.items():
        descriptor = descriptor_at(schema, path)
        if descriptor is None:
            errors[path] = "not an editable schema field"
            continue
        ok, value, err = validate_value(path, descriptor, raw)
        if ok:
            coerced[path] = value
        else:
            errors[path] = err
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400

    doc = _load_doc(asset)
    target = next((r for r in _records_of(doc, asset) if _record_id(asset, r) == rid), None)
    if target is None:
        return jsonify({"error": f"{asset} '{rid}' not found"}), 404

    ts = datetime.now().isoformat(timespec="seconds")
    audit = []
    for path, value in coerced.items():
        old = _get_nested(target, path)
        if old == value:
            continue  # no-op change — not audited
        _set_nested(target, path, value)
        audit.append({
            "timestamp": ts, "user": AUDIT_USER,
            "asset": asset, "asset_label": ASSETS[asset]["label"],
            "record_id": rid, "field": path,
            "field_label": path.rsplit(".", 1)[-1],
            "old": old, "new": value,
        })
    _save_doc(asset, doc)
    _append_audit(audit)
    recompute = _maybe_recompute(asset, rid, target, coerced)
    return jsonify({"status": "success", "updated": len(audit),
                    "record": target, "recompute": recompute})


@app.route("/api/audit")
def api_audit():
    """The amendment audit trail (newest first)."""
    return jsonify(list(reversed(_load_audit())))


def _flood_payload(asset: str, rid: str) -> dict:
    """Severe flood events: storm, cluster type, damage %. Property/commercial."""
    if asset not in HC_CONFIG:
        return {"supported": False, "reason": "No flood model for this asset."}
    rec = _hc_record(asset, rid)
    if rec is None:
        return {"supported": True, "count": 0, "events": []}
    idx = _storm_type_index()
    events = []
    for d in rec.get("storm_details", []):
        if not (d.get("flooded") or d.get("exceeded_severe") or d.get("damage_ratio", 0) > 0):
            continue
        t = idx.get(d.get("storm_id"), {})
        events.append({
            "storm": d.get("storm_id"),
            "type": t.get("type") or "—",
            "intensity": t.get("intensity"),
            "damage_pct": round(d.get("damage_ratio", 0) * 100, 2),
            "depth_m": round(d.get("flood_depth_m", 0) or 0, 2),
            "peak_m": round(d.get("gauge_peak_m", 0) or 0, 2),
            "severe": bool(d.get("exceeded_severe")),
        })
    events.sort(key=lambda e: (-e["damage_pct"], 0 if e["severe"] else 1))
    return {"supported": True, "count": len(events),
            "flood_zone": rec.get("flood_zone"), "events": events[:12]}


def _wind_payload(asset: str, rid: str) -> dict:
    """Wind/typhoon events. The thames win files are zero-event placeholders
    (the typhoon ensemble was not run), so there is nothing real to show yet."""
    if asset not in HC_CONFIG:
        return {"supported": False, "reason": "No wind model for this asset."}
    return {"supported": True, "count": 0, "events": [],
            "note": "Typhoon/wind ensemble not run for this catchment — "
                    "zero-event placeholder. Run `port --typhoon` to populate."}


def _fire_payload(asset: str, rid: str) -> dict:
    """Fire model outcome distribution (commercial assets only)."""
    model, amap = _model_assets("fire", FIRE_FILE)
    a = amap.get(rid)
    if not a:
        return {"supported": False,
                "reason": "Fire model (MKM-FIRE-001) covers commercial assets only."}
    return {
        "supported": True, "model": model, "n_sim": a.get("n_sim"),
        "lambda_annual": a.get("lambda_annual"),
        "n_fires": a.get("n_fires"),
        "outcomes": [
            {"label": "Contained", "count": a.get("n_contained", 0), "cls": "ok"},
            {"label": "Partial loss", "count": a.get("n_partial", 0), "cls": "warn"},
            {"label": "Total loss", "count": a.get("n_total", 0), "cls": "bad"},
            {"label": "Point of no return", "count": a.get("n_point_of_no_return", 0), "cls": "bad"},
        ],
        "stats": [
            {"label": "Loss frequency (annual)", "value": a.get("loss_frequency")},
            {"label": "Partial-loss freq", "value": a.get("partial_loss_frequency")},
            {"label": "Total-loss freq", "value": a.get("total_loss_frequency")},
            {"label": "Containment rate", "value": a.get("containment_rate"), "pct": True},
        ],
    }


def _seismic_payload(asset: str, rid: str) -> dict:
    """Seismic model damage-state distribution (commercial assets only)."""
    model, amap = _model_assets("seismic", SEISMIC_FILE)
    a = amap.get(rid)
    if not a:
        return {"supported": False,
                "reason": "Seismic model covers commercial assets only."}
    ds = a.get("damage_state_counts", {}) or {}
    classes = ["ok", "warn", "warn", "bad"]
    return {
        "supported": True, "model": model, "n_sim": a.get("n_sim"),
        "n_events": a.get("n_events"),
        "site": [
            {"label": "Hazard zone", "value": a.get("zone")},
            {"label": "Site class", "value": a.get("site_class")},
            {"label": "Construction", "value": a.get("construction_type")},
            {"label": "BRI rating", "value": a.get("rating")},
        ],
        "damage_states": [
            {"label": SEISMIC_DS_LABELS[i], "count": ds.get(str(i), 0), "cls": classes[i]}
            for i in range(4)
        ],
        "stats": [
            {"label": "No-collapse rate", "value": a.get("no_collapse_rate"), "pct": True},
            {"label": "Loss frequency (annual)", "value": a.get("loss_frequency")},
            {"label": "PML 1-in-475", "value": a.get("pml_475"), "pct": True},
            {"label": "PML 1-in-2475", "value": a.get("pml_2475"), "pct": True},
        ],
    }


@app.route("/api/<asset>/items/<rid>/perils")
def api_perils(asset: str, rid: str):
    """All four perils for one asset, each with a `supported` flag."""
    if asset not in ASSETS:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    return jsonify({
        "flood": _flood_payload(asset, rid),
        "wind": _wind_payload(asset, rid),
        "fire": _fire_payload(asset, rid),
        "seismic": _seismic_payload(asset, rid),
    })


@app.route("/api/<asset>/items/<rid>/waterfall")
def api_waterfall(asset: str, rid: str):
    """PRS spread waterfall for one asset, from its hazard-curve decomposition.

    Mirrors the main app's basis waterfall (Gauge -> SHE elevation -> SHD
    distance -> Property -> BRI resilient), each bar the spread under that
    stage's adjustment plus its effect vs the gauge spread. Property/commercial
    only; other assets return supported=False.
    """
    if asset not in ASSETS:
        return jsonify({"error": f"Unknown asset '{asset}'"}), 404
    if asset not in HC_CONFIG:
        return jsonify({"supported": False,
                        "reason": "No PRS waterfall for this asset class."})
    rec = _hc_record(asset, rid)
    if rec is None:
        return jsonify({"supported": True, "spread_decomposition": None,
                        "note": "No hazard curve for this asset."})
    sd = rec.get("spread_decomposition", {}) or {}
    # Return the raw decomposition; the shared phc_basis_waterfall.js renderer
    # builds the bars (Gauge -> SHE -> SHD -> Property -> BRI) from it, exactly
    # as the main-app basis panel does.
    return jsonify({
        "supported": True,
        "flood_zone": rec.get("flood_zone"),
        "property_spread_bps": sd.get("property_spread_bps") or 0.0,
        "spread_decomposition": sd,
    })


@app.route("/shared/phc_basis_waterfall.js")
def shared_waterfall_js():
    """Serve the main app's spread-waterfall renderer verbatim (shared utility)."""
    return SHARED_WATERFALL_JS.read_text(encoding="utf-8"), 200, \
        {"Content-Type": "application/javascript"}


if __name__ == "__main__":
    print(f"CDM Asset Review — sandbox dir: {SANDBOX_DIR}")
    print(f"Assets: {', '.join(ASSETS)}  (catchment: {CATCHMENT})")
    print("Open http://127.0.0.1:5057")
    app.run(host="127.0.0.1", port=5057, debug=True)
