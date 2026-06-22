# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Field-usage downstream lineage for CDM fields.

Classifies each CDM field by how far downstream its value travels — RED (feeds
PRS pricing), AMBER (contract / operational) or GREEN (report only) — and
returns the lineage chain to the consuming model / output. See resolve.py for
the public functions.
"""

from .registry import AMBER_PREFIXES, EXACT_FIELDS
from .resolve import classify, lineage, tier_meta
from .tiers import AMBER, DEFAULT_TIER, GREEN, RED, TIER_META

__all__ = [
    "classify",
    "lineage",
    "tier_meta",
    "RED",
    "AMBER",
    "GREEN",
    "DEFAULT_TIER",
    "TIER_META",
    "EXACT_FIELDS",
    "AMBER_PREFIXES",
]
