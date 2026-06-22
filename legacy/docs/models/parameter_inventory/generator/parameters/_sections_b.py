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


"""Parameter sections (_sections_b) for the model parameter inventory."""


def get_sections():
    return [
        # ──────────────────────────────────────────────
        # 8. RISK ANALYTICS
        # ──────────────────────────────────────────────
        {
            'title': 'Risk Analytics',
            'model_id': 'MKM-RA-001',
            'source': 'models/floodrisk/risk_analytics.py',
            'subsections': [
                ('Monte Carlo Settings', [
                    ('n_simulations', '1,000', 'Default simulation count', 'floodrisk/risk_analytics.py:22'),
                    ('shock_multiplier', '0.2', 'Stress shock (20\\%)', 'floodrisk/risk_analytics.py:54'),
                    ('random_seed', '42', 'Reproducibility seed', 'floodrisk/risk_analytics.py:38'),
                    ('grid_size', '1,000', 'Spatial grid cell size (m)', 'floodrisk/risk_analytics.py:78'),
                ]),
                ('Risk Classification Thresholds', [
                    ('high_risk', '> 0.6', 'Damage ratio for high risk', 'floodrisk/risk_analytics.py:157'),
                    ('medium_risk', '0.3--0.6', 'Damage ratio for medium risk', 'floodrisk/risk_analytics.py:158'),
                    ('low_risk', '0.1--0.3', 'Damage ratio for low risk', 'floodrisk/risk_analytics.py:159'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 9. RISK ASSESSMENT
        # ──────────────────────────────────────────────
        {
            'title': 'Risk Assessment Model',
            'model_id': 'MKM-RA-001',
            'source': 'models/risk/risk_assessor.py',
            'subsections': [
                ('Flood Depth Thresholds', [
                    ('very_low', '0.0 m', 'No flood exposure', 'risk/risk_assessor.py:23-29'),
                    ('low', '0.1 m', 'Minor flooding', 'risk/risk_assessor.py:23-29'),
                    ('medium', '0.5 m', 'Moderate flooding', 'risk/risk_assessor.py:23-29'),
                    ('high', '1.0 m', 'Significant flooding', 'risk/risk_assessor.py:23-29'),
                    ('very_high', '2.0 m', 'Severe flooding', 'risk/risk_assessor.py:23-29'),
                ]),
                ('LTV Risk Thresholds', [
                    ('low', '0.6', 'Low LTV boundary', 'risk/risk_assessor.py:31-36'),
                    ('moderate', '0.8', 'Moderate LTV boundary', 'risk/risk_assessor.py:31-36'),
                    ('high', '0.95', 'High LTV boundary', 'risk/risk_assessor.py:31-36'),
                    ('critical', '1.0', 'Negative equity threshold', 'risk/risk_assessor.py:31-36'),
                ]),
                ('Flood Risk Scores', [
                    ('Very Low', '1', 'Base risk score', 'risk/risk_assessor.py:154-161'),
                    ('Low', '2', '', 'risk/risk_assessor.py:154-161'),
                    ('Medium', '4', '', 'risk/risk_assessor.py:154-161'),
                    ('High', '7', '', 'risk/risk_assessor.py:154-161'),
                    ('Very High', '9', '', 'risk/risk_assessor.py:154-161'),
                    ('Unknown', '3', 'Default when unknown', 'risk/risk_assessor.py:154-161'),
                ]),
                ('LTV Multipliers', [
                    ('> 0.95', '2.0x', 'Near negative equity', 'risk/risk_assessor.py:171-176'),
                    ('> 0.8', '1.5x', 'High LTV', 'risk/risk_assessor.py:171-176'),
                    ('> 0.6', '1.2x', 'Moderate LTV', 'risk/risk_assessor.py:171-176'),
                    ('else', '1.0x', 'Low LTV (base)', 'risk/risk_assessor.py:171-176'),
                ]),
                ('Construction Type Factors', [
                    ('timber / wood', '1.3', 'Highest vulnerability', 'risk/risk_assessor.py:189-197'),
                    ('brick', '1.0', 'Standard', 'risk/risk_assessor.py:189-197'),
                    ('concrete', '0.9', 'More resilient', 'risk/risk_assessor.py:189-197'),
                    ('steel', '0.8', 'Most resilient', 'risk/risk_assessor.py:189-197'),
                ]),
                ('Age Factors', [
                    ('> 100 years', '1.3', 'Heritage property risk', 'risk/risk_assessor.py:181-184'),
                    ('> 50 years', '1.1', 'Older property risk', 'risk/risk_assessor.py:181-184'),
                ]),
                ('Insurance Premium Base Rates', [
                    ('Very Low', '0.001', '0.1\\% of property value', 'risk/risk_assessor.py:391-398'),
                    ('Low', '0.002', '0.2\\%', 'risk/risk_assessor.py:391-398'),
                    ('Medium', '0.005', '0.5\\%', 'risk/risk_assessor.py:391-398'),
                    ('High', '0.015', '1.5\\%', 'risk/risk_assessor.py:391-398'),
                    ('Very High', '0.035', '3.5\\%', 'risk/risk_assessor.py:391-398'),
                    ('Premium cap', '0.10', 'Max 10\\% of property value', 'risk/risk_assessor.py:406'),
                ]),
                ('Distance Risk Factors', [
                    ('<= 0.1 km', '1.0', 'Immediate proximity', 'risk/risk_assessor.py:361-372'),
                    ('<= 0.5 km', '0.8', '', 'risk/risk_assessor.py:361-372'),
                    ('<= 1.0 km', '0.6', '', 'risk/risk_assessor.py:361-372'),
                    ('<= 2.0 km', '0.4', '', 'risk/risk_assessor.py:361-372'),
                    ('<= 5.0 km', '0.2', '', 'risk/risk_assessor.py:361-372'),
                    ('> 5.0 km', '0.1', 'Minimal proximity risk', 'risk/risk_assessor.py:361-372'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 10. PROPERTY VALUATION
        # ──────────────────────────────────────────────
        {
            'title': 'Property Valuation Model',
            'model_id': 'MKM-PV-001',
            'source': 'models/valuation/property_value.py',
            'subsections': [
                ('Floor Area Ranges (sq m)', [
                    ('Flat', '35--120', 'Typical flat range', 'valuation/property_value.py:19-26'),
                    ('Mid-terrace', '60--180', '', 'valuation/property_value.py:19-26'),
                    ('End-terrace', '70--200', '', 'valuation/property_value.py:19-26'),
                    ('Semi-detached', '80--250', '', 'valuation/property_value.py:19-26'),
                    ('Detached', '120--400', '', 'valuation/property_value.py:19-26'),
                    ('Bungalow', '80--200', '', 'valuation/property_value.py:19-26'),
                ]),
                ('Base Price per sqm (GBP)', [
                    ('Detached', '8,000--15,000', 'London market calibration', 'valuation/property_value.py:29-36'),
                    ('Semi-detached', '6,500--12,000', '', 'valuation/property_value.py:29-36'),
                    ('Mid-terrace', '6,000--11,000', '', 'valuation/property_value.py:29-36'),
                    ('End-terrace', '6,200--11,500', '', 'valuation/property_value.py:29-36'),
                    ('Bungalow', '7,000--13,000', '', 'valuation/property_value.py:29-36'),
                    ('Flat', '5,500--10,000', '', 'valuation/property_value.py:29-36'),
                ]),
                ('Age Band Factors (multiplier range)', [
                    ('New build (< 10y)', '1.05--1.15', 'Premium for new', 'valuation/property_value.py:39-45'),
                    ('Modern (10--24y)', '0.95--1.05', 'Near base', 'valuation/property_value.py:39-45'),
                    ('Established (25--49y)', '0.90--1.00', 'Minor discount', 'valuation/property_value.py:39-45'),
                    ('Period (50--99y)', '0.85--0.95', '', 'valuation/property_value.py:39-45'),
                    ('Heritage (100+y)', '0.80--1.20', 'Wide range (character premium)', 'valuation/property_value.py:39-45'),
                ]),
                ('Condition Factors', [
                    ('Excellent', '1.10--1.20', '', 'valuation/property_value.py:48-54'),
                    ('Good', '1.00--1.10', '', 'valuation/property_value.py:48-54'),
                    ('Fair', '0.90--1.00', '', 'valuation/property_value.py:48-54'),
                    ('Poor', '0.70--0.90', '', 'valuation/property_value.py:48-54'),
                    ('Very poor', '0.50--0.70', '', 'valuation/property_value.py:48-54'),
                ]),
                ('Flood Risk Factors', [
                    ('Very Low', '1.00--1.02', 'Near neutral impact', 'valuation/property_value.py:57-63'),
                    ('Low', '0.98--1.00', '', 'valuation/property_value.py:57-63'),
                    ('Medium', '0.92--0.98', '', 'valuation/property_value.py:57-63'),
                    ('High', '0.85--0.92', '', 'valuation/property_value.py:57-63'),
                    ('Very High', '0.75--0.85', 'Significant discount', 'valuation/property_value.py:57-63'),
                ]),
                ('EPC Rating Factors', [
                    ('A', '1.05--1.10', 'Green premium', 'valuation/property_value.py:66-74'),
                    ('B', '1.02--1.05', '', 'valuation/property_value.py:66-74'),
                    ('C', '1.00--1.02', '', 'valuation/property_value.py:66-74'),
                    ('D', '0.98--1.00', '', 'valuation/property_value.py:66-74'),
                    ('E', '0.95--0.98', '', 'valuation/property_value.py:66-74'),
                    ('F', '0.90--0.95', '', 'valuation/property_value.py:66-74'),
                    ('G', '0.85--0.90', 'Energy penalty', 'valuation/property_value.py:66-74'),
                ]),
                ('Valuation Bounds', [
                    ('MIN_PROPERTY_VALUE', '150,000', 'Floor (GBP)', 'valuation/property_value.py:105'),
                    ('MAX_PROPERTY_VALUE', '5,000,000', 'Cap (GBP)', 'valuation/property_value.py:106'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 11. INSURANCE PREMIUM
        # ──────────────────────────────────────────────
        {
            'title': 'Insurance Premium Model',
            'model_id': 'MKM-IP-001',
            'source': 'models/valuation/insurance.py',
            'subsections': [
                ('Property Type Premium Factors', [
                    ('Flat', '0.80--1.00', 'Lower exposure', 'valuation/insurance.py:20-27'),
                    ('Mid-terrace', '0.90--1.10', '', 'valuation/insurance.py:20-27'),
                    ('End-terrace', '1.00--1.20', '', 'valuation/insurance.py:20-27'),
                    ('Semi-detached', '1.10--1.30', '', 'valuation/insurance.py:20-27'),
                    ('Detached', '1.20--1.50', 'Highest exposure', 'valuation/insurance.py:20-27'),
                    ('Bungalow', '1.00--1.20', 'Ground-floor risk', 'valuation/insurance.py:20-27'),
                ]),
                ('Flood Risk Premium Factors', [
                    ('Very Low', '0.90--1.00', '', 'valuation/insurance.py:30-36'),
                    ('Low', '1.00--1.20', '', 'valuation/insurance.py:30-36'),
                    ('Medium', '1.30--1.80', '', 'valuation/insurance.py:30-36'),
                    ('High', '1.80--2.50', '', 'valuation/insurance.py:30-36'),
                    ('Very High', '2.50--4.00', 'Significant loading', 'valuation/insurance.py:30-36'),
                ]),
                ('Premium Bounds', [
                    ('BASE_RATE_RANGE', '1.5--4.0', 'Per GBP 1,000 insured', 'valuation/insurance.py:64'),
                    ('MIN_PREMIUM', '200', 'Floor (GBP)', 'valuation/insurance.py:67'),
                    ('MAX_PREMIUM', '20,000', 'Cap (GBP)', 'valuation/insurance.py:68'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 12. MORTGAGE PRICER
        # ──────────────────────────────────────────────
        {
            'title': 'Mortgage Pricer',
            'model_id': 'MKM-MP-001',
            'source': 'models/mortgage_pricer.py',
            'subsections': [
                ('Credit Spread Schedule', [
                    ('Affordability ratio points', '[0.1, 0.2, ..., 1.0]', '10 interpolation points', 'mortgage_pricer.py:55'),
                    ('Credit spreads', '[50, 100, 200, 300, 500, 800, 1200, 1800, 2500, 3500] bps', 'Corresponding spread curve', 'mortgage_pricer.py:58'),
                    ('Default for zero income', '0.15', '15\\% spread fallback', 'mortgage_pricer.py:141'),
                    ('Minimum spread', '0.001', '10 bps floor', 'mortgage_pricer.py:175'),
                ]),
                ('Flood Risk Multipliers', [
                    ('Very Low', '1.00', 'No adjustment', 'mortgage_pricer.py:178-184'),
                    ('Low', '1.05', '', 'mortgage_pricer.py:178-184'),
                    ('Medium', '1.20', '', 'mortgage_pricer.py:178-184'),
                    ('High', '1.40', '', 'mortgage_pricer.py:178-184'),
                    ('Very High', '1.75', 'Largest loading', 'mortgage_pricer.py:178-184'),
                ]),
                ('LTV Impact Thresholds', [
                    ('> 0.95', '1.5x', 'Near negative equity', 'mortgage_pricer.py:389-396'),
                    ('> 0.9', '1.3x', '', 'mortgage_pricer.py:389-396'),
                    ('> 0.8', '1.1x', '', 'mortgage_pricer.py:389-396'),
                    ('else', '1.0x', 'Low LTV (base)', 'mortgage_pricer.py:389-396'),
                ]),
                ('Default Assumptions', [
                    ('tax_rate', '0.20', 'Corporation tax (20\\%)', 'mortgage_pricer.py:37'),
                    ('gross_annual_income (batch)', '50,000', 'Batch pricing default', 'mortgage_pricer.py:415'),
                    ('interest_rate (batch)', '0.035', '3.5\\% default rate', 'mortgage_pricer.py:417'),
                    ('insurance_rate (batch)', '0.002', '0.2\\% insurance', 'mortgage_pricer.py:418'),
                    ('recovery_haircut (batch)', '0.2', '20\\% recovery haircut', 'mortgage_pricer.py:420'),
                ]),
            ],
        },
    ]
