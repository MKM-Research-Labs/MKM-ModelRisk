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

"""Assembled field-usage registry.

Merges the per-concern RED chains (wind, flood, fire/seismic, direct PRS) into
one exact-path lookup, and exposes the AMBER prefix rules. Pure data assembly —
no behaviour (that lives in resolve.py).
"""

from ._contract import AMBER_PREFIXES
from ._fire_seismic import FIRE_SEISMIC_FIELDS
from ._flood import FLOOD_FIELDS
from ._prs import PRS_FIELDS
from ._wind import WIND_FIELDS

# Exact CDM dotted path -> usage entry. RED entries only (AMBER is by prefix,
# GREEN is the default).
EXACT_FIELDS = {
    **WIND_FIELDS,
    **FLOOD_FIELDS,
    **FIRE_SEISMIC_FIELDS,
    **PRS_FIELDS,
}

__all__ = ["EXACT_FIELDS", "AMBER_PREFIXES"]
