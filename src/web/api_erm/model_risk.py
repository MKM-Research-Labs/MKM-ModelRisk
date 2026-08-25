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
"""The ERM's model-risk endpoints: the frozen v1 contract.

Three reads, and one rule that shapes all of them: **the ERM and the console differ
in what they emit, never in what they know.** Both serialise
``src.governance.attention``; the console adds the ids its deep links need, and this
adds the stable field names an integration is written against. That is the only
thing guaranteeing an executive's screen and the ERM's model-risk tile can never
disagree.

Two conventions an integrator should be able to rely on without reading the code:

*Fixed machine values beside adopter labels.* Every enumerated field ships both —
``state``/``label``, ``reason``/``reason_label``. The vocabulary is configurable by
design (an institution renames its risk language); the contract cannot be, or the
first rename breaks every consumer.

*Items come back individually.* The console collapses twenty overdue remediation
steps into three rows, one per owner. That is a presentation decision and it stays
in the console: each item carries a ``group`` key so an ERM can reproduce the same
rollup, or list every record instead. Rolling up inside the contract would leave a
consumer no way back to the records.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import jsonify, request

from config.erm import (
    ERM_ATTENTION_CAP,
    ERM_CONSOLE_BASE,
    ERM_CONSOLE_TAB,
    ERM_SCHEMA_VERSION,
)
from src.governance.attention import dashboard
from src.governance.mrc_settings import get_settings
from src.web.api_erm._bp import erm_bp


def _generated_at() -> str:
    """When this response was produced, in UTC. Carried on every payload beside
    ``as_of``: an ERM panel showing a stale figure without saying so is worse than
    showing none."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _institution() -> str:
    """The institution's own name for itself, so a payload arriving in an ERM says
    whose estate it describes."""
    return ((get_settings() or {}).get("fields") or {}).get("org_name") or ""


def _envelope(as_of: str) -> dict:
    """The four fields every response in this contract carries."""
    return {"schema_version": ERM_SCHEMA_VERSION, "as_of": as_of,
            "generated_at": _generated_at(), "institution": _institution()}


def _console_base() -> str:
    """Where a click-through from the ERM lands. The configured base if an operator
    set one (their ERM may reach the console on a different hostname than it reaches
    this API on), else the host this request arrived at."""
    return (ERM_CONSOLE_BASE or request.host_url).rstrip("/")


def _href(entity: dict) -> str | None:
    """A link a person can follow from the ERM to the record itself.

    ``None`` where nothing in the console shows that thing, rather than a plausible
    URL that 404s: a dead link in somebody else's dashboard is worse than no link,
    because it is discovered by a person who cannot fix it.
    """
    tab = ERM_CONSOLE_TAB.get(entity.get("kind"))
    if not tab:
        return None
    target = entity.get("parent_id") or entity.get("id")
    return f"{_console_base()}/#{tab}" + (f"/{target}" if target else "")


def _item(item: dict) -> dict:
    """One attention item, in the frozen shape. Field names here are the contract:
    a test asserts them so a rename fails loudly rather than in somebody's ERM."""
    entity = item.get("entity") or {}
    return {
        "id": item["id"],
        "state": item["state"],
        "reason": item["reason"],
        "reason_label": item["reason_label"],
        "group": item.get("group"),
        "entity": {
            "kind": entity.get("kind"), "id": entity.get("id"),
            "name": entity.get("name"), "tier": entity.get("tier"),
            "rating": entity.get("rating"), "division": entity.get("division"),
        },
        "owner": item.get("owner") or "",
        "committee": item.get("committee") or "",
        "due": item.get("due"),
        "days_over": item.get("days_over"),
        "action": item.get("action") or "",
        "href": _href(entity),
    }


def _as_of() -> str | None:
    return (request.args.get("as_of") or "").strip() or None


@erm_bp.get("/model-risk")
def model_risk():
    """The panel: the verdict for a C-suite tile, plus the two feeds.

    ``operational`` is what an operational-risk view consumes; ``direction`` is what
    a strategic view consumes. They are separate blocks because they are read by
    different functions, and an undifferentiated dump of counts would leave both
    guessing which numbers were theirs.
    """
    data = dashboard(_as_of())
    verdict = data["verdict"]
    return jsonify({
        **_envelope(data["as_of"]),
        "verdict": {
            "response_required": verdict["response_required"],
            "state": verdict["state"],
            "headline": verdict["headline"],
            "detail": verdict["detail"],
            "counts": verdict["counts"],
            "breakdown": verdict["breakdown"],
        },
        "operational": data["operational"],
        "direction": data["direction"],
        "estate": data["estate"],
        "attention": {
            "total": len(data["items"]),
            "href": f"{_console_base()}/api/erm/{ERM_SCHEMA_VERSION}"
                    "/model-risk/attention",
        },
    })


@erm_bp.get("/model-risk/attention")
def attention():
    """The queue: every outstanding obligation, individually, worst state first."""
    data = dashboard(_as_of())
    items = data["items"]
    return jsonify({
        **_envelope(data["as_of"]),
        "total": len(items),
        "returned": min(len(items), ERM_ATTENTION_CAP),
        "truncated": len(items) > ERM_ATTENTION_CAP,
        "items": [_item(i) for i in items[:ERM_ATTENTION_CAP]],
    })


@erm_bp.get("/model-risk/estate")
def estate():
    """The position: what the estate is made of, for an ERM rolling model risk into
    its own divisional view."""
    data = dashboard(_as_of())
    return jsonify({**_envelope(data["as_of"]), "estate": data["estate"],
                    "direction": data["direction"]})
