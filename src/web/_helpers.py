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
"""Request helpers shared by the API blueprints."""
from __future__ import annotations

from typing import Any

from flask import request

from config.governance import REFERENCE_SPECS
from src.command import CommandContext, context_from_headers
from src.governance.model_inventory import list_models
from src.governance.reference import get_reference_lists


def json_body() -> dict[str, Any]:
    """Return the request's JSON body as a dict (empty if none)."""
    return request.get_json(silent=True) or {}


def resolve_mrc_for_org(division: str | None, department: str | None) -> dict[str, Any]:
    """The MRC committee responsible for a given org location, as a JSON block.

    Returns ``{"mrc": <committee or None>, "level": <match level or None>}`` —
    the shared shape used by the model and product overviews and by the sign-off
    router to decide where a request goes.
    """
    from src.governance.mrc import matching_mrc  # lazy: avoids an import cycle
    mrc, level = matching_mrc(division, department, get_reference_lists())
    return {"mrc": mrc, "level": level}


def reference_options() -> dict[str, list]:
    """Current option values per reference list, using each list's display field.

    Also exposes the model inventory under the synthetic key ``model_inventory``
    so collection fields (e.g. an MRC decision's linked model) can render as a
    dropdown of registered model ids.
    """
    lists = get_reference_lists()
    options = {
        name: [item[REFERENCE_SPECS[name].get("display", "value")] for item in items]
        for name, items in lists.items()
    }
    options["model_inventory"] = [m["model_id"] for m in list_models()]
    return options


def resolve_field(field: dict, options_by_list: dict | None = None) -> dict:
    """Promote a field's reference to a choice dropdown when the referenced list
    has values; otherwise keep its native type and any static options.

    Shared by every API that renders field specs to the front end, so a single
    rule decides whether a field becomes a dropdown.
    """
    options_by_list = options_by_list if options_by_list is not None else reference_options()
    field_type = field["type"]
    options = list(field.get("options", []))
    reference = field.get("reference")
    if reference and options_by_list.get(reference):
        field_type = "choice"
        options = options_by_list[reference]
    resolved = {
        "key": field["key"], "label": field["label"], "type": field_type,
        "options": options, "required": bool(field.get("required")),
    }
    # Carry the hidden flag through so the UI can skip internal fields (e.g. the
    # agenda escalation back-pointers) in tables and add forms.
    if field.get("hidden"):
        resolved["hidden"] = True
    return resolved


def request_actor() -> str:
    """The SSO actor for a non-JSON (e.g. multipart upload) request."""
    from src.identity import resolve_principal
    return resolve_principal(request.headers).actor


def context_from_request(body: dict[str, Any]) -> CommandContext:
    """Build the command context from SSO headers and the confirm flag."""
    return context_from_headers(
        request.headers,
        confirmed=bool(body.get("confirmed")),
        reason=body.get("reason"),
    )
