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
"""Pure decision logic for the field-lineage registry aggregate.

Payload shape is already schema-validated at the ingest boundary, so the rule here
just assembles the event to append (with derived counts). No I/O.
"""
from __future__ import annotations

from typing import Any

from src.governance.errors import DomainError
from src.governance.field_lineage._state import EVENT_INGESTED, RegistryState


def field_count(registry: dict[str, Any]) -> int:
    """Total fields catalogued across every report and section."""
    return sum(len(section.get("fields", {}) or {})
               for report in (registry.get("reports") or {}).values()
               for section in (report.get("sections") or {}).values())


def decide_ingest(
    state: RegistryState, *, registry: dict[str, Any],
    provenance: dict[str, Any], content_hash: str,
) -> tuple[str, dict[str, Any]]:
    """Assemble a ``FieldLineageIngested`` event for the pushed registry."""
    if not isinstance(registry, dict):
        raise DomainError("registry must be an object")
    payload = {
        "registry": registry,
        "provenance": provenance,
        "content_hash": content_hash,
        "report_count": len(registry.get("reports") or {}),
        "field_count": field_count(registry),
    }
    return EVENT_INGESTED, payload
