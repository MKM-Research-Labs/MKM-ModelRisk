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

"""Wind damage-function field chains (RED — feed the PRS wind spread).

Keys are CDM dotted paths from the record root. The wind fields live under the
shared ``ProtectionMeasures`` block, so the same paths apply to residential and
commercial assets. Source of truth: ``src/models/winddamage/cdm.py`` and the
wind vulnerability model (MKM-WD-001).
"""

from .tiers import RED

_WD = "MKM-WD-001 wind damage"
_PRS = "PRS wind spread"

# Shared downstream tail: damage ratio -> PRS wind spread.
_WIND_TAIL = [
    {"node": "bri_wind_damage()", "kind": "function",
     "ref": "src/models/winddamage/vulnerability.py"},
    {"node": "per-event wind damage_ratio", "kind": "output",
     "ref": "src/models/winddamage/event.py"},
    {"node": "PRS wind spread (bps)", "kind": "output",
     "ref": "src/port/src/property/hc/pricing/_wind.py"},
]

WIND_FIELDS = {
    "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIWindScore": {
        "tier": RED,
        "summary": "Wind resilience score; shifts the damage curve's v_50 upward (a more "
                   "resilient building fails at higher wind), feeding the PRS wind spread.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "BRIWindScore (CDM)", "kind": "field"},
            {"node": "bri_v50_shift()", "kind": "function",
             "ref": "src/models/winddamage/bri_shift.py"},
        ] + _WIND_TAIL,
    },
    "ProtectionMeasures.HazardProfile.WindThresholdMinorMps": {
        "tier": RED,
        "summary": "Damage-onset wind threshold (v_50, m/s); the centre of the wind "
                   "vulnerability sigmoid and the persistence reference level.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "WindThresholdMinorMps (CDM)", "kind": "field"},
            {"node": "resolve_threshold_ms()", "kind": "function",
             "ref": "src/models/winddamage/threshold.py"},
        ] + _WIND_TAIL,
    },
    "ProtectionMeasures.HazardProfile.WindThresholdMajorMps": {
        "tier": RED,
        "summary": "Severe-damage wind threshold; fallback v_50 when the minor threshold "
                   "is absent.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "WindThresholdMajorMps (CDM)", "kind": "field"},
            {"node": "resolve_threshold_ms()", "kind": "function",
             "ref": "src/models/winddamage/threshold.py"},
        ] + _WIND_TAIL,
    },
    "ProtectionMeasures.HazardProfile.WindThresholdKph": {
        "tier": RED,
        "summary": "Legacy wind threshold (km/h); converted to m/s as the v_50 fallback.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "WindThresholdKph (CDM, legacy)", "kind": "field"},
            {"node": "resolve_threshold_ms()  (÷3.6)", "kind": "function",
             "ref": "src/models/winddamage/threshold.py"},
        ] + _WIND_TAIL,
    },
}
