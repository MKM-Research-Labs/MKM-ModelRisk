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
"""The ERM read API's parameters (coding rule R1).

Model risk does not stop at this platform: it feeds the firm's enterprise risk
management, in two named places. An operational-risk function consumes what has
actually failed and which controls are not holding; a strategic view consumes how
much of the estate meets the standard its divisions set, and which way that is
moving. The payload is shaped around those two consumers rather than around how
this platform happens to store things.

Everything here is READ-ONLY by contract. There is no write endpoint on this
surface at any version: if the ERM could change the governance record, the record
would no longer be the thing the committee signed.
"""
from __future__ import annotations

import os

# The contract's major version, carried in the path and in every payload. An ERM
# integration outlives our refactors, and an adopter cannot redeploy their ERM
# because we renamed something — so the path is versioned from the first release
# rather than when the first breaking change turns up.
ERM_SCHEMA_VERSION = "v1"
ERM_API_PREFIX = f"/api/erm/{ERM_SCHEMA_VERSION}"

# Phase 0 shared-token auth, the same stub the ingest surface carries and the same
# guard (``src.web._token_auth``). A separate token from ingest deliberately: the
# two surfaces have opposite privileges — one writes the governance record, one may
# only read it — and a single credential for both would collapse that distinction.
ERM_TOKEN_HEADER = os.environ.get("ERM_TOKEN_HEADER", "X-ERM-Token")
ERM_DEV_TOKEN = os.environ.get("ERM_DEV_TOKEN", "dev-erm-token")

# The most attention items one response will carry. Reached only by an estate in a
# state no dashboard can help with; when it bites the response still reports the
# true total and says it truncated, because a capped list that says nothing about
# the cap reads as "that is all there is".
ERM_ATTENTION_CAP = int(os.environ.get("ERM_ATTENTION_CAP", "500"))

# Where a row's ``href`` points a person who clicks through from the ERM. Empty
# means "derive it from the request", which is right for a single deployment; an
# institution whose ERM sits behind a different hostname than the one this API is
# called on sets it explicitly.
ERM_CONSOLE_BASE = os.environ.get("ERM_CONSOLE_BASE", "")

# Which console tab a kind of record opens on, for that link. Held here rather than
# built in the view so a re-organised console is a config change and the ERM's links
# do not quietly start 404-ing.
ERM_CONSOLE_TAB = {
    "Model": "inventory",
    "Product": "product",
    "ML Application": "mlapps",
    "Committee action": "mrc",
    "Division": "reference",
}
