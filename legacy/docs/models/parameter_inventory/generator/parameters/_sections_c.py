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


"""Parameter sections (_sections_c) for the model parameter inventory."""


def get_sections():
    return [
        # ──────────────────────────────────────────────
        # 13. TIMESERIES STATISTICS
        # ──────────────────────────────────────────────
        {
            'title': 'Timeseries Statistics',
            'model_id': 'MKM-TS-001',
            'source': 'models/statistics/timeseries.py, models/statistics/synthetic.py',
            'subsections': [
                ('Statistical Parameters', [
                    ('days_per_year', '365.25', 'Year length for annual maxima', 'statistics/timeseries.py:48'),
                    ('percentile_bands', '[5, 10, 25, 50, 75, 90, 95, 99]', 'Standard percentile breakpoints', 'statistics/timeseries.py:69-77'),
                ]),
                ('Synthetic Water Level Generation', [
                    ('base_level range', 'U(0.3, 0.5) * flood_alert', 'Normal water level', 'statistics/synthetic.py:62'),
                    ('daily_std', 'base_level * 0.15', 'Daily standard deviation', 'statistics/synthetic.py:63'),
                    ('seasonal_amplitude', 'base_level * 0.25', 'Winter/summer variation', 'statistics/synthetic.py:64'),
                    ('seasonal_peak', 'Day 15 (January)', 'Winter peak offset', 'statistics/synthetic.py:98'),
                    ('minor_flood_prob', '5.0x severe_prob', 'Minor flood frequency', 'statistics/synthetic.py:83'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 14. FLOOD PROBABILITY CLASSIFIER
        # ──────────────────────────────────────────────
        {
            'title': 'Flood Probability Classifier (GBM)',
            'model_id': 'MKM-FC-001',
            'source': 'models/stress/flood_classifier.py',
            'subsections': [
                ('GBM Hyperparameters', [
                    ('n_estimators', '200', 'Number of boosting rounds', 'stress/flood_classifier.py:76'),
                    ('max_depth', '4', 'Maximum tree depth', 'stress/flood_classifier.py:77'),
                    ('learning_rate', '0.1', 'Shrinkage per round', 'stress/flood_classifier.py:78'),
                    ('subsample', '0.8', 'Row sampling fraction', 'stress/flood_classifier.py:79'),
                    ('min_samples_leaf', '20', 'Minimum leaf node samples', 'stress/flood_classifier.py:80'),
                    ('random_state', '42', 'Random seed for reproducibility', 'stress/flood_classifier.py:81'),
                ]),
                ('Training Configuration', [
                    ('test_size', '0.2', 'Hold-out test fraction (stratified)', 'stress/flood_classifier.py:73'),
                    ('features', '[water_level, hour, delta_w, delta2_w]', 'Four-dimensional feature space (v1.2)', 'stress/flood_classifier.py:55'),
                    ('target', 'flood_flag', 'Binary: 1 if storm breaches alert level', 'stress/flood_classifier.py:56'),
                    ('delta_w', 'w(t) - w(t-1)', 'Velocity: hourly water level change', 'port/src/stress.py'),
                    ('delta2_w', 'dw(t) - dw(t-1)', 'Acceleration: hourly velocity change', 'port/src/stress.py'),
                ]),
                ('Training Noise (upstream)', [
                    ('noise_sigma_start', '0.5 m', 'Gaussian noise std at hour 0', 'port/src/stress.py'),
                    ('noise_sigma_end', '0.1 m', 'Gaussian noise std at hour 167', 'port/src/stress.py'),
                    ('noise_decay', 'Exponential', 'Time-decaying noise envelope', 'port/src/stress.py'),
                    ('num_hours', '168', 'Storm horizon (7 days)', 'port/src/stress.py'),
                ]),
            ],
        },

        # -----------------------------------------------------------------------
        # MKM-SS-001  Storm Sequence Generator
        # -----------------------------------------------------------------------
        {
            'section': 'Storm Sequence Generator (MKM-SS-001)',
            'model_id': 'MKM-SS-001',
            'source': 'port/src/storm_multi/',
            'subsections': [
                ('Event Window', [
                    ('EVENT_WINDOW_HOURS', '168', 'Insurance hours clause event window', 'storm_multi/utils/validation.py'),
                    ('MIN_DRAINAGE_WINDOW_HOURS', '12', 'Minimum post-precipitation drainage window', 'storm_multi/utils/validation.py'),
                    ('MAX_PRECIP_END_HOUR', '156', 'Latest hour at which precipitation may end (168-12)', 'storm_multi/utils/validation.py'),
                ]),
                ('Sequence Type Probabilities', [
                    ('P(sequence|minimal)', '0.05', 'Probability of multi-storm sequence for minimal category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|baseline)', '0.15', 'Probability of multi-storm sequence for baseline category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|moderate)', '0.30', 'Probability of multi-storm sequence for moderate category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|severe)', '0.50', 'Probability of multi-storm sequence for severe category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|extreme)', '0.70', 'Probability of multi-storm sequence for extreme category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|catastrophic)', '0.85', 'Probability of multi-storm sequence for catastrophic category', 'storm_multi/generators/intensity_sampler.py'),
                ]),
                ('Storm Duration Parameters (min, mode, max hours)', [
                    ('minimal', '(2, 6, 12)', 'Triangular duration range for minimal category', 'storm_multi/generators/duration_sampler.py'),
                    ('baseline', '(6, 12, 24)', 'Triangular duration range for baseline category', 'storm_multi/generators/duration_sampler.py'),
                    ('moderate', '(12, 30, 60)', 'Triangular duration range for moderate category', 'storm_multi/generators/duration_sampler.py'),
                    ('severe', '(24, 48, 96)', 'Triangular duration range for severe category', 'storm_multi/generators/duration_sampler.py'),
                    ('extreme', '(36, 72, 144)', 'Triangular duration range for extreme category', 'storm_multi/generators/duration_sampler.py'),
                    ('catastrophic', '(48, 120, 240)', 'Triangular duration range for catastrophic category', 'storm_multi/generators/duration_sampler.py'),
                ]),
                ('Inter-Storm Gap Parameters (min, mode, max hours)', [
                    ('SHORT (persistent)', '(6, 18, 36)', 'Minimal drainage gap for persistent sequences', 'storm_multi/generators/gap_sampler.py'),
                    ('MEDIUM (doublet, cluster)', '(24, 48, 72)', 'Partial drainage gap for doublet/cluster sequences', 'storm_multi/generators/gap_sampler.py'),
                ]),
                ('Intensity Sampling', [
                    ('base_intensity_moderate', 'N(1.0, 0.20)', 'Normal base intensity for moderate category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('base_intensity_severe', 'N(1.8, 0.30)', 'Normal base intensity for severe category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('base_intensity_extreme', 'N(3.0, 0.50)', 'Normal base intensity for extreme category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('base_intensity_catastrophic', 'N(5.0, 0.80)', 'Normal base intensity for catastrophic category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('INTENSITY_VARIATION', '±0.20', 'Per-storm intensity variation around base (±20%)', 'storm_multi/generators/intensity_sampler.py'),
                    ('CORRELATION_PROB', '0.70', 'Probability subsequent storm ≥ first storm intensity', 'storm_multi/generators/intensity_sampler.py'),
                    ('peak_position_alpha', '2.0', 'Beta distribution shape α for peak position', 'storm_multi/generators/sequence_generator.py'),
                    ('peak_position_beta', '2.0', 'Beta distribution shape β for peak position', 'storm_multi/generators/sequence_generator.py'),
                ]),
                ('Batch Generation Defaults', [
                    ('default_count', '10000', 'Default number of sequences per batch', 'storm_multi/generators/batch_generator.py'),
                    ('weight_moderate', '0.40', 'Default intensity weight for moderate category', 'storm_multi/generators/batch_generator.py'),
                    ('weight_severe', '0.35', 'Default intensity weight for severe category', 'storm_multi/generators/batch_generator.py'),
                    ('weight_extreme', '0.20', 'Default intensity weight for extreme category', 'storm_multi/generators/batch_generator.py'),
                    ('weight_catastrophic', '0.05', 'Default intensity weight for catastrophic category', 'storm_multi/generators/batch_generator.py'),
                    ('catchment_base_precip_thames', '35.0 mm', 'Thames catchment base precipitation', 'storm_multi/generators/sequence_generator.py'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # MKM-BRI-001: BUILDING RESILIENCE INDEX MODEL
        # ──────────────────────────────────────────────
        {
            'title': 'Building Resilience Index Model',
            'model_id': 'MKM-BRI-001',
            'source': 'port/rand/thames/property/property_random/resilience.py',
            'subsections': [
                ('Section Weights (BRI letter rating, sum to 1.0)', [
                    ('FloodProtection',    '0.30', 'Top-weighted under Thames fluvial dominance', 'resilience.py:SECTION_WEIGHTS'),
                    ('SiteAndDrainage',    '0.25', 'Passive flood resilience + drainage',          'resilience.py:SECTION_WEIGHTS'),
                    ('BuildingAssessment', '0.20', 'Structural/envelope checks',                   'resilience.py:SECTION_WEIGHTS'),
                    ('ContinuityMeasures', '0.15', 'Drives the "+" continuity modifier',          'resilience.py:SECTION_WEIGHTS'),
                    ('FireProtection',     '0.10', 'Lowest BRI-relevance for Thames',              'resilience.py:SECTION_WEIGHTS'),
                ]),
                ('Compliance Level Credits (5-level enum)', [
                    ('Not assessed',  '0.00', 'Measure not evaluated',     'resilience.py:RESILIENCE\\_LEVEL\\_CREDIT'),
                    ('Partial',       '0.40', 'Present but below minimum', 'resilience.py:RESILIENCE\\_LEVEL\\_CREDIT'),
                    ('Meets minimum', '0.70', 'At minimum requirement',    'resilience.py:RESILIENCE\\_LEVEL\\_CREDIT'),
                    ('Enhanced',      '0.90', 'Exceeds minimum',           'resilience.py:RESILIENCE\\_LEVEL\\_CREDIT'),
                    ('Verified',      '1.00', 'Independently verified',    'resilience.py:RESILIENCE\\_LEVEL\\_CREDIT'),
                ]),
                ('Rating Thresholds (score on 0-1 scale)', [
                    ('AA',                       '0.87', 'Top-tier resilience threshold',          'resilience.py:RATING\\_THRESHOLDS'),
                    ('A',                        '0.62', 'Strong resilience',                       'resilience.py:RATING\\_THRESHOLDS'),
                    ('B',                        '0.38', 'Moderate resilience',                     'resilience.py:RATING\\_THRESHOLDS'),
                    ('CONTINUITY\\_PLUS\\_THRESHOLD', '0.65', 'Continuity score needed for "+" modifier', 'resilience.py:CONTINUITY\\_PLUS\\_THRESHOLD'),
                ]),
                ('Flood-Spec Base Weights (sum to 100)', [
                    ('lowest\\_occupied\\_floor\\_elevation',       '20', 'Highest-impact control on water reaching occupied space', 'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('critical\\_systems\\_elevation',              '15', 'Strong effect on severe loss and downtime',               'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('site\\_drainage\\_topography',                '10', 'Site grading; stronger in pluvial regimes',               'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('onsite\\_retainage\\_capacity',               '10', 'Onsite stormwater retention',                              'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('lower\\_level\\_flood\\_compatible\\_design', '8',  'Limits damage when lower level floods',                    'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('water\\_resistant\\_materials',               '8',  'Repair severity after inundation (proxy)',                'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('permeable\\_surface\\_share',                 '6',  'Reduces runoff generation',                                'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('backflow\\_protection',                       '6',  'Backflow on vulnerable lines',                             'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('debris\\_impact\\_resistance',                '5',  'Envelope debris resistance (proxy)',                       'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('roof\\_drainage\\_standard',                  '4',  'Roof drainage maintenance (proxy)',                        'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('roof\\_membrane\\_openings\\_seal',           '3',  'Membrane/seal water-tightness (proxy)',                    'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('sump\\_pumps\\_backup\\_power',               '3',  'Sump + backup; min of two CDM fields',                     'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                    ('historic\\_water\\_area\\_flag',              '2',  'Adverse history; from FloodDamageSeverity',                'resilience.py:FLOOD\\_SPEC\\_BASE\\_WEIGHTS'),
                ]),
                ('Damage Modifier alpha by Regime', [
                    ('alpha\\_pluvial', '0.65', 'Higher mitigation leverage in pluvial flooding',     'resilience.py:FLOOD\\_SPEC\\_ALPHA\\_BY\\_REGIME'),
                    ('alpha\\_fluvial', '0.60', 'Default fluvial regime',                              'resilience.py:FLOOD\\_SPEC\\_ALPHA\\_BY\\_REGIME'),
                    ('alpha\\_coastal', '0.50', 'Lower leverage; residual loss high in deep inundation', 'resilience.py:FLOOD\\_SPEC\\_ALPHA\\_BY\\_REGIME'),
                ]),
                ('Soft Caps', [
                    ('LOF compliance = 0',                          '40', 'Cap when lowest occupied floor is at risk',           'resilience.py:FLOOD\\_SPEC\\_SOFT\\_CAPS'),
                    ('Critical systems compliance = 0',             '60', 'Cap when critical systems below flood level',          'resilience.py:FLOOD\\_SPEC\\_SOFT\\_CAPS'),
                    ('Pluvial retainage + drainage = 0',            '55', 'Cap for pluvial regime without site controls',         'resilience.py:FLOOD\\_SPEC\\_SOFT\\_CAPS'),
                    ('Fluvial/coastal lower-level + materials = 0', '65', 'Cap for inundation regime without lower-level controls', 'resilience.py:FLOOD\\_SPEC\\_SOFT\\_CAPS'),
                ]),
                ('Elevation-Margin Compliance Bands', [
                    ('Less than 0 m',         '0.00', 'Below local water reference', 'resilience.py:LOWEST\\_FLOOR\\_ELEVATION\\_BANDS'),
                    ('0 to less than 1 m',    '0.20', 'Marginal',                     'resilience.py:LOWEST\\_FLOOR\\_ELEVATION\\_BANDS'),
                    ('1 to less than 3 m',    '0.50', 'Adequate',                     'resilience.py:LOWEST\\_FLOOR\\_ELEVATION\\_BANDS'),
                    ('3 to less than 5 m',    '0.75', 'Strong',                       'resilience.py:LOWEST\\_FLOOR\\_ELEVATION\\_BANDS'),
                    ('5 to less than 6 m',    '0.90', 'Very strong',                  'resilience.py:LOWEST\\_FLOOR\\_ELEVATION\\_BANDS'),
                    ('6 m or more',           '1.00', 'Full credit',                   'resilience.py:LOWEST\\_FLOOR\\_ELEVATION\\_BANDS'),
                ]),
            ],
        },

        # ──────────────────────────────────────────────
        # MKM-BRF-001: BRI-ADJUSTED FLOOR LEVEL MODEL
        # ──────────────────────────────────────────────
        {
            'title': 'BRI-Adjusted Floor Level Model',
            'model_id': 'MKM-BRF-001',
            'source': 'models/floodrisk/depth_damage.py',
            'subsections': [
                ('Floor-Uplift Ramp (additive, continuous in BRIFloodScore)', [
                    ('BRI\\_FLOOR\\_UPLIFT\\_MAX\\_M',      '3.00', 'Maximum floor-level uplift (m) at/above the AA anchor score',     'damage.py:BRI\\_FLOOR\\_UPLIFT\\_MAX\\_M'),
                    ('BRI\\_FLOOR\\_UPLIFT\\_SCORE\\_LO',   '0.38', 'Score at/below which no uplift is awarded (NR / B boundary)',     'damage.py:BRI\\_FLOOR\\_UPLIFT\\_SCORE\\_LO'),
                    ('BRI\\_FLOOR\\_UPLIFT\\_SCORE\\_HI',   '0.87', 'Score at/above which the full uplift is awarded (AA anchor)',     'damage.py:BRI\\_FLOOR\\_UPLIFT\\_SCORE\\_HI'),
                ]),
                ('Letter-Grade Fallback Scores (band mid-points)', [
                    ('AA', '0.935', 'Mid-point of [0.87, 1.00]; used when no numeric flood score', 'damage.py:BRI\\_FLOOR\\_RATING\\_SCORES'),
                    ('A',  '0.745', 'Mid-point of [0.62, 0.87]',                                    'damage.py:BRI\\_FLOOR\\_RATING\\_SCORES'),
                    ('B',  '0.500', 'Mid-point of [0.38, 0.62]',                                    'damage.py:BRI\\_FLOOR\\_RATING\\_SCORES'),
                    ('NR', '0.190', 'Mid-point of [0.00, 0.38]',                                    'damage.py:BRI\\_FLOOR\\_RATING\\_SCORES'),
                ]),
                ('Effective-Floor Formula', [
                    ('adjusted\\_floor', 'FloorLevelMeters + uplift(s)', 'Effective flood threshold; floods iff attenuated WSE > GroundLevelMeters + adjusted\\_floor', 'depth\\_damage.py:bri\\_adjusted\\_floor\\_level'),
                    ('uplift(s)',        'linear on [LO, HI]',           'uplift = 0 for s<=LO, = MAX\\_M for s>=HI, linear between; always >= 0',                      'depth\\_damage.py:bri\\_floor\\_uplift'),
                ]),
            ],
        },
    ]
