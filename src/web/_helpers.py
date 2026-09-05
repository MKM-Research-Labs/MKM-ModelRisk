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

from flask import request, send_file

from config.files import HIDDEN_DOC_EXTENSIONS, INLINE_VIEW_EXTENSIONS
from config.governance import (DOC_CATEGORIES, DOC_TAB_CATEGORIES, DOC_TAB_GROUPS, REFERENCE_SPECS,
                               REVIEW_DOC_CATEGORIES, TESTING_DOC_CATEGORIES)
from src.command import CommandContext, context_from_headers
from src.files import extension
from src.governance.ml_application import list_ml_applications
from src.governance.model_inventory import list_models
from src.governance.reference import get_reference_lists


def document_specs() -> dict:
    """How the console should surface documents: which categories each panel offers,
    which extensions stay stored but unlisted, and which may be viewed inline. Served
    with every aggregate's field specs so the two consoles cannot drift apart."""
    return {
        "doc_categories": list(DOC_CATEGORIES),
        "doc_tab_categories": list(DOC_TAB_CATEGORIES),
        # Which of those tabs is a group, and over what. "Testing" is a panel
        # of four categories, not a category anything is filed under.
        "doc_tab_groups": {k: list(v) for k, v in DOC_TAB_GROUPS.items()},
        "testing_doc_categories": list(TESTING_DOC_CATEGORIES),
        "review_doc_categories": list(REVIEW_DOC_CATEGORIES),
        "hidden_doc_extensions": sorted(HIDDEN_DOC_EXTENSIONS),
        "inline_view_extensions": sorted(INLINE_VIEW_EXTENSIONS),
    }


def send_document(path, doc: dict, *, inline: bool = False):
    """Serve an uploaded document, inline (opened in a browser tab) only when the
    caller asked for it AND the extension is one we are willing to render in this
    origin. An uploaded file shown inline executes as this application, so the
    allow-list is the security boundary, not the query parameter."""
    viewable = extension(doc.get("original_name", "")) in INLINE_VIEW_EXTENSIONS
    return send_file(str(path), as_attachment=not (inline and viewable),
                     download_name=doc["original_name"])


def json_body() -> dict[str, Any]:
    """Return the request's JSON body as a dict (empty if none)."""
    return request.get_json(silent=True) or {}


def resolve_mrc_for_record(record_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """The committee responsible for a record, and why it is that one.

    Where ``resolve_mrc_for_org`` answers only "what covers this org location", this
    also applies the routing rules — so an agentic AI System or a mission-critical model
    reports the committee it must actually reach, with the reason travelling alongside.
    """
    from src.governance.mrc import route  # lazy: avoids an import cycle
    return route(record_type, data or {}, get_reference_lists())


def resolve_mrc_for_org(division: str | None, line_of_business: str | None) -> dict[str, Any]:
    """The MRC committee responsible for a given org location, as a JSON block.

    Returns ``{"mrc": <committee or None>, "level": <match level or None>}`` —
    the shared shape used by the model and product overviews and by the sign-off
    router to decide where a request goes.
    """
    from src.governance.mrc import matching_mrc  # lazy: avoids an import cycle
    mrc, level = matching_mrc(division, line_of_business, get_reference_lists())
    return {"mrc": mrc, "level": level}


def reference_options() -> dict[str, list]:
    """Current option values per reference list, using each list's display field.

    Also exposes the model inventory under the synthetic key ``model_inventory``
    so collection fields (e.g. an MRC decision's linked model) can render as a
    dropdown of registered model ids.
    """
    lists = get_reference_lists()
    # A list with a ``value_key`` is a status vocabulary: the record stores one word
    # and the screen shows another. The options stay the STORED values — that is what
    # a dropdown must submit and what the code matches on — and the labels travel
    # beside them, so a rename changes what is shown without moving anything stored.
    options = {
        name: [item[_option_key(name)] for item in items if item.get(_option_key(name))]
        for name, items in lists.items()
    }
    options["model_inventory"] = [m["model_id"] for m in list_models()]
    # A Product component is a model OR an ML Application, so its picker offers both.
    # Kept separate from ``model_inventory`` so the other consumers of that list (an
    # MRC decision's linked model, say) are not quietly offered ML Applications too.
    options["product_component"] = (options["model_inventory"] +
                                    [r["ml_application_id"] for r in list_ml_applications()])
    return options


def _option_key(name: str) -> str:
    """Which field of a reference item a record stores. A status vocabulary names it
    explicitly; every other list stores the same thing it displays."""
    spec = REFERENCE_SPECS.get(name, {})
    return spec.get("value_key") or spec.get("display", "value")


def reference_option_labels() -> dict[str, dict]:
    """``{list: {stored value: shown label}}`` for the status vocabularies.

    Only lists that separate the two appear here, so a field with no entry is
    displayed exactly as it is stored — which is every other dropdown in the app.
    """
    labels = {}
    for name, items in get_reference_lists().items():
        spec = REFERENCE_SPECS.get(name, {})
        if not spec.get("value_key"):
            continue
        shown = spec.get("display", "value")
        labels[name] = {item[spec["value_key"]]: item.get(shown) or item[spec["value_key"]]
                        for item in items if item.get(spec["value_key"])}
    return labels


def resolve_field(field: dict, options_by_list: dict | None = None,
                  labels_by_list: dict | None = None) -> dict:
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
        # A reference decides where the options come from, not how many may be
        # picked: a multi-valued field (an action's owners) keeps its own type and
        # only borrows the list.
        field_type = "multichoice" if field_type == "multichoice" else "choice"
        options = options_by_list[reference]
    resolved = {
        "key": field["key"], "label": field["label"], "type": field_type,
        "options": options, "required": bool(field.get("required")),
    }
    # What each stored value is shown as, where the two differ. Absent for every
    # ordinary list, so those render exactly as before.
    if reference:
        shown = (labels_by_list or reference_option_labels()).get(reference)
        if shown:
            resolved["option_labels"] = dict(shown)
    # Set once and never after: the console shows it but must not offer it for
    # editing, and must not send it back — the domain would refuse the whole edit.
    if field.get("immutable"):
        resolved["immutable"] = True
    # Carry the hidden flag through so the UI can skip internal fields (e.g. the
    # agenda escalation back-pointers) in tables and add forms.
    if field.get("hidden"):
        resolved["hidden"] = True
    # Layout the config decides rather than the console: a field that shares the
    # previous column and sits beneath it, and a date that starts at today. Both are
    # opt-in per field — a due date must not default to today — and both are dropped
    # unless carried here, because this rebuilds the field rather than copying it.
    if field.get("stacked"):
        resolved["stacked"] = True
    if field.get("default_today"):
        resolved["default_today"] = True
    # What each option MEANS, where the config defines it (a person's roles). An
    # administrator granting a role should be able to see what they are granting, so the
    # explanation travels with the option rather than living only in the config file.
    if field.get("explanations"):
        resolved["explanations"] = field["explanations"]
    # Shown, but not offered as an input: the value is recorded by the process that grants
    # it (a person's ratified roles) rather than typed on this screen.
    if field.get("readonly"):
        resolved["readonly"] = True
    # What the add form starts on where a blank is not the sensible opening value
    # (an agreed action is Open). Config decides it, not the screen (coding rule R1).
    if field.get("default"):
        resolved["default"] = field["default"]
    return resolved


def request_actor() -> str:
    """The SSO actor for a non-JSON (e.g. multipart upload) request.

    These paths — document uploads, logo and ToR replacement, item deletion — call their
    command directly rather than through ``dispatch``, so they would sidestep the
    known-actor rule that ``authorize`` applies. The check belongs wherever a change is
    about to be authored, so it is applied here too.
    """
    from src.identity import assert_recognised, resolve_principal
    actor = resolve_principal(request.headers).actor
    assert_recognised(actor)
    return actor


def context_from_request(body: dict[str, Any]) -> CommandContext:
    """Build the command context from SSO headers and the confirm flag."""
    return context_from_headers(
        request.headers,
        confirmed=bool(body.get("confirmed")),
        reason=body.get("reason"),
    )


def grouped_field_specs(field_specs: dict, options_by_list: dict[str, list]) -> list[dict]:
    """Field specs grouped for a detail view; references resolve to dropdowns.

    One implementation for every aggregate that draws a grouped detail view -- the
    model inventory, Products, Clients and ML Applications. There were four, and only
    the inventory's carried ``option_labels``, so a status vocabulary renamed in Admin
    displayed correctly on a model and by its stored value everywhere else.

    ``option_labels`` is carried only where a list separates the word a record stores
    from the word a screen shows, so every other field's payload is unchanged.
    """
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for key, spec in field_specs.items():
        group = by_name.get(spec["group"])
        if group is None:
            group = {"group": spec["group"], "fields": []}
            by_name[spec["group"]] = group
            groups.append(group)
        resolved = resolve_field({**spec, "key": key}, options_by_list)
        field = {"key": resolved["key"], "label": resolved["label"],
                 "type": resolved["type"], "options": resolved["options"]}
        if resolved.get("option_labels"):
            field["option_labels"] = resolved["option_labels"]
        group["fields"].append(field)
    return groups


def collection_field_specs(specs: dict) -> list[dict]:
    """Collection metadata (label, id prefix, item fields) for the UI."""
    options_by_list = reference_options()
    return [
        {"key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
         "fields": [resolve_field(f, options_by_list) for f in spec["fields"]]}
        for key, spec in specs.items()
    ]
