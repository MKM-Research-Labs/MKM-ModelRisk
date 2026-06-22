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

"""Static pipeline topology: dependency graph, optional steps, and step I/O."""

from __future__ import annotations

DEPENDENCY_GRAPH = {
    "gauges":             [],
    "synthetic_gauges":   ["gauges"],
    # properties depends on synthetic_gauges (not gauges) because
    # synthetic_gauges overwrites gauge.json before properties reads it.
    # Without this edge, _find_producer resolves to gauges and the
    # consumer/producer hash comparison flags properties as stale on
    # every successful run.
    "properties":         ["synthetic_gauges"],
    "mortgages":          ["properties"],
    "gaugehd":            ["gauges", "synthetic_gauges"],
    "stressm":            ["synthetic_gauges", "gaugehd"],
    "hazard":             ["synthetic_gauges", "stressm"],
    "propertyts":         ["properties", "hazard"],
    "propertytsd":        ["propertyts"],
    "propertytse":        ["propertyts"],
    "propertyhc":         ["propertyts", "hazard"],
    "propertyshd":        ["propertytsd", "hazard"],
    "propertyshe":        ["propertytse", "hazard"],
    "propertytsb":        ["propertyts"],
    "propertybri":        ["propertytsb", "hazard"],
    "counterparties":     [],
    "blotter":            ["hazard", "counterparties"],
    "typhoon":            ["properties"],
    "commercial":         ["synthetic_gauges"],
    "commercialts":       ["commercial", "hazard"],
    "commercialtsd":      ["commercialts"],
    "commercialtse":      ["commercialts"],
    "commercialhc":       ["commercialts", "hazard"],
    "commercialshd":      ["commercialtsd", "hazard"],
    "commercialshe":      ["commercialtse", "hazard"],
    "commercialtsb":      ["commercialts"],
    "commercialbri":      ["commercialtsb", "hazard"],
    # Wind-coupled peril scenarios (opt-in, require the typhoon damage join).
    # bow/baw additionally anchor on the BRI-resilient flood, so the peril ts
    # step also consumes the bri ts (propertytsb / commercialtsb).
    "property_peril_ts":  ["propertyts", "propertytsb", "typhoon"],
    "propertywin":        ["property_peril_ts"],
    "propertyfaw":        ["property_peril_ts"],
    "propertyfow":        ["property_peril_ts"],
    "propertybow":        ["property_peril_ts"],
    "propertybaw":        ["property_peril_ts"],
    "commercial_peril_ts": ["commercialts", "commercialtsb", "typhoon"],
    "commercialwin":      ["commercial_peril_ts"],
    "commercialfaw":      ["commercial_peril_ts"],
    "commercialfow":      ["commercial_peril_ts"],
    "commercialbow":      ["commercial_peril_ts"],
    "commercialbaw":      ["commercial_peril_ts"],
    # Fire-resilience credit over the commercial portfolio (opt-in).
    "fire":               ["commercial"],
    # Seismic-resilience credit over the commercial portfolio (opt-in).
    "seismic":            ["commercial"],
}

# External inputs: config/data files consumed by pipeline steps but not
# produced by any step.  The freshness check compares recorded hashes
# against the live file on disk instead of against a producer step.
EXTERNAL_INPUTS: set[str] = {"storm_control.json"}

# Optional steps: opt-in stages whose absence is expected for catchments
# that don't enable them. `typhoon` only runs for catchments with a
# `data/catch/<id>/tc.py` (tropical-cyclone exposure). When a step in
# this set has ZERO outputs on disk, the completeness check treats it
# as "not enabled" and skips it. If some outputs exist but others
# don't, the step is treated as partially-broken (still flagged).
OPTIONAL_STEPS: set[str] = {
    "typhoon",
    # Wind-coupled peril scenarios only run when the typhoon stage has
    # produced damage to join against (same opt-in gate as typhoon itself).
    "property_peril_ts", "propertywin", "propertyfaw", "propertyfow",
    "propertybow", "propertybaw",
    "commercial_peril_ts", "commercialwin", "commercialfaw", "commercialfow",
    "commercialbow", "commercialbaw",
    # Fire only runs when a commercial portfolio exists for the catchment.
    "fire",
    # Seismic only runs when a commercial portfolio exists for the catchment.
    "seismic",
}

STEP_IO = {
    "gauges":         {"inputs": [],
                       "outputs": ["gauge.json"]},
    "properties":     {"inputs": ["gauge.json"],
                       "outputs": ["property.json"]},
    "mortgages":      {"inputs": ["property.json"],
                       "outputs": ["loan.json"]},
    "synthetic_gauges": {"inputs": ["gauge.json"],
                        "outputs": ["gauge.json"]},
    "gaugehd":        {"inputs": ["gauge.json"],
                       "outputs": ["gaugehd/"]},
    "stressm":        {"inputs": ["gauge.json", "gaugehd/",
                                   "storm_control.json"],
                       "outputs": ["gaugets/", "stress_storms/",
                                   "storm_sequences.json",
                                   "sequence_gauge/"]},
    "hazard":         {"inputs": ["gauge.json", "gaugets/"],
                       "outputs": ["gaugehc.json", "gaugets/"]},
    "propertyts":     {"inputs": ["property.json", "gauge.json", "gaugets/"],
                       "outputs": ["propertyts/"]},
    "propertytsd":    {"inputs": ["property.json", "gauge.json", "gaugets/"],
                       "outputs": ["propertytsd/"]},
    "propertytse":    {"inputs": ["property.json", "gauge.json", "gaugets/"],
                       "outputs": ["propertytse/"]},
    "propertyhc":     {"inputs": ["propertyts/", "gaugehc.json", "gauge.json"],
                       "outputs": ["propertyhc.json"]},
    "propertyshd":    {"inputs": ["propertytsd/", "gaugehc.json", "gauge.json"],
                       "outputs": ["propertyshd.json"]},
    "propertyshe":    {"inputs": ["propertytse/", "gaugehc.json", "gauge.json"],
                       "outputs": ["propertyshe.json"]},
    "propertytsb":    {"inputs": ["property.json", "gauge.json", "gaugets/"],
                       "outputs": ["propertytsb/"]},
    "propertybri":    {"inputs": ["propertytsb/", "gaugehc.json", "gauge.json"],
                       "outputs": ["propertybri.json"]},
    "counterparties": {"inputs": [],
                       "outputs": ["counterparty.json"]},
    "blotter":        {"inputs": ["gaugehc.json", "counterparty.json"],
                       "outputs": ["prs/", "blotter/eod/",
                                   "blotter/market_state.json",
                                   "blotter/trade_marks.json"]},
    # typhoon's recorded inputs are catchment code files (tc.py), not
    # data artifacts produced by other steps, so STEP_IO inputs is empty.
    # The DEPENDENCY_GRAPH edge to properties captures pipeline ordering.
    "typhoon":        {"inputs": [],
                       "outputs": ["typhoon/ensemble.json",
                                   "typhoon/events/",
                                   "typhoon/windts/",
                                   "typhoon/damage/"]},
    "commercial":     {"inputs": [],
                       "outputs": ["commercial.json", "commercial_loan.json"]},
    "commercialts":   {"inputs": ["commercial.json", "gauge.json", "gaugets/"],
                       "outputs": ["commercialts/"]},
    "commercialtsd":  {"inputs": ["commercial.json", "gauge.json", "gaugets/"],
                       "outputs": ["commercialtsd/"]},
    "commercialtse":  {"inputs": ["commercial.json", "gauge.json", "gaugets/"],
                       "outputs": ["commercialtse/"]},
    "commercialhc":   {"inputs": ["commercialts/", "gaugehc.json", "gauge.json"],
                       "outputs": ["commercialhc.json"]},
    "commercialshd":  {"inputs": ["commercialtsd/", "gaugehc.json", "gauge.json"],
                       "outputs": ["commercialshd.json"]},
    "commercialshe":  {"inputs": ["commercialtse/", "gaugehc.json", "gauge.json"],
                       "outputs": ["commercialshe.json"]},
    "commercialtsb":  {"inputs": ["commercial.json", "gauge.json", "gaugets/"],
                       "outputs": ["commercialtsb/"]},
    "commercialbri":  {"inputs": ["commercialtsb/", "gaugehc.json", "gauge.json"],
                       "outputs": ["commercialbri.json"]},
    # Wind-coupled peril scenarios. The peril ts step derives five dirs from
    # the flood spine joined against typhoon/damage + storm_sequences.json;
    # each hc step prices one derived dir into its scenario file. win/faw/fow
    # anchor on the raw flood spine; bow/baw anchor on the BRI-resilient flood
    # (propertytsb / commercialtsb), so the peril ts step also reads that dir.
    "property_peril_ts":  {"inputs": ["propertyts/", "propertytsb/",
                                      "typhoon/damage/", "storm_sequences.json"],
                           "outputs": ["propertytsw/", "propertytsfaw/",
                                       "propertytsfow/", "propertytsbow/",
                                       "propertytsbaw/"]},
    "propertywin":        {"inputs": ["propertytsw/", "gaugehc.json", "gauge.json"],
                           "outputs": ["propertywin.json"]},
    "propertyfaw":        {"inputs": ["propertytsfaw/", "gaugehc.json", "gauge.json"],
                           "outputs": ["propertyfaw.json"]},
    "propertyfow":        {"inputs": ["propertytsfow/", "gaugehc.json", "gauge.json"],
                           "outputs": ["propertyfow.json"]},
    "propertybow":        {"inputs": ["propertytsbow/", "gaugehc.json", "gauge.json"],
                           "outputs": ["propertybow.json"]},
    "propertybaw":        {"inputs": ["propertytsbaw/", "gaugehc.json", "gauge.json"],
                           "outputs": ["propertybaw.json"]},
    "commercial_peril_ts": {"inputs": ["commercialts/", "commercialtsb/",
                                       "typhoon/damage/", "storm_sequences.json"],
                            "outputs": ["commercialtsw/", "commercialtsfaw/",
                                        "commercialtsfow/", "commercialtsbow/",
                                        "commercialtsbaw/"]},
    "commercialwin":      {"inputs": ["commercialtsw/", "gaugehc.json", "gauge.json"],
                           "outputs": ["commercialwin.json"]},
    "commercialfaw":      {"inputs": ["commercialtsfaw/", "gaugehc.json", "gauge.json"],
                           "outputs": ["commercialfaw.json"]},
    "commercialfow":      {"inputs": ["commercialtsfow/", "gaugehc.json", "gauge.json"],
                           "outputs": ["commercialfow.json"]},
    "commercialbow":      {"inputs": ["commercialtsbow/", "gaugehc.json", "gauge.json"],
                           "outputs": ["commercialbow.json"]},
    "commercialbaw":      {"inputs": ["commercialtsbaw/", "gaugehc.json", "gauge.json"],
                           "outputs": ["commercialbaw.json"]},
    "fire":           {"inputs": ["commercial.json"],
                       "outputs": ["fire/fire.json"]},
    "seismic":        {"inputs": ["commercial.json"],
                       "outputs": ["seismic/seismic.json"]},
}
