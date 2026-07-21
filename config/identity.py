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
"""Identity configuration (coding rule R1).

The client's SSO authenticates users at the perimeter (e.g. a reverse proxy /
oauth2-proxy) and forwards the identity in trusted request headers. These names
are the headers we read; defaults follow the common oauth2-proxy convention and
are overridable per deployment via the environment.
"""
from __future__ import annotations

import os

# Header carrying the authenticated user's stable identifier.
IDENTITY_HEADER = os.environ.get("IDENTITY_HEADER", "X-Auth-Request-User")

# Header carrying a human-friendly display name (optional).
IDENTITY_NAME_HEADER = os.environ.get(
    "IDENTITY_NAME_HEADER", "X-Auth-Request-Preferred-Username"
)

# Actor used for local development when no SSO header is present. Only honoured
# when the caller explicitly allows a fallback (never in a hardened deployment).
IDENTITY_DEV_FALLBACK = os.environ.get("IDENTITY_DEV_FALLBACK", "dev@localhost")
