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
"""MRC settings store: a global, event-sourced singleton (chair, branding…)."""
from __future__ import annotations

from config.governance import MRC_SETTINGS_DEFAULTS
from src.database import read_stream

AGGREGATE_TYPE = "MRCSettings"
AGGREGATE_ID = "global"
EVENT_SETTING_UPDATED = "MRCSettingUpdated"
EVENT_LOGO_SET = "MRCLogoSet"
EVENT_TOR_SET = "MRCTorSet"


def load(config=None) -> tuple[dict, dict | None, dict | None, int]:
    """Fold the settings stream into ``(fields, logo, tor, version)``."""
    fields = dict(MRC_SETTINGS_DEFAULTS)
    logo = None
    tor = None
    version = 0
    for event in read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID, config=config
    ):
        if event.event_type == EVENT_SETTING_UPDATED:
            fields[event.payload["field"]] = event.payload["value"]
        elif event.event_type == EVENT_LOGO_SET:
            logo = {
                "filename": event.payload["filename"],
                "original_name": event.payload["original_name"],
            }
        elif event.event_type == EVENT_TOR_SET:
            tor = {
                "filename": event.payload["filename"],
                "original_name": event.payload["original_name"],
            }
        version = event.stream_seq
    return fields, logo, tor, version


def get_settings(config=None) -> dict:
    """Current MRC settings: ``{fields, logo, tor}``."""
    fields, logo, tor, _ = load(config)
    return {"fields": fields, "logo": logo, "tor": tor}
