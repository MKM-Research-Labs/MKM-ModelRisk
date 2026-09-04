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
"""Only a registered person may author a change (permissions P1).

The rule that would have refused ``alice@corp`` — the web tests' own header — when an
ad-hoc script pointed at the live database on 2026-08-06.
"""
from __future__ import annotations

import pytest

from src.governance.reference import add_option
from src.identity import _recognition
from src.identity._recognition import (
    UnrecognisedActor,
    assert_recognised,
    enforcement_applies,
    is_recognised,
)

PEOPLE = [
    {"name": "Johnny Mattimore", "email": "johnny.mattimore@mkmresearchlabs.com"},
    {"name": "David Kelly", "email": "david.kelly@mkmresearchlabs.com"},
]


@pytest.fixture
def registered(monkeypatch):
    """Enforcement on, with a People list — a hardened deployment."""
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "always")
    monkeypatch.setattr(_recognition, "registered_identities",
                        lambda: {" ".join(str(p[f]).split()).casefold()
                                 for p in PEOPLE for f in ("name", "email")})


def test_a_registered_person_is_recognised_by_name_or_email(registered):
    # The console sends the person's NAME; an SSO deployment sends their email. Both
    # identify the same person, so both are accepted.
    assert is_recognised("Johnny Mattimore")
    assert is_recognised("david.kelly@mkmresearchlabs.com")


def test_recognition_ignores_case_and_spacing(registered):
    """The two identity sources spell the same person differently."""
    assert is_recognised("  johnny   MATTIMORE ")


def test_the_test_suite_identity_is_refused(registered):
    """The 2026-08-06 breach: alice@corp is a fixture header, not a person."""
    with pytest.raises(UnrecognisedActor) as excinfo:
        assert_recognised("alice@corp")
    message = str(excinfo.value)
    assert "alice@corp" in message          # names who was refused
    assert "Admin -> People" in message     # and the remedy, since the usual cause is
    assert "cannot author" in message       # a misconfigured caller, not an attack


def test_an_empty_actor_is_refused(registered):
    with pytest.raises(UnrecognisedActor):
        assert_recognised("")


def test_the_platform_and_machine_producers_are_not_people(registered):
    """Seeding and ingest are legitimate authors that will never be in People. Scoping
    what a machine may do is P6; this rule only lets them through."""
    assert is_recognised("system")
    assert is_recognised("ingest:mkm-physicalrisk")


def test_a_fresh_install_is_not_locked_out(monkeypatch):
    """A new adopter has an empty People list and a protected database name; refusing
    every actor would prevent them registering the first person."""
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "always")
    monkeypatch.setattr(_recognition, "registered_identities", set)
    assert is_recognised("whoever.sets.this.up@adopter.com")


def test_the_rule_stands_down_on_a_scratch_database(monkeypatch):
    """Default policy: protected databases only, so the suite and throwaway
    environments are unaffected — which is why this file's own actor works."""
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "protected")
    assert enforcement_applies("mkm_modelrisk") is True
    assert enforcement_applies("mkm_modelrisk_demo") is True
    assert enforcement_applies("mkm_modelrisk_test_p123") is False
    assert enforcement_applies("mkm_modelrisk_scratch") is False


def test_enforcement_can_be_turned_off_and_on_wholesale(monkeypatch):
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "never")
    assert enforcement_applies("mkm_modelrisk") is False
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "always")
    assert enforcement_applies("mkm_modelrisk_test_p123") is True


# --- The People list itself -------------------------------------------------
# Every test above substitutes ``registered_identities``, so the one function that
# actually reads the register was never run. These exercise it for real: the rule
# is only as good as the lookup underneath it.

def test_registered_identities_reads_both_spellings_from_people():
    """A person is recognised by either spelling, normalised the same way the
    incoming actor is — the console sends the name, SSO sends the email."""
    add_option(list_name="people",
               fields={"name": "  Jane   Doe ", "email": "JANE@firm"}, actor="admin")
    assert _recognition.registered_identities() == {"jane doe", "jane@firm"}


def test_a_person_recorded_without_an_email_is_still_recognised():
    """The People screen only requires a name, so a half-filled row must not
    become an identity nobody can author under."""
    add_option(list_name="people", fields={"name": "Rob Ellis"}, actor="admin")
    assert _recognition.registered_identities() == {"rob ellis"}


def test_an_empty_people_list_recognises_nobody():
    assert _recognition.registered_identities() == set()


def test_enforcement_reads_the_database_in_use_when_none_is_named(monkeypatch):
    """The production call site passes no name: the rule has to find the database
    itself, and the suite's own disposable one must fall outside it."""
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "protected")
    assert enforcement_applies() is False
