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
