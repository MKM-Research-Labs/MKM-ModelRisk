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


"""Parameter sections (_sections_a) for the model parameter inventory."""


def get_sections():
    return [
        # ──────────────────────────────────────────────
        # 1. PRS PRICING (Analytical)
        # ──────────────────────────────────────────────
        {
            'title': 'PRS Pricing --- Analytical Model',
            'model_id': 'MKM-PR-001',
            'source': 'models/hazard/prs_analytical.py',
            'subsections': [
                ('PRS Pricing Parameters', [
                    ('MIN_PRS_SPREAD_BPS', '2.0', 'Minimum PRS spread floor (bps)', 'hazard/prs_analytical.py'),
                ]),
                ('Spread Decomposition', [
                    ('method', 'data-driven', 'Uses synthetic HC variants (shd/she) instead of parametric basis', 'port/src/property/hc/generator.py'),
                    ('reference_tenor', '5yr', 'Decomposition uses 5yr any_flood spread', 'port/src/property/hc/generator.py'),
                ]),
                ('Recovery Rates by Trigger', [
                    ('any_flood (> 0m)', '0.85', 'Recovery rate for any flood trigger', 'hazard/prs_analytical.py:55-59'),
                    ('moderate (> 0.5m)', '0.70', 'Recovery rate for moderate flood', 'hazard/prs_analytical.py:55-59'),
                    ('severe (> 1.0m)', '0.50', 'Recovery rate for severe flood', 'hazard/prs_analytical.py:55-59'),
                ]),
                ('CDS Pricing', [
                    ('dt', '0.25', 'Quarterly period length (years)', 'hazard/prs_analytical.py:97'),
                    ('max_annual_hazard_rate', '0.999', 'Cap for continuous hazard rate', 'hazard/prs_analytical.py:95'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 2. PRS PRICING (QuantLib)
        # ──────────────────────────────────────────────
        {
            'title': 'PRS Pricing --- QuantLib CDS',
            'model_id': 'MKM-PR-001',
            'source': 'models/prshc.py',
            'subsections': [
                ('Default Trade Parameters', [
                    ('notional', '10,000,000', 'Default notional (GBP)', 'prshc.py:131'),
                    ('tenor_years', '5', 'Default swap tenor', 'prshc.py:132'),
                    ('running_spread', '0.01', 'Default running spread (100 bps)', 'prshc.py:133'),
                    ('recovery_rate', '0.0', 'Default recovery (no recovery for flood)', 'prshc.py:134'),
                    ('risk_free_rate', '0.03', 'Default risk-free rate (3\\%)', 'prshc.py:135'),
                    ('implied_hazard_rate fallback', '0.05', 'Fallback hazard rate (5\\%)', 'prshc.py:83'),
                ]),
                ('QuantLib Conventions', [
                    ('Schedule frequency', 'Quarterly', 'CDS payment frequency', 'prshc.py:194'),
                    ('Calendar', 'TARGET()', 'TARGET settlement calendar', 'prshc.py:182'),
                    ('Day counter', 'Actual/360', 'Accrual day count convention', 'prshc.py:184'),
                    ('Business day convention', 'Following', 'Roll convention', 'prshc.py:183'),
                    ('Date generation rule', 'TwentiethIMM', 'IMM date schedule', 'prshc.py:198'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 3. GEV HAZARD
        # ──────────────────────────────────────────────
        {
            'title': 'GEV Hazard Curve Model',
            'model_id': 'MKM-GH-001',
            'source': 'models/hazard/gev.py, models/hazard/builder.py',
            'subsections': [
                ('Hazard Curve Construction', [
                    ('STANDARD_THRESHOLDS', '[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]', 'Flood depth thresholds (m)', 'hazard/builder.py:24'),
                    ('RETURN_PERIODS', '[2, 5, 10, 20, 50, 100]', 'Standard return periods (years)', 'hazard/builder.py:25'),
                    ('exceedance_prob floor', '0.01', 'Floor at 1\\% (100-yr return period)', 'hazard/builder.py:69-70'),
                ]),
                ('Term Structure', [
                    ('max_years', '5', 'Maximum years for term structure', 'hazard/gev.py:48'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 4. STORM-GAUGE RESPONSE
        # ──────────────────────────────────────────────
        {
            'title': 'Storm-Gauge Response Model',
            'model_id': 'MKM-SG-001',
            'source': 'models/hazard/response_model.py, models/stormgauge/forward_model.py',
            'subsections': [
                ('Gauge Alert Thresholds (defaults)', [
                    ('flood_alert', '3.0', 'Flood alert level (m)', 'hazard/response_model.py:42'),
                    ('flood_warning', '4.0', 'Flood warning level (m)', 'hazard/response_model.py:43'),
                    ('severe_flood_warning', '5.0', 'Severe warning level (m)', 'hazard/response_model.py:44'),
                ]),
                ('Response Calibration', [
                    ('base_response', 'level_range * 0.015', 'Base gauge response coefficient', 'hazard/response_model.py:59'),
                    ('response_coef variation', 'U(0.8, 1.2)', 'Uniform multiplier on response', 'hazard/response_model.py:60'),
                    ('precip_factor divisor', '35.0', 'Precipitation normalisation (mm)', 'hazard/response_model.py:78'),
                    ('duration_factor cap', '2.0', 'Maximum duration amplification', 'hazard/response_model.py:79'),
                    ('noise factor', 'U(0.85, 1.15)', 'Random noise multiplier', 'hazard/response_model.py:89'),
                ]),
                ('Forward Model --- Spatial Decay', [
                    ('intensity_to_level_scale', '0.1', 'Intensity-to-level conversion scale', 'stormgauge/forward_model.py:42'),
                    ('time_resolution_hours', '0.5', 'Temporal resolution (hours)', 'stormgauge/forward_model.py:43'),
                    ('response_lag_hours', '2.0', 'Lag before gauge response', 'stormgauge/forward_model.py:44'),
                    ('response_decay_hours', '12.0', 'Exponential decay time', 'stormgauge/forward_model.py:45'),
                    ('gamma (intensity mapping)', '0.8', 'Non-linear intensity exponent', 'stormgauge/forward_model.py:195'),
                    ('rise limb multiplier', '3.0', 'Faster rising limb vs decay', 'stormgauge/forward_model.py:244'),
                    ('Earth radius', '6,371 km', 'Haversine distance calculation', 'stormgauge/forward_model.py:54'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 5. STORM INTENSITY
        # ──────────────────────────────────────────────
        {
            'title': 'Storm Intensity Distribution',
            'model_id': 'MKM-SI-001',
            'source': 'models/intensity/distribution.py, models/intensity/parameters.py',
            'subsections': [
                ('Distribution Defaults', [
                    ('base_mean', '45.0', 'Mean storm intensity', 'intensity/distribution.py:33'),
                    ('base_std', '15.0', 'Standard deviation', 'intensity/distribution.py:34'),
                    ('tail_threshold', '60.0', 'Pareto tail crossover point', 'intensity/distribution.py:35'),
                    ('tail_index', '2.5', 'Pareto tail index (heavier = lower)', 'intensity/distribution.py:36'),
                    ('min_intensity', '10.0', 'Minimum storm intensity', 'intensity/distribution.py:37'),
                    ('max_intensity', '100.0', 'Maximum storm intensity', 'intensity/distribution.py:38'),
                ]),
                ('Scenario Families', [
                    ('historical', 'mean=40, std=12, thresh=60, idx=3.0', 'Historical baseline scenario', 'intensity/parameters.py:43-50'),
                    ('baseline', 'mean=45, std=15, thresh=60, idx=2.5', 'Current climate scenario', 'intensity/parameters.py:51-58'),
                    ('moderate_stress', 'mean=50, std=15, thresh=55, idx=2.0', 'Moderate climate stress', 'intensity/parameters.py:59-66'),
                    ('severe_stress', 'mean=55, std=18, thresh=50, idx=1.5', 'Severe climate stress', 'intensity/parameters.py:67-74'),
                    ('extreme', 'mean=60, std=20, thresh=45, idx=1.2', 'Extreme tail scenario', 'intensity/parameters.py:75-79'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 6. FLOOD RISK (Depth-Damage + Velocity)
        # ──────────────────────────────────────────────
        {
            'title': 'Flood Risk --- Depth-Damage and Velocity',
            'model_id': 'MKM-DD-001',
            'source': 'models/floodrisk/depth_damage.py, models/floodrisk/velocity.py',
            'subsections': [
                ('UK Depth-Damage Curve', [
                    ('DEPTH_POINTS', '[0, 0.05, 0.5, 1, 1.5, 2, 3, 4, 5, 6]', 'Flood depth breakpoints (m)', 'floodrisk/depth_damage.py:80'),
                    ('DAMAGE_POINTS', '[0, 0.05, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.95, 1.0]', 'Damage fraction at each depth', 'floodrisk/depth_damage.py:81'),
                    ('max flood depth', '5.0', 'Maximum modelled depth (m)', 'floodrisk/depth_damage.py:74'),
                    ('max distance', '25,000', 'Maximum distance for damage (m)', 'floodrisk/depth_damage.py:67'),
                ]),
                ('Property Type Factors', [
                    ('residential', '1.0', 'Base case damage factor', 'floodrisk/depth_damage.py:130-134'),
                    ('commercial', '1.2', 'Higher damage for commercial', 'floodrisk/depth_damage.py:130-134'),
                    ('industrial', '0.9', 'Lower damage for industrial', 'floodrisk/depth_damage.py:130-134'),
                ]),
                ('Manning Velocity Model', [
                    ('DEFAULT_ROUGHNESS', '0.04', 'Manning n for urban floodplain', 'floodrisk/velocity.py:15'),
                    ('MIN_SLOPE', '0.001', 'Minimum slope clamp', 'floodrisk/velocity.py:21'),
                    ('DEFAULT_RETENTION_LENGTH', '3,000', 'Exponential retention e-folding length (m)', 'floodrisk/velocity.py:18'),
                    ('DEFAULT_RECESSION_FACTOR', '1.5', 'Recession limb multiplier', 'floodrisk/velocity.py:24'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 7. SPATIAL INTERPOLATION
        # ──────────────────────────────────────────────
        {
            'title': 'Spatial Interpolation',
            'model_id': 'MKM-SP-001',
            'source': 'models/floodrisk/spatial.py',
            'subsections': [
                ('Spatial Parameters', [
                    ('Earth radius', '6,371,000', 'Haversine radius (m)', 'floodrisk/spatial.py:53'),
                    ('IDW power (deprecated v2.1)', '2.0', 'Legacy IDW exponent (no longer used in flood pipeline)', 'floodrisk/spatial.py:114'),
                    ('IDW min_distance (deprecated v2.1)', '1.0', 'Legacy IDW distance floor (m)', 'floodrisk/spatial.py:115'),
                    ('Near-field threshold', '2,000', 'Retention = 1.0 below this distance (m)', 'models/floodrisk/velocity.py'),
                    ('Retention length scale', '10,000', 'Exponential decay length (m), beyond near-field', 'models/floodrisk/velocity.py'),
                    ('Synthetic dedup distance', '50', 'Properties sharing a synthetic gauge (m)', 'port/src/gauge/synthetic.py'),
                    ('distance_km to degrees', '111.0', 'km per degree latitude', 'floodrisk/spatial.py:40'),
                ]),
            ],
        },
    ]
