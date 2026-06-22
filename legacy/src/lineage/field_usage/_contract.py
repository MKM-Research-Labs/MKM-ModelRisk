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

"""AMBER contract / operational sub-trees (prefix rules).

Whole CDM sub-trees that are used operationally — loan terms, transaction
history, counterparty accounts, insurance ratings — but do not feed the PRS
spread. Matched by dotted-path prefix so we do not have to enumerate every
leaf. Anything not matched here (and not RED) defaults to GREEN (report only).
"""

from .tiers import AMBER


def _amber(summary, consumer):
    return {
        "tier": AMBER,
        "summary": summary,
        "consumers": [consumer],
        "chain": [
            {"node": "CDM field", "kind": "field"},
            {"node": consumer, "kind": "output"},
        ],
    }


# (prefix, entry) — a field matches when its path equals the prefix or starts
# with ``prefix + '.'``. Order matters only if prefixes overlap (they do not).
AMBER_PREFIXES = [
    ("TransactionHistory",
     _amber("Purchase, sale, rental and insurance history — operational / contract "
            "record, not a PRS input.", "Platform · contract record")),
    ("RLoan.Application",
     _amber("Loan application detail — operational record.", "Loan servicing")),
    ("RLoan.FinancialTerms",
     _amber("Loan financial terms (rate, term, LTV) — contract detail.", "Loan servicing")),
    ("RLoan.Features",
     _amber("Loan product features — contract detail.", "Loan servicing")),
    ("RLoan.CurrentStatus",
     _amber("Loan current status (balance, arrears) — servicing record.", "Loan servicing")),
    ("Mortgage.Application",
     _amber("Commercial loan application detail — operational record.", "Loan servicing")),
    ("Mortgage.FinancialTerms",
     _amber("Commercial loan financial terms — contract detail.", "Loan servicing")),
    ("Mortgage.Features",
     _amber("Commercial loan product features — contract detail.", "Loan servicing")),
    ("Mortgage.CurrentStatus",
     _amber("Commercial loan current status — servicing record.", "Loan servicing")),
    ("CounterpartySet.Party.Accounts",
     _amber("Counterparty settlement / collateral accounts — operational.", "Settlement")),
    ("CounterpartySet.Party.BusinessUnits",
     _amber("Counterparty business units — operational record.", "Onboarding")),
    ("CounterpartySet.Party.ContactInformation",
     _amber("Counterparty contact detail — operational record.", "Onboarding")),
    ("CounterpartySet.Party.NaturalPersons",
     _amber("Counterparty contacts — operational record.", "Onboarding")),
    ("ProtectionMeasures.RiskAssessment.InsuranceBodyRatings",
     _amber("Third-party insurance ratings — reference / operational, not a PRS input.",
            "Reference")),
]
