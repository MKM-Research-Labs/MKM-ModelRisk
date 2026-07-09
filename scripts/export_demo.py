# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Regenerate ``scripts/demo_data.json`` from the live demo database.

Run against the demo DB so the seed file matches what's on screen::

    MKM_DB_NAME=mkm_modelrisk_demo python scripts/export_demo.py

Every item is filtered to the *current* specs — dropping generated ids, stale
fields left over from schema changes, and file-upload metadata (uploaded files
live outside git) — so the result re-seeds cleanly on a fresh clone.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from config.governance import (
    BIBLIOGRAPHY_SPEC,
    COLLECTION_SPECS,
    MEETING_FIELD_SPECS,
    MODEL_FIELD_SPECS,
    MRC_COLLECTION_SPECS,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_FIELD_SPECS,
    REFERENCE_SPECS,
)
from src.governance.bibliography import get_references
from src.governance.model_inventory import list_models
from src.governance.mrc import list_meetings
from src.governance.mrc_settings import get_settings
from src.governance.product import list_products
from src.governance.reference import get_reference_lists

_OUT = Path(__file__).resolve().parent / "demo_data.json"
_ASSETS = Path(__file__).resolve().parent / "demo_assets"
_UPLOADS_MRC = Path(__file__).resolve().parents[1] / "uploads" / "mrc"


def _capture_committee_tors(mrc_items: list[dict]) -> dict:
    """Copy each committee's ToR out of gitignored uploads/ into demo_assets/
    (committed) and return a {committee value -> {file, original_name}} map so
    the seed can re-upload them on a fresh clone."""
    tors = {}
    for c in mrc_items:
        filename = c.get("tor_filename")
        src = _UPLOADS_MRC / filename if filename else None
        if src and src.exists():
            _ASSETS.mkdir(exist_ok=True)
            shutil.copy(src, _ASSETS / filename)
            tors[c["value"]] = {"file": filename, "original_name": c.get("tor_original_name") or filename}
    return tors


def _keep(key: str) -> bool:
    return key != "item_id" and not (key.endswith("_filename") or key.endswith("_original_name"))


def _clean(item: dict, allowed: set[str]) -> dict:
    return {k: v for k, v in item.items() if _keep(k) and k in allowed}


def _collections(data: dict, specs: dict, exclude: set[str] = frozenset()) -> dict:
    out = {}
    for name, spec in specs.items():
        if name in exclude:
            continue
        items = data.get(name) or []
        if items:
            allowed = {f["key"] for f in spec["fields"]}
            out[name] = [_clean(it, allowed) for it in items]
    return out


def _scalars(data: dict, spec: dict, skip: set[str]) -> dict:
    keys = set(spec)
    return {k: v for k, v in data.items() if k in keys and k not in skip and _keep(k)}


def export() -> None:
    refs = get_reference_lists()
    reference = {
        name: [_clean(it, {f["key"] for f in spec["fields"]}) for it in refs.get(name, [])]
        for name, spec in REFERENCE_SPECS.items()
    }

    models = []
    for m in list_models():
        d = m["data"]
        vq = d.get("validation_questions") or []
        models.append({
            "model_id": m["model_id"], "name": d.get("name"),
            "fields": _scalars(d, MODEL_FIELD_SPECS, {"name"}),
            "collections": _collections(d, COLLECTION_SPECS, {"validation_questions"}),
            "validation": {q["item_id"]: q.get("status") for q in vq if q.get("status")},
        })

    products = [{
        "product_id": p["product_id"], "product": p["data"].get("product"),
        "fields": _scalars(p["data"], PRODUCT_FIELD_SPECS, {"product"}),
        "collections": _collections(p["data"], PRODUCT_COLLECTION_SPECS),
    } for p in list_products()]

    meetings = [{
        "meeting_id": mt["meeting_id"], "title": mt["data"].get("title"),
        "fields": _scalars(mt["data"], MEETING_FIELD_SPECS, {"title"}),
        "collections": _collections(mt["data"], MRC_COLLECTION_SPECS),
    } for mt in list_meetings()]

    bib_allowed = {f["key"] for f in BIBLIOGRAPHY_SPEC["fields"]}
    out = {
        "settings": dict(get_settings().get("fields", {})),
        "reference": reference,
        "committee_tors": _capture_committee_tors(refs.get("mrc", [])),
        "models": models,
        "products": products,
        "meetings": meetings,
        "bibliography": [_clean(b, bib_allowed) for b in get_references()],
    }
    _OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {_OUT}  ({len(models)} models, {len(products)} products, {len(meetings)} meetings)")


if __name__ == "__main__":
    export()
