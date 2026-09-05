# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""What the reference lists are SEEDED with, apart from what they ARE.

The seam ``_data_sources`` already opened: a list's shape — its label, its id prefix,
the fields a row carries — is one thing, and the rows a fresh install starts with are
another. An adopter re-seeds these to their own estate on day one and never touches the
shapes; the two move at completely different rates.

Same rule for every list here: seeds a vacuum, never reconciles a curated one.

Re-exported from ``_reference`` so every existing import goes on working.
"""
from __future__ import annotations

# Analytical models price or quantify risk; Curve Models produce the hazard and
# damage curves the analytical engines consume; Market Data Models produce
# calibrated curves/surfaces. All are models -- they involve methodology and
# judgement, not raw vendor feeds -- which is why they sit on one inventory.
DEFAULT_MODEL_TYPES = (
    {"value": "Analytical Model", "binding_role": "Analytics"},
    {"value": "Curve Model", "binding_role": "Analytics"},
    {"value": "Market Data Model", "binding_role": "Market Data"},
    {"value": "Other", "binding_role": "Neither"},
)

# Simple single-value lists seeded on first use (same "seed a vacuum, never
# reconcile a curated list" rule as the model types above). Data sources are the
# feeds a model pulls its inputs from; Vendor names who supplies the model
# itself. Both are strict lists an adopter re-seeds to its own estate.
#
# The vendor seed names no institution: a fresh install should not plant this
# platform's author in an adopter's inventory, where it would sit in the Vendor
# menu as though it supplied their models. "In-house" is the honest starting
# point (most banks build their own), and every real supplier — including this
# one, on the MKM estate — is added in Admin > Vendor.
from config.governance._data_sources import DEFAULT_DATA_SOURCES  # noqa: E402
DEFAULT_VENDORS = ("In-house", "Other")
