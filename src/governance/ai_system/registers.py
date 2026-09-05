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
"""The failure-mode register, flattened across the estate.

A failure mode is recorded against the system it belongs to, and is read two ways: down
one system's list, and across the estate — "which systems can be reached through a
compromised MCP server" is the question the register exists to answer and a per-record
list cannot.

**Nothing here resolves whether a mitigation is in place.** That is answered from the
documents tagged against each record by the FINOS coverage view, and answering it a
second way here is how two registers come to disagree.
"""
from __future__ import annotations

from typing import Any

from config.governance._ai_failure_modes import FAILURE_MODE_COLLECTION
from config.governance._standing_risks import STANDING_RISKS
from src.database import read_all, read_view, replace_view
from src.governance.ai_system._state import apply, initial_state, record_data
from src.governance.ai_system.commands import AGGREGATE_TYPE

_VIEW = "failure_mode_register_view"
_COLUMNS = ("entry_id", "ai_system_id", "finos_risk", "data")
_STANDING_VIEW = "standing_risk_register_view"
_STANDING_COLUMNS = ("risk_id", "data")


def rebuild_failure_mode_register_view(config=None) -> int:
    """Rebuild the register from the event log; return the entry count.

    Folded through the aggregate's own ``apply`` rather than by reading collection
    events directly: an entry that was added and then removed must not appear, and the
    fold is the only thing that knows that.
    """
    states: dict[str, Any] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state = states.get(event.aggregate_id, initial_state())
        states[event.aggregate_id] = apply(state, event.event_type, event.payload)

    rows = []
    for ai_system_id, state in states.items():
        for entry in record_data(state).get(FAILURE_MODE_COLLECTION) or []:
            rows.append((f"{ai_system_id}#{entry.get('item_id')}", ai_system_id,
                         str(entry.get("finos_risk") or ""), entry))
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def failure_modes_for_risk(finos_risk: str, config=None) -> list[dict[str, Any]]:
    """Every system that can fail this way, across the estate."""
    return read_view(_VIEW, _COLUMNS, where="finos_risk", value=finos_risk,
                     config=config)


def all_failure_modes(config=None) -> list[dict[str, Any]]:
    return read_view(_VIEW, _COLUMNS, order_by="entry_id", config=config)


__all__ = ["all_failure_modes", "failure_modes_for_risk",
           "rebuild_failure_mode_register_view",
           "rebuild_standing_risk_register_view", "standing_risks"]


def rebuild_standing_risk_register_view(config=None) -> int:
    """Lay the standing register down from config; return the entry count.

    Not projected from events, because it is not the estate's — it is the firm's list
    of what it carries whatever it has registered. Rebuilt from config so the view and
    the config cannot drift, and written identically in every deployment: an entry
    muted in one instance would be a risk somebody had been told does not apply to
    them.
    """
    rows = [(ref, {"finos_risk": ref, "title": title, "why_standing": why})
            for ref, title, why in STANDING_RISKS]
    return replace_view(_STANDING_VIEW, _STANDING_COLUMNS, rows, config=config)


def standing_risks(config=None) -> list[dict[str, Any]]:
    """The register, in the order config states it."""
    rows = read_view(_STANDING_VIEW, _STANDING_COLUMNS, config=config)
    order = {ref: i for i, (ref, _, _) in enumerate(STANDING_RISKS)}
    return sorted(rows, key=lambda r: order.get(r["risk_id"], len(order)))
