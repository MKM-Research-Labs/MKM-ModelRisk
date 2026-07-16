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
"""Commands to update the MRC settings + branding."""
from __future__ import annotations

from typing import Any

from config.governance import MRC_SETTINGS_SPECS
from src.database import Event, append_event
from src.governance.errors import DomainError
from src.governance.mrc_settings._store import (
    AGGREGATE_ID,
    AGGREGATE_TYPE,
    EVENT_LOGO_SET,
    EVENT_SETTING_UPDATED,
    EVENT_TOR_SET,
    load,
)

_SPEC_BY_KEY = {spec["key"]: spec for spec in MRC_SETTINGS_SPECS}


def _record(event_type, payload, actor, reason, config) -> Event:
    _, _, _, version = load(config)
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version, config=config,
    )


def set_field(
    *, field: str, value: Any, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Update one MRC setting (org name, chair, frequency, …)."""
    spec = _SPEC_BY_KEY.get(field)
    if spec is None:
        raise DomainError(f"unknown setting: {field}")
    if spec["type"] == "choice" and value not in spec["options"]:
        raise DomainError(f"{spec['label']} must be one of: {', '.join(spec['options'])}")
    return _record(EVENT_SETTING_UPDATED, {"field": field, "value": value}, actor, reason, config)


def set_logo(
    *, filename: str, original_name: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Record that the branding logo has been set to an uploaded file."""
    payload = {"filename": filename, "original_name": original_name}
    return _record(EVENT_LOGO_SET, payload, actor, reason, config)


def set_tor(
    *, filename: str, original_name: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Record that the MRC Terms of Reference document has been uploaded."""
    payload = {"filename": filename, "original_name": original_name}
    return _record(EVENT_TOR_SET, payload, actor, reason, config)
