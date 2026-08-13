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
"""Identity: resolve the acting principal from the client's SSO, and say whether the
institution recognises them."""
from src.identity._principal import Principal
from src.identity._recognition import (
    UnrecognisedActor,
    assert_recognised,
    enforcement_applies,
    is_recognised,
    roles_for,
    same_person,
)
from src.identity.resolver import IdentityError, ingest_principal, resolve_principal

__all__ = [
    "Principal",
    "IdentityError",
    "UnrecognisedActor",
    "resolve_principal",
    "ingest_principal",
    "assert_recognised",
    "is_recognised",
    "enforcement_applies",
    "roles_for",
    "same_person",
]
