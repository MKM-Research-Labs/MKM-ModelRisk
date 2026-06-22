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
"""Identity configuration (coding rule R1).

The client's SSO authenticates users at the perimeter (e.g. a reverse proxy /
oauth2-proxy) and forwards the identity in trusted request headers. These names
are the headers we read; defaults follow the common oauth2-proxy convention and
are overridable per deployment via the environment.
"""
from __future__ import annotations

import os

# Header carrying the authenticated user's stable identifier.
IDENTITY_HEADER = os.environ.get("MKM_IDENTITY_HEADER", "X-Auth-Request-User")

# Header carrying a human-friendly display name (optional).
IDENTITY_NAME_HEADER = os.environ.get(
    "MKM_IDENTITY_NAME_HEADER", "X-Auth-Request-Preferred-Username"
)

# Actor used for local development when no SSO header is present. Only honoured
# when the caller explicitly allows a fallback (never in a hardened deployment).
IDENTITY_DEV_FALLBACK = os.environ.get("MKM_IDENTITY_DEV_FALLBACK", "dev@localhost")
