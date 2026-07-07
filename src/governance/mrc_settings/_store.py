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
