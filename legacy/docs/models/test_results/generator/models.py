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

"""Test-to-model mapping and model metadata."""

# Maps test file paths (relative to project root) to model IDs.
# Updated to reflect modular test structure (no test_ prefix).
TEST_MODEL_MAP = {
    # ---------------------------------------------------------------------------
    # MKM-GH-001  GEV Hazard Model
    # ---------------------------------------------------------------------------
    'tests/port/hazard/hazard_builder.py':              'MKM-GH-001',

    # ---------------------------------------------------------------------------
    # MKM-SI-001  Storm Intensity Distribution
    # ---------------------------------------------------------------------------
    'tests/models/intensity/distribution.py':           'MKM-SI-001',
    'tests/port/storm/storm_generator.py':              'MKM-SI-001',
    'tests/port/storm/storm_duration.py':               'MKM-SI-001',
    'tests/port/storm/storm_gap.py':                    'MKM-SI-001',
    'tests/port/storm/storm_sequence.py':               'MKM-SI-001',

    # ---------------------------------------------------------------------------
    # MKM-SG-001  Storm-Gauge Response Model
    # ---------------------------------------------------------------------------
    'tests/models/stormgauge/forward_model.py':         'MKM-SG-001',
    'tests/port/gauge/gauge_generator.py':              'MKM-SG-001',
    'tests/port/gauge/rand_gauge.py':                   'MKM-SG-001',

    # ---------------------------------------------------------------------------
    # MKM-PR-001  PRS Pricing Model
    # ---------------------------------------------------------------------------
    'tests/models/prs/prs_pricing.py':                  'MKM-PR-001',
    'tests/port/propertyhc/basis.py':                   'MKM-PR-001',
    'tests/port/propertyhc/generator.py':               'MKM-PR-001',
    'tests/port/propertyhc/pricing.py':                 'MKM-PR-001',
    'tests/models/schedule/maturity.py':                'MKM-PR-001',

    # ---------------------------------------------------------------------------
    # MKM-PV-001  Property Valuation
    # ---------------------------------------------------------------------------
    'tests/port/property/property_generator.py':        'MKM-PV-001',
    'tests/port/property/rand_property_mortgage.py':    'MKM-PV-001',

    # ---------------------------------------------------------------------------
    # MKM-MP-001  Mortgage Pricer
    # ---------------------------------------------------------------------------
    'tests/port/mortgage/mortgage_generator.py':        'MKM-MP-001',
    'tests/models/mortgage/credit.py':                  'MKM-MP-001',
    'tests/models/mortgage/payment.py':                 'MKM-MP-001',
    'tests/models/mortgage/pricing.py':                 'MKM-MP-001',

    # ---------------------------------------------------------------------------
    # MKM-DD-001  Flood Risk (Depth-Damage / Velocity)
    # ---------------------------------------------------------------------------
    'tests/models/velocity.py':                         'MKM-DD-001',
    'tests/models/risk/risk_assessor.py':               'MKM-DD-001',
    'tests/models/floodrisk/risk_visualization.py':     'MKM-DD-001',

    # ---------------------------------------------------------------------------
    # MKM-SS-001  Storm Sequence Generator
    # ---------------------------------------------------------------------------
    'tests/port/storm/sequence_gen.py':                 'MKM-SS-001',
    'tests/port/storm/batch_generator.py':              'MKM-SS-001',
    'tests/port/storm/stressm.py':                      'MKM-SS-001',

    # ---------------------------------------------------------------------------
    # MKM-FPO-001  Flood Polynomial Model
    # ---------------------------------------------------------------------------
    'tests/models/stress/flood_poly.py':                'MKM-FPO-001',

    # MKM-FC-001  Flood Probability Classifier
    # ---------------------------------------------------------------------------
    'tests/port/stress/classifier.py':                  'MKM-FC-001',
    'tests/port/stress/hydrograph.py':                  'MKM-FC-001',
    'tests/port/stress/labels.py':                      'MKM-FC-001',
    'tests/port/stress/sampling.py':                    'MKM-FC-001',
    'tests/port/stress/storms_file.py':                 'MKM-FC-001',
    'tests/routes/trading/stress_routes.py':            'MKM-FC-001',
    'tests/routes/trading/port_stress_routes.py':       'MKM-FC-001',

    # ---------------------------------------------------------------------------
    # MKM-TD-001  Trading Desk (Delta Engine, P&L, EOD, Blotter)
    # ---------------------------------------------------------------------------
    'tests/models/trading/delta/engine.py':             'MKM-TD-001',
    'tests/models/trading/delta/formulas.py':           'MKM-TD-001',
    'tests/models/trading/pnl/daily_pnl.py':            'MKM-TD-001',
    'tests/models/trading/pnl/eod.py':                  'MKM-TD-001',
    'tests/models/trading/pnl/marks.py':                'MKM-TD-001',
    'tests/models/trading/book/leg_pvs.py':             'MKM-TD-001',
    'tests/models/trading/book/market_making.py':       'MKM-TD-001',
    'tests/models/trading/book/thames_central.py':      'MKM-TD-001',
    'tests/models/trading/historical_eod.py':           'MKM-TD-001',
    'tests/models/trading/market_state.py':             'MKM-TD-001',
    'tests/models/trading/stress_hydrograph.py':        'MKM-TD-001',
    'tests/routes/trading/blotter_routes.py':           'MKM-TD-001',
    'tests/routes/trading/curves_routes.py':            'MKM-TD-001',
    'tests/routes/trading/eod_routes.py':               'MKM-TD-001',
    'tests/routes/trading/market_state_routes.py':      'MKM-TD-001',
    'tests/routes/trading/risk_routes.py':              'MKM-TD-001',
    'tests/visual/trading/blotter_detail.py':           'MKM-TD-001',
    'tests/visual/trading/eod_detail.py':               'MKM-TD-001',
    'tests/visual/trading/market_detail.py':            'MKM-TD-001',

    # ---------------------------------------------------------------------------
    # MKM-SP-001  Spatial Interpolation
    # ---------------------------------------------------------------------------
    'tests/models/floodrisk/spatial.py':                'MKM-SP-001',
    'tests/models/floodrisk/test_spatial_coverage.py':  'MKM-SP-001',

    # ---------------------------------------------------------------------------
    # MKM-IP-001  Insurance Premium
    # ---------------------------------------------------------------------------
    'tests/models/valuation/insurance.py':              'MKM-IP-001',

    # ---------------------------------------------------------------------------
    # MKM-GHD-001  GaugeHD Synthetic
    # ---------------------------------------------------------------------------
    'tests/models/synthetic.py':                        'MKM-GHD-001',
    'tests/models/hazard/test_synthetic_coverage.py':   'MKM-GHD-001',
    'tests/port/gauge/test_synthetic_gauge.py':         'MKM-GHD-001',
    'tests/port/gauge/test_synthetic_gauge_coverage.py': 'MKM-GHD-001',
    'tests/port/gauge/test_gaugehd_runner.py':          'MKM-GHD-001',
    'tests/port/gauge/test_gaugehd_module.py':          'MKM-GHD-001',
    'tests/port/gauge/test_synthetic_gauge_lineage.py': 'MKM-GHD-001',

    # ---------------------------------------------------------------------------
    # MKM-ST-001  Stress Test Pipeline
    # ---------------------------------------------------------------------------
    'tests/port/storm/stressm/test_batch_train.py':    'MKM-ST-001',
    'tests/port/storm/stressm/test_generate.py':       'MKM-ST-001',
    'tests/port/storm/stressm/test_records.py':        'MKM-ST-001',
    'tests/port/storm/stressm/test_single_gauge.py':   'MKM-ST-001',
    'tests/port/storm/stressm/test_gauge_parser.py':   'MKM-ST-001',
    'tests/port/storm/stressm/test_helpers.py':        'MKM-ST-001',
    'tests/port/storm/stressm/test_pipeline_coverage.py': 'MKM-ST-001',
    'tests/port/storm/stressm/test_classifier.py':     'MKM-ST-001',

    # ---------------------------------------------------------------------------
    # MKM-PF-001  Property Flood Response
    # ---------------------------------------------------------------------------
    'tests/models/risk/risk_assessor.py':               'MKM-PF-001',

    # ---------------------------------------------------------------------------
    # MKM-BRI-001  Building Resilience Index Model
    # ---------------------------------------------------------------------------
    'tests/port/cdm/test_bri_helper.py':                'MKM-BRI-001',
    'tests/port/cdm/test_bri_aggregation.py':           'MKM-BRI-001',
    'tests/port/cdm/test_resilience_generator.py':      'MKM-BRI-001',
    'tests/port/cdm/test_consistency_fixes.py':         'MKM-BRI-001',
    'tests/port/cdm/test_schema_invariants.py':         'MKM-BRI-001',
    'tests/port/cdm/test_flood_resilience_model.py':    'MKM-BRI-001',

    # ---------------------------------------------------------------------------
    # MKM-BRF-001  BRI-Adjusted Floor Level Model
    # ---------------------------------------------------------------------------
    'tests/models/floodrisk/test_bri_floor_level.py':   'MKM-BRF-001',

    # ---------------------------------------------------------------------------
    # CDM-ALL  CDM Schema Validation
    # ---------------------------------------------------------------------------
    'tests/port/cdm/schemas.py':                        'CDM-ALL',
    'tests/port/cdm/schema_basics.py':                  'CDM-ALL',
    'tests/port/cdm/gauge_mapping.py':                  'CDM-ALL',
    'tests/port/cdm/property_mapping.py':               'CDM-ALL',
    'tests/port/cdm/mortgage_mapping.py':               'CDM-ALL',
    'tests/port/cdm/cdm_all.py':                        'CDM-ALL',

    # ---------------------------------------------------------------------------
    # MKM-TC-001  Tropical Cyclone Progression and Wind-Field
    # ---------------------------------------------------------------------------
    'tests/config/test_typhoon.py':                     'MKM-TC-001',
    'tests/models/typhoon/data_structures.py':          'MKM-TC-001',
    'tests/models/typhoon/genesis.py':                  'MKM-TC-001',
    'tests/models/typhoon/transitions.py':              'MKM-TC-001',
    'tests/models/typhoon/particle_filter.py':          'MKM-TC-001',
    'tests/models/typhoon/plausibility.py':             'MKM-TC-001',
    'tests/models/typhoon/wind_field/geometry.py':      'MKM-TC-001',
    'tests/models/typhoon/wind_field/radial.py':        'MKM-TC-001',
    'tests/models/typhoon/wind_field/asymmetry.py':     'MKM-TC-001',
    'tests/models/typhoon/wind_field/surface.py':       'MKM-TC-001',
    'tests/models/typhoon/wind_field/point.py':         'MKM-TC-001',
    'tests/models/typhoon/wind_field/time_series.py':   'MKM-TC-001',
    'tests/models/typhoon/wind_field/windfield_class.py':'MKM-TC-001',
    'tests/models/typhoon/pipeline/results.py':         'MKM-TC-001',
    'tests/models/typhoon/pipeline/aggregation.py':     'MKM-TC-001',
    'tests/models/typhoon/pipeline/event.py':           'MKM-TC-001',
    'tests/models/typhoon/pipeline/ensemble.py':        'MKM-TC-001',
    'tests/models/typhoon/import_discipline.py':        'MKM-TC-001',

    # ---------------------------------------------------------------------------
    # MKM-WS-001  Event Wind Lookup (wind-at-point query)
    # ---------------------------------------------------------------------------
    'tests/models/windspeed/interpolation.py':          'MKM-WS-001',
    'tests/models/windspeed/loader.py':                 'MKM-WS-001',
    'tests/models/windspeed/query.py':                  'MKM-WS-001',
    'tests/models/windspeed/timeseries.py':             'MKM-WS-001',

    # ---------------------------------------------------------------------------
    # MKM-WD-001  Wind Damage
    # ---------------------------------------------------------------------------
    'tests/models/winddamage/vulnerability.py':         'MKM-WD-001',
    'tests/models/winddamage/bri_shift.py':             'MKM-WD-001',
    'tests/models/winddamage/cdm.py':                   'MKM-WD-001',
    'tests/models/winddamage/threshold.py':             'MKM-WD-001',
    'tests/models/winddamage/extraction.py':            'MKM-WD-001',
    'tests/models/winddamage/event.py':                 'MKM-WD-001',
    'tests/catch/halong/test_tc.py':                    'MKM-TC-001',
}

MODEL_INFO = {
    'MKM-SI-001': {'name': 'Storm Intensity Distribution',      'dir': 'storm_intensity'},
    'MKM-SG-001': {'name': 'Storm-Gauge Response Model',        'dir': 'storm_gauge'},
    'MKM-GH-001': {'name': 'GEV Hazard Model',                  'dir': 'gev_hazard'},
    'MKM-PR-001': {'name': 'PRS Pricing Model',                 'dir': 'prs_pricing'},
    'MKM-DD-001': {'name': 'Flood Risk (Depth-Damage)',         'dir': 'flood_risk'},
    'MKM-SP-001': {'name': 'Spatial Interpolation',             'dir': 'spatial_model'},
    'MKM-PV-001': {'name': 'Property Valuation',                'dir': 'property_valuation'},
    'MKM-IP-001': {'name': 'Insurance Premium',                 'dir': 'insurance_premium'},
    'MKM-MP-001': {'name': 'Mortgage Pricer',                   'dir': 'mortgage_pricer'},
    'MKM-RA-001': {'name': 'Risk Analytics',                    'dir': 'risk_assessment'},
    'MKM-FC-001': {'name': 'Flood Probability Classifier',      'dir': 'flood_classifier'},
    'MKM-SS-001': {'name': 'Storm Sequence Generator',          'dir': 'storm_multi'},
    'MKM-GHD-001': {'name': 'GaugeHD Synthetic',                'dir': 'gaugehd_synthetic'},
    'MKM-ST-001': {'name': 'Stress Test Pipeline',              'dir': 'stressm_pipeline'},
    'MKM-PF-001': {'name': 'Property Flood Response',           'dir': 'property_flood_response'},
    'MKM-FPO-001': {'name': 'Flood Polynomial Model',            'dir': 'flood_poly'},
    'MKM-DE-001': {'name': 'Delta Engine',                      'dir': 'delta_engine'},
    'MKM-BRI-001': {'name': 'Building Resilience Index Model',  'dir': 'bri_resilience'},
    'MKM-BRF-001': {'name': 'BRI-Adjusted Floor Level Model',   'dir': 'bri_floor'},
    'MKM-TC-001': {'name': 'Tropical Cyclone Progression and Wind-Field', 'dir': 'typhoon'},
    'MKM-WS-001': {'name': 'Event Wind Lookup',                 'dir': None},
    'MKM-WD-001': {'name': 'Wind Damage',                       'dir': None},
    'MKM-TD-001': {'name': 'Trading Desk',                      'dir': None},
    'CDM-ALL':    {'name': 'CDM Schema Validation',             'dir': None},
    'E2E-ALL':    {'name': 'End-to-End Browser Tests',          'dir': None},
    'PLATFORM':   {'name': 'Platform Infrastructure',           'dir': None},
}

# Short alias -> full model ID for --model flag
MODEL_ALIASES = {
    'SI': 'MKM-SI-001', 'SG': 'MKM-SG-001', 'GH': 'MKM-GH-001',
    'PR': 'MKM-PR-001', 'DD': 'MKM-DD-001', 'SP': 'MKM-SP-001',
    'PV': 'MKM-PV-001', 'IP': 'MKM-IP-001', 'MP': 'MKM-MP-001',
    'RA': 'MKM-RA-001', 'FC': 'MKM-FC-001', 'SS': 'MKM-SS-001', 'TD': 'MKM-TD-001',
    'GHD': 'MKM-GHD-001', 'ST': 'MKM-ST-001', 'PF': 'MKM-PF-001',
    'DE': 'MKM-DE-001', 'FPO': 'MKM-FPO-001',
    'BRI': 'MKM-BRI-001',
    'BRF': 'MKM-BRF-001',
    'TC': 'MKM-TC-001',
    'WS': 'MKM-WS-001',
    'WD': 'MKM-WD-001',
    'E2E': 'E2E-ALL',
}
