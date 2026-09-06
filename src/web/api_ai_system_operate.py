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
"""What an AI System's owner records while it is running.

Three things the domain has been able to do since Phases 3–5 and nothing could ask
it to: measure a variability envelope, set the bar a trigger fires on, and seal the
record of a release. The commands existed, were tested, and were reachable by
nothing — no route, no ingest, no button. A governance capability the estate cannot
reach is not a governance capability, and an envelope panel that can only ever read
"not measured" invites the belief that the system is well behaved.

Attaches to ``ai_system_bp``; imported for its side effects in app.py, the same way
the sign-off and document routes are.
"""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch
from src.governance.ai_system import (current_config_version, get_ai_system,
                                      latest_envelope, rebuild_ai_system_view,
                                      rebuild_variability_envelope_view,
                                      record_variability_envelope,
                                      seal_release_manifest, set_trigger_threshold)
from src.governance.ai_system.envelope import envelope_status
from src.web._helpers import context_from_request, json_body
from src.web.api_ai_system import ai_system_bp

_NOT_FOUND = ({"error": "AI System not found"}, 404)


def _require(ai_system_id: str):
    return get_ai_system(ai_system_id) is not None


@ai_system_bp.post("/<ai_system_id>/envelope")
def record_envelope(ai_system_id: str):
    """Record what N runs of the same input actually produced.

    The scores go in raw and the envelope is computed from them, rather than the
    caller posting a range it worked out itself: the refusal below the minimum run
    count is the point of the whole measurement, and a caller that hands over a
    finished range has already decided the question it was supposed to be asked.
    """
    if not _require(ai_system_id):
        return jsonify(_NOT_FOUND[0]), _NOT_FOUND[1]
    body = json_body()
    dispatch("record_variability_envelope", record_variability_envelope,
             context=context_from_request(body), ai_system_id=ai_system_id,
             scores=body.get("scores") or [], note=body.get("note", ""))
    rebuild_variability_envelope_view()
    envelope = latest_envelope(ai_system_id)
    return jsonify({"envelope": envelope_status(
        envelope, current_config_version(ai_system_id)) if envelope else None}), 201


@ai_system_bp.post("/<ai_system_id>/thresholds")
def set_threshold(ai_system_id: str):
    """Set the bar one property is judged against, and what happens when it breaks.

    ``fallback`` is required by the domain rather than optional: a threshold with no
    stated consequence is a number on a screen. The refusal for a property that is
    not a trigger property is the domain's — "tone" is a dimension the ACE scores,
    not something a trigger fires on, and a threshold set against it would look
    configured and never fire.
    """
    if not _require(ai_system_id):
        return jsonify(_NOT_FOUND[0]), _NOT_FOUND[1]
    body = json_body()
    dispatch("set_trigger_threshold", set_trigger_threshold,
             context=context_from_request(body), ai_system_id=ai_system_id,
             property_name=body.get("property_name", ""),
             threshold=body.get("threshold"), fallback=body.get("fallback", ""),
             rationale=body.get("rationale", ""))
    rebuild_ai_system_view()
    return jsonify({"data": (get_ai_system(ai_system_id) or {}).get("data", {})}), 201


@ai_system_bp.post("/<ai_system_id>/release-manifest")
def seal_manifest(ai_system_id: str):
    """Seal what a release contained. Sealed, not saved — it is never edited again.

    The change class is the engine's, not a word typed here, so what a release was
    classified as reads the same in the manifest as it does in the change history.
    """
    if not _require(ai_system_id):
        return jsonify(_NOT_FOUND[0]), _NOT_FOUND[1]
    body = json_body()
    dispatch("seal_release_manifest", seal_release_manifest,
             context=context_from_request(body), ai_system_id=ai_system_id,
             release=body.get("release", ""),
             change_class=body.get("change_class", ""), note=body.get("note", ""))
    rebuild_ai_system_view()
    return jsonify({"data": (get_ai_system(ai_system_id) or {}).get("data", {})}), 201
