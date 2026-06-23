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
"""Tests for the MRC settings singleton."""
from __future__ import annotations

import pytest

from src.database import append_event
from src.governance.errors import DomainError
from src.governance.mrc_settings import get_settings, set_field, set_logo


def test_load_ignores_unrelated_event():
    append_event(
        aggregate_type="MRCSettings", aggregate_id="global",
        event_type="Noise", payload={}, actor="system",
    )
    assert get_settings()["fields"]["frequency"] == "Quarterly"


def test_defaults_present():
    settings = get_settings()
    assert settings["fields"]["frequency"] == "Quarterly"
    assert settings["logo"] is None


def test_set_field_updates():
    set_field(field="chair", value="Johnny Mattimore", actor="admin")
    assert get_settings()["fields"]["chair"] == "Johnny Mattimore"


def test_set_field_unknown_raises():
    with pytest.raises(DomainError):
        set_field(field="bogus", value="x", actor="admin")


def test_set_field_invalid_choice_raises():
    with pytest.raises(DomainError):
        set_field(field="frequency", value="Hourly", actor="admin")


def test_set_logo_records_metadata():
    set_logo(filename="logo.png", original_name="Company Logo.png", actor="admin")
    logo = get_settings()["logo"]
    assert logo["filename"] == "logo.png"
    assert logo["original_name"] == "Company Logo.png"
