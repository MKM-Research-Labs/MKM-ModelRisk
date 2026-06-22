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

"""Flood damage-function field chains (RED — feed the PRS flood spread).

Keys are CDM dotted paths from the record root. Construction / risk fields sit
under the asset-specific header (``PropertyHeader`` for residential,
``CommercialAsset`` for commercial), so both variants are registered. Source of
truth: ``src/models/floodrisk/depth_damage.py`` and the composite BRI stilt.
"""

from .tiers import RED

_FR = "MKM-DD-001 flood depth-damage"
_PRS = "PRS flood spread"

_FLOOD_TAIL = [
    {"node": "bri_depth_damage()", "kind": "function",
     "ref": "src/models/floodrisk/depth_damage.py"},
    {"node": "per-storm flood damage_ratio", "kind": "output",
     "ref": "src/port/src/property/hc/pricing"},
    {"node": "PRS flood spread (bps)", "kind": "output",
     "ref": "src/port/src/property/hc/pricing"},
]


def _floor_entry(label):
    return {
        "tier": RED,
        "summary": f"{label} sets the effective flood depth (depth − floor − stilt) the "
                   "depth-damage polynomial sees, feeding the PRS flood spread.",
        "consumers": [_FR, _PRS],
        "chain": [{"node": f"{label} (CDM)", "kind": "field"}] + _FLOOD_TAIL,
    }


def _gauge_stage_entry(label):
    """Gauge flood-stage threshold (alert / warning / severe) — RED.

    These thresholds grade each storm peak into a flood event and set its
    severity at the gauge, driving the gauge flood spread the property PRS
    basis is decomposed from. Source: ``src/port/cdm/gauge/mapping.py``.
    """
    return {
        "tier": RED,
        "summary": f"{label} (gauge flood-stage threshold) grades each storm peak into a "
                   "flood event and sets its severity at the gauge, driving the gauge "
                   "flood spread the property PRS basis is decomposed from.",
        "consumers": ["Gauge flood-event grading", _PRS],
        "chain": [
            {"node": f"{label} (CDM)", "kind": "field"},
            {"node": "gauge flood-stage mapping", "kind": "function",
             "ref": "src/port/cdm/gauge/mapping.py"},
            {"node": "gauge flood-event grading", "kind": "output"},
            {"node": "gauge flood spread (bps)", "kind": "output"},
            {"node": "PRS property spread (bps)", "kind": "output"},
        ],
    }


FLOOD_FIELDS = {
    # Composite BRI — shared by flood, wind, fire and seismic damage curves.
    "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIScore": {
        "tier": RED,
        "summary": "Composite resilience score; shifts every peril damage curve "
                   "(flood floor uplift, wind/fire/seismic v_50), feeding the PRS spread.",
        "consumers": [_FR, "MKM-WD-001 wind", "PRS spread"],
        "chain": [
            {"node": "BRIScore (composite, CDM)", "kind": "field"},
            {"node": "bri_stilt() / bri_v50_shift()", "kind": "function",
             "ref": "src/models/floodrisk/depth_damage.py"},
            {"node": "peril damage_ratio", "kind": "output"},
            {"node": "PRS spread (bps)", "kind": "output"},
        ],
    },
    "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIFloodScore": {
        "tier": RED,
        "summary": "Flood resilience score; applies a floor-level uplift (resilience credit) "
                   "in the depth-damage curve, feeding the PRS flood spread.",
        "consumers": [_FR, _PRS],
        "chain": [
            {"node": "BRIFloodScore (CDM)", "kind": "field"},
            {"node": "bri_stilt()", "kind": "function",
             "ref": "src/models/floodrisk/depth_damage.py"},
        ] + _FLOOD_TAIL,
    },
    "PropertyHeader.Construction.FloorLevelMeters": _floor_entry("Ground-floor level"),
    "CommercialAsset.Construction.FloorLevelMeters": _floor_entry("Ground-floor level"),
    "PropertyHeader.Construction.BRIAdjustedFloorLevelMeters":
        _floor_entry("BRI-adjusted floor level"),
    "CommercialAsset.Construction.BRIAdjustedFloorLevelMeters":
        _floor_entry("BRI-adjusted floor level"),
    "PropertyHeader.Construction.StiltsHeight": _floor_entry("Stilt height"),
    "CommercialAsset.Construction.StiltsHeight": _floor_entry("Stilt height"),
    "PropertyHeader.RiskAssessment.GroundLevelMeters": _floor_entry("Ground elevation"),
    "CommercialAsset.RiskAssessment.GroundLevelMeters": _floor_entry("Ground elevation"),
    # Gauge flood-stage thresholds — set flood-event triggers / severity at the gauge.
    "FloodGauge.FloodStage.UK.FloodAlert": _gauge_stage_entry("Flood alert level"),
    "FloodGauge.FloodStage.UK.FloodWarning": _gauge_stage_entry("Flood warning level"),
    "FloodGauge.FloodStage.UK.SevereFloodWarning":
        _gauge_stage_entry("Severe flood warning level"),
}
