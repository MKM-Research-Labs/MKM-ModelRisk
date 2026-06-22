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

"""Direct PRS pricing inputs (RED) that do not pass through a damage function.

Valuation drives the notional / loss amount; the reference gauges select the
hazard-curve basket that prices the swap. Keys are CDM dotted paths from the
record root.
"""

from .tiers import RED

_PRS = "PRS pricing"


def _valuation_entry():
    return {
        "tier": RED,
        "summary": "Asset value sets the PRS notional / loss-at-risk that the spread is "
                   "applied to.",
        "consumers": [_PRS],
        "chain": [
            {"node": "PropertyValue (CDM)", "kind": "field"},
            {"node": "notional / loss-at-risk", "kind": "function",
             "ref": "src/port/src/property/hc/pricing"},
            {"node": "PRS premium / protection leg", "kind": "output"},
        ],
    }


PRS_FIELDS = {
    "PropertyHeader.Valuation.PropertyValue": _valuation_entry(),
    "CommercialAsset.Valuation.PropertyValue": _valuation_entry(),
    "PropertyHeader.Contents.ContentsValue": {
        "tier": RED,
        "summary": "Contents replacement value adds to the loss-at-risk priced by the PRS.",
        "consumers": [_PRS],
        "chain": [
            {"node": "ContentsValue (CDM)", "kind": "field"},
            {"node": "loss-at-risk", "kind": "function"},
            {"node": "PRS protection leg", "kind": "output"},
        ],
    },
    "PropertyHeader.ReferenceGauges": {
        "tier": RED,
        "summary": "Reference gauges select the hazard-curve basket that prices the swap — "
                   "the flood hazard transmitted to this asset.",
        "consumers": ["MKM-GH-001 hazard curves", _PRS],
        "chain": [
            {"node": "ReferenceGauges (CDM)", "kind": "field"},
            {"node": "IDW gauge basket", "kind": "function",
             "ref": "src/port/src/property/hc"},
            {"node": "property hazard curve", "kind": "output",
             "ref": "data/input/<catchment>/propertyhc.json"},
            {"node": "PRS flood spread (bps)", "kind": "output"},
        ],
    },
}
