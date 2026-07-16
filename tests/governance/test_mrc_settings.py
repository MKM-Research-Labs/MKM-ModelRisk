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
