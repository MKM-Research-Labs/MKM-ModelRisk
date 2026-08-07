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
"""Is this actor somebody the institution has registered? (permissions phase P1)

The console sends a person's NAME as the actor and an SSO deployment sends their email,
so either identifies them. Matching is case- and whitespace-insensitive because the two
sources spell the same person differently.

Policy lives in ``config.permissions``; this module only applies it.
"""
from __future__ import annotations

from config.database import PROTECTED_DB_NAMES, DatabaseConfig
from config.identity import SYSTEM_ACTOR
from config.permissions import (
    ALLOW_WHEN_NO_PEOPLE_REGISTERED,
    ENFORCE_KNOWN_ACTORS,
    MACHINE_ACTOR_PREFIX,
)


class UnrecognisedActor(RuntimeError):
    """Raised when a change is authored by an identity nobody has registered."""


def _normalise(value: str) -> str:
    return " ".join(str(value or "").split()).casefold()


def enforcement_applies(database_name: str | None = None) -> bool:
    """Whether the known-actor rule is in force for the database in use."""
    if ENFORCE_KNOWN_ACTORS == "never":
        return False
    if ENFORCE_KNOWN_ACTORS == "always":
        return True
    name = database_name if database_name is not None else DatabaseConfig.from_env().name
    return name in PROTECTED_DB_NAMES


def registered_identities() -> set[str]:
    """Every identity the People list recognises — each person's name and their email."""
    # Imported here: the reference store reads a view, and identity must stay importable
    # by modules that have no database at hand.
    from src.governance.reference import get_reference_lists

    identities: set[str] = set()
    for person in get_reference_lists().get("people") or []:
        for field in ("name", "email"):
            value = person.get(field)
            if value:
                identities.add(_normalise(value))
    return identities


def roles_for(actor: str) -> frozenset[str]:
    """The roles the People register gives this actor (permissions P2).

    Empty for an unregistered actor, for the platform and machine principals, and for a
    person nobody has given a role yet — so a caller must decide what "no roles" means
    rather than being handed a default. P3 answers that; today nothing consumes it but
    the Admin screen that sets them.
    """
    from src.governance.reference import get_reference_lists

    wanted = _normalise(actor)
    for person in get_reference_lists().get("people") or []:
        if wanted in {_normalise(person.get(f)) for f in ("name", "email") if person.get(f)}:
            return frozenset(person.get("roles") or ())
    return frozenset()


def is_recognised(actor: str) -> bool:
    """Whether ``actor`` is the platform, a machine producer, or a registered person."""
    if not actor:
        return False
    if actor == SYSTEM_ACTOR or actor.startswith(MACHINE_ACTOR_PREFIX):
        return True
    people = registered_identities()
    if not people and ALLOW_WHEN_NO_PEOPLE_REGISTERED:
        return True
    return _normalise(actor) in people


def assert_recognised(actor: str) -> None:
    """Refuse a change authored by an unregistered identity.

    The message names the actor and the remedy, because the honest cause is usually a
    misconfigured header or a script borrowing a test identity — not an attack.
    """
    if not enforcement_applies() or is_recognised(actor):
        return
    raise UnrecognisedActor(
        f"'{actor}' is not a registered person, so it cannot author a change on this "
        "database. Add them under Admin -> People, or correct the identity the caller "
        "is sending."
    )
