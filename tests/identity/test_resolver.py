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
"""Tests for resolving the acting principal from SSO headers."""
from __future__ import annotations

import pytest

from src.identity import IdentityError, resolve_principal
from src.identity._principal import SOURCE_FALLBACK, SOURCE_SSO_HEADER


def test_resolves_actor_and_name_from_headers():
    principal = resolve_principal(
        {
            "X-Auth-Request-User": "alice@corp",
            "X-Auth-Request-Preferred-Username": "Alice Smith",
        }
    )
    assert principal.actor == "alice@corp"
    assert principal.display_name == "Alice Smith"
    assert principal.source == SOURCE_SSO_HEADER


def test_header_lookup_is_case_insensitive():
    principal = resolve_principal({"x-auth-request-user": "bob@corp"})
    assert principal.actor == "bob@corp"
    # No name header -> display name falls back to the actor.
    assert principal.display_name == "bob@corp"


def test_fallback_actor_when_no_header_and_allowed():
    principal = resolve_principal({}, allow_fallback=True)
    assert principal.actor == "dev@localhost"
    assert principal.source == SOURCE_FALLBACK


def test_missing_header_without_fallback_raises():
    with pytest.raises(IdentityError):
        resolve_principal({}, allow_fallback=False)
