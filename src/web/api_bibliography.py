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
"""HTTP API for the bibliography (references + BibTeX export)."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify

from config.governance import BIBLIOGRAPHY_SPEC
from src.command import dispatch
from src.governance.bibliography import (
    add_reference,
    get_references,
    remove_reference,
    to_bibtex,
    update_reference,
)
from src.web._helpers import context_from_request, json_body

bib_bp = Blueprint("bibliography", __name__, url_prefix="/api/bibliography")


def _spec():
    return {
        "label": BIBLIOGRAPHY_SPEC["label"],
        "fields": [
            {"key": f["key"], "label": f["label"], "type": f["type"],
             "options": list(f.get("options", [])), "required": bool(f.get("required"))}
            for f in BIBLIOGRAPHY_SPEC["fields"]
        ],
    }


@bib_bp.get("")
def list_all():
    return jsonify({"references": get_references(), "spec": _spec()})


@bib_bp.post("/references")
def add():
    body = json_body()
    dispatch("add_reference", add_reference, context=context_from_request(body),
             fields=body.get("fields") or {})
    return jsonify(get_references()), 201


@bib_bp.post("/references/<item_id>")
def update(item_id: str):
    body = json_body()
    dispatch("update_reference", update_reference, context=context_from_request(body),
             item_id=item_id, fields=body.get("fields") or {})
    return jsonify(get_references())


@bib_bp.post("/references/<item_id>/delete")
def remove(item_id: str):
    body = json_body()
    dispatch("remove_reference", remove_reference, context=context_from_request(body), item_id=item_id)
    return jsonify(get_references())


@bib_bp.get("/export.bib")
def export():
    return Response(to_bibtex(get_references()), mimetype="application/x-bibtex", headers={
        "Content-Disposition": 'attachment; filename="references.bib"',
    })
