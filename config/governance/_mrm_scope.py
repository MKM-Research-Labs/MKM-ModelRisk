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
"""What is in model risk management scope, and what is governed outside it.

The question an examiner asks first, and the one a coverage table cannot answer on its
own: a clause met by 90% of the estate says nothing until somebody says what the estate
IS. This names the boundary and, just as important, what sits beyond it and is still
governed — because "out of scope" read without that looks like "ungoverned", and the
two are not the same thing.

**The record type is the filter.** There is no ``model_class`` field and there must not
be one: a record's type is what it IS, and duplicating it into a classification column
for reporting convenience gives two answers that drift the first time somebody edits
one. A test asserts no such field exists on any record type.

Three record types are in scope because all three are applications of a model that
produce a number or a judgement somebody relies on. What is outside is outside for two
different reasons, and the distinction matters to a reader:

  governed elsewhere   the firm governs it, through a different process — a Product is
                       governed as a product, not as a model
  not the firm's       a dependency it uses and does not own, which it can assess and
                       cannot validate: a foundation model somebody else trained, an
                       MCP server somebody else runs
"""
from __future__ import annotations

# Subject kinds (src/web/_signoff_subject.py) that are model-risk records.
IN_SCOPE_RECORD_TYPES = (
    ("model", "Model",
     "A model the firm builds or buys and runs: methodology, assumptions and a "
     "validated result."),
    ("ml_application", "ML Application",
     "The firm's USE of an off-the-shelf estimator. The estimator is somebody else's; "
     "the fitting, the features and the decision it informs are the firm's."),
    ("ai_system", "AI System",
     "A deployed use of a generative or agentic model. The model is somebody else's; "
     "the prompt, the tools, the grounding and the exposure are the firm's."),
)

GOVERNED_ELSEWHERE = (
    ("product", "Product",
     "Governed as a product: it binds models rather than being one, and its risk is "
     "in the binding — which analytics engine, which market data, which agent."),
    ("handoff", "Model handoff",
     "Governed as a compatibility question between two models, ratified by the "
     "committee. It is a relationship, not a record that produces a number."),
)

# Lineage node kinds the firm depends on and does not own. Kept as node kinds rather
# than as records because that is exactly what they are: things a chain points at.
NOT_THE_FIRMS = (
    ("FOUNDATION_MODEL", "Foundation model",
     "Trained and versioned by a provider. The firm can pin it, test against it and "
     "record what it depends on; it cannot validate it, and saying otherwise in a "
     "coverage report would be the flattering reading."),
    ("MCP_SERVER", "MCP server",
     "Run outside the firm and reached by its agentic systems. Assessable as a supply "
     "chain dependency, not validatable as a model."),
)

IN_SCOPE_KINDS = tuple(kind for kind, _, _ in IN_SCOPE_RECORD_TYPES)

# Which id field each in-scope record type is keyed by, so one breakdown can count a
# mixed population without asking each row what it is.
RECORD_TYPE_ID_FIELDS = {
    "model": "model_id",
    "ml_application": "ml_application_id",
    "ai_system": "ai_system_id",
}

__all__ = ["GOVERNED_ELSEWHERE", "IN_SCOPE_KINDS", "IN_SCOPE_RECORD_TYPES",
           "NOT_THE_FIRMS", "RECORD_TYPE_ID_FIELDS"]
