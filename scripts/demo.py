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
"""Demo bootstrap: a separate, seeded ``mkm_modelrisk_demo`` database.

``python app.py demo`` points the app at this database, creating, migrating and
seeding it (once) before serving — so a client demo is one command and never
touches the dev data.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import psycopg

from config import DatabaseConfig
from src.database import run_migrations
from src.files import save_upload
from src.governance.bibliography import add_reference
from src.governance.documents import add_document
from src.governance.model_inventory import add_collection_item as _model_add
from src.governance.model_inventory import (
    list_models,
    rebuild_inventory_view,
    register_model,
    update_collection_item as _model_update,
)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.mrc import add_collection_item as _meeting_add
from src.governance.mrc import rebuild_meeting_view, schedule_meeting
from src.governance.mrc.pack import compile_tex
from src.governance.mrc_settings import set_field, set_logo
from src.governance.product import add_collection_item as _product_add
from src.governance.product import list_products, rebuild_product_view, register_product
from src.governance.product.commands import AGGREGATE_TYPE as PRODUCT_AGGREGATE
from src.governance.reference import add_option

DEMO_DB = "mkm_modelrisk_demo"
_DATA = Path(__file__).resolve().parent / "demo_data.json"
_LOGO = Path(__file__).resolve().parents[1] / "docs" / "shared" / "moodys.jpeg"
_ACTOR = "demo@modelrisk"


def _ensure_demo_database() -> None:
    cfg = DatabaseConfig.from_env()
    admin = psycopg.connect(
        host=cfg.host, port=cfg.port, dbname="mkm_modelrisk",
        user=cfg.owner_user, password=cfg.owner_password, autocommit=True)
    try:
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DEMO_DB,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{DEMO_DB}" OWNER {cfg.owner_user}')
    finally:
        admin.close()


def _seed_logo() -> None:
    if not _LOGO.exists():
        return
    meta = save_upload("mrc", _LOGO.name, _LOGO.read_bytes())
    set_logo(filename=meta["filename"], original_name=_LOGO.name, actor=_ACTOR)


def _demo_pdf() -> bytes | None:
    """A one-page placeholder document: the company logo over 'This is a demo'."""
    assets, logo_tex = {}, ""
    if _LOGO.exists():
        assets["logo.png"] = _LOGO.read_bytes()
        logo_tex = "\\includegraphics[height=3.5cm]{logo.png}\\\\[16pt]\n"
    tex = (
        "\\documentclass[12pt]{article}\n"
        "\\usepackage[a4paper,margin=20mm]{geometry}\n"
        "\\usepackage{graphicx}\\pagestyle{empty}\n"
        "\\begin{document}\n\\vspace*{3cm}\\begin{center}\n"
        + logo_tex + "{\\Large\\textbf{This is a demo}}\n"
        "\\end{center}\n\\end{document}\n"
    )
    try:
        return compile_tex(tex, assets)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None  # tectonic unavailable — skip the placeholder documents


def _seed_documents() -> None:
    """Attach the placeholder demo PDF to every model and Product."""
    pdf = _demo_pdf()
    if pdf is None:
        return
    targets = [(MODEL_AGGREGATE, m["model_id"], "model") for m in list_models()]
    targets += [(PRODUCT_AGGREGATE, p["product_id"], "product") for p in list_products()]
    for aggregate_type, aggregate_id, prefix in targets:
        add_document(
            aggregate_type=aggregate_type, aggregate_id=aggregate_id,
            scope=f"{prefix}/{aggregate_id}", category="Core Documentation",
            filename="demo.pdf", data=pdf, description="Demo placeholder", actor=_ACTOR)


def seed() -> None:
    """Populate the demo database from ``demo_data.json``."""
    data = json.loads(_DATA.read_text())
    _seed_logo()
    for field, value in data["settings"].items():
        set_field(field=field, value=value, actor=_ACTOR)
    for list_name, items in data["reference"].items():
        for item in items:
            add_option(list_name=list_name, fields=item, actor=_ACTOR)
    for model in data["models"]:
        register_model(model_id=model["model_id"], name=model["name"],
                       fields=model.get("fields", {}), actor=_ACTOR)
        for collection, items in model.get("collections", {}).items():
            for item in items:
                _model_add(model_id=model["model_id"], collection=collection, fields=item, actor=_ACTOR)
        for item_id, status in model.get("validation", {}).items():
            _model_update(model_id=model["model_id"], collection="validation_questions",
                          item_id=item_id, fields={"status": status}, actor=_ACTOR)
    rebuild_inventory_view()
    for product in data["products"]:
        register_product(product_id=product["product_id"], product=product["product"], fields=product["fields"], actor=_ACTOR)
        rebuild_product_view()
        for collection, items in product.get("collections", {}).items():
            for item in items:
                _product_add(product_id=product["product_id"], collection=collection, fields=item, actor=_ACTOR)
    for meeting in data["meetings"]:
        schedule_meeting(meeting_id=meeting["meeting_id"], title=meeting["title"],
                         date=meeting["fields"]["date"], fields=meeting.get("fields", {}), actor=_ACTOR)
        for collection, items in meeting.get("collections", {}).items():
            for item in items:
                _meeting_add(meeting_id=meeting["meeting_id"], collection=collection, fields=item, actor=_ACTOR)
    for reference in data["bibliography"]:
        add_reference(fields=reference, actor=_ACTOR)
    _seed_documents()
    rebuild_inventory_view()
    rebuild_product_view()
    rebuild_meeting_view()


def bootstrap_demo() -> None:
    """Ensure the demo database exists, is migrated, and is seeded (once)."""
    _ensure_demo_database()
    run_migrations()
    if not list_models():
        seed()
