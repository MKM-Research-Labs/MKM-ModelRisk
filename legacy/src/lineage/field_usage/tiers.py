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

"""Usage tiers for CDM field downstream lineage.

A field is classified by how far downstream its value travels:

    RED    — feeds the PRS pricing (directly, or via a peril damage function
             whose loss drives the PRS spread). Highest scrutiny.
    AMBER  — contract / operational detail: used by the platform (loan terms,
             transaction history, counterparty accounts) but not in the PRS.
    GREEN  — descriptive: only appears in the property/asset report.

GREEN is the default for any field not explicitly classified.
"""

RED = "RED"
AMBER = "AMBER"
GREEN = "GREEN"

DEFAULT_TIER = GREEN

# Display metadata for the legend and the lineage popup. Colours match the
# CDM Asset Review palette (RED #d32f2f, AMBER #f57c00, GREEN #388e3c).
TIER_META = {
    RED: {
        "label": "Feeds PRS pricing",
        "colour": "#d32f2f",
        "description": "Feeds the PRS spread — directly or via a peril damage function.",
    },
    AMBER: {
        "label": "Contract / operational",
        "colour": "#f57c00",
        "description": "Used operationally (contract, loan, transaction, counterparty) — not in the PRS.",
    },
    GREEN: {
        "label": "Report only",
        "colour": "#388e3c",
        "description": "Descriptive field — used only in the property/asset report.",
    },
}
