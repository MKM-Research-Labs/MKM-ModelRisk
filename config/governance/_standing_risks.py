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
"""The standing risk register: risks that do not belong to a lifecycle phase.

Most AI risks attach to a moment — you baseline, you measure, you escalate, you
revalidate. These do not. Bias does not arrive at a release; it is a property of a
system for as long as the system runs. Copyright exposure does not get measured and
closed. Reputational risk has no threshold. They sit outside the five-phase lifecycle
and are reviewed at onboarding and at every Material revalidation, which is why they
are a REGISTER rather than a stage: a stage you complete, and none of these completes.

**Identical under every deployment, by design.** No entry is muted or filtered per
deployment: the register reads the same from MKM's own instance and from a fork of it.
A register that showed a shorter list in one deployment would be a register whose
absences nobody could account for, and the one thing worse than an unmanaged risk is an
unmanaged risk somebody has been told does not apply to them.

**AI Systems only.** ML Applications have their own boundary (spec §7): a fitted
estimator carries bias and IP questions too, but they are answered inside its training
and validation record rather than as standing exposures of a bought-in model somebody
else trained. Extending this register to ML Applications would duplicate what the ML
review already asks.

The identifiers are the FINOS catalogue's own. The spec names six; this platform's
catalogue defines five of them, and no sixth is invented here — a register entry naming
a risk the catalogue does not define could not be evidenced against it.
"""
from __future__ import annotations

# Reviewed whenever one of these happens, and not on a schedule of their own: a
# standing risk reviewed quarterly regardless of what changed is a diary entry.
REVIEW_AT_ONBOARDING = "onboarding"
REVIEW_AT_MATERIAL_REVALIDATION = "material revalidation"
STANDING_REVIEW_POINTS = (REVIEW_AT_ONBOARDING, REVIEW_AT_MATERIAL_REVALIDATION)

# (FINOS id, title, why it stands outside the lifecycle)
STANDING_RISKS = (
    ("AIR-OP-016", "Bias and Discrimination",
     "A property of the system for as long as it runs, not an event at a release. It "
     "is measured against attributes on the fairness register, and the measurement "
     "ages rather than closing."),
    ("AIR-RC-023", "Intellectual Property and Copyright",
     "Exposure follows from what the model was trained on and what it reproduces, "
     "neither of which the firm controls or can close out. It changes when the law or "
     "the provider's terms change, not when the system does."),
    ("AIR-OP-020", "Reputational Risk",
     "Has no threshold and no test. What makes it standing is that its trigger is "
     "external — a story about somebody else's system moves this firm's exposure "
     "without anything here changing."),
    ("AIR-OP-007", "Availability of the Foundation Model",
     "A supply-chain dependency the institution does not own. The provider may "
     "deprecate, rate-limit or withdraw the model, and no amount of governance here "
     "prevents it — which is exactly why it is carried rather than mitigated."),
    ("AIR-SEC-026", "MCP Server Supply Chain Compromise",
     "The deep supply chain: a server the firm reaches but does not run, whose "
     "compromise reaches every agentic system that calls it. Treated generically "
     "elsewhere; named here because the agentic estate makes it concrete."),
)

STANDING_RISK_IDS = tuple(ref for ref, _, _ in STANDING_RISKS)

__all__ = ["REVIEW_AT_MATERIAL_REVALIDATION", "REVIEW_AT_ONBOARDING",
           "STANDING_REVIEW_POINTS", "STANDING_RISKS", "STANDING_RISK_IDS"]
