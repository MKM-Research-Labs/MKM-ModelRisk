# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""MRC blueprint object and shared spec helpers (used by every submodule)."""
from __future__ import annotations

from flask import Blueprint, jsonify

from config.governance import MEETING_FIELD_SPECS, MRC_COLLECTION_SPECS
from src.web._helpers import reference_options, resolve_field

mrc_bp = Blueprint("mrc", __name__, url_prefix="/api/meetings")


def field_spec_list() -> list[dict]:
    """Meeting scalar fields resolved for the UI (references → dropdowns)."""
    options_by_list = reference_options()
    return [resolve_field({**spec, "key": key}, options_by_list)
            for key, spec in MEETING_FIELD_SPECS.items()]


def collection_spec_list() -> list[dict]:
    """Meeting collection specs resolved for the UI (references → dropdowns)."""
    options_by_list = reference_options()
    return [
        {
            "key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
            "fields": [resolve_field(f, options_by_list) for f in spec["fields"]],
        }
        for key, spec in MRC_COLLECTION_SPECS.items()
    ]


@mrc_bp.get("/fields")
def field_specs():
    """The meeting scalar + collection field specs (populates the console)."""
    return jsonify({"fields": field_spec_list(), "collections": collection_spec_list()})
