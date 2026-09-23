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
"""The SR 26-2 boundary, and the second complexity axis an AI System carries.

**Classification** (spec v0.5 §2.1, the AIGov edition). ``model_class`` is the line SR 26-2
draws: generative and agentic AI fall outside Model Risk Management scope, traditional
quantitative and machine-learning models stay in it. It is stored on the record because
it is the first filter an exam response or coverage report applies, and a structural
two-value field is harder to get quietly wrong than a value buried in a longer enum. A
record's type fixes which class it may carry — ``MODEL_CLASS_BY_RECORD_TYPE`` — so the
field can be read without being able to disagree with what the record is.

**AI complexity** (§2.2). Materiality and the existing complexity attribute apply to
every record unchanged. For an AI System they are not enough: the governance difficulty
it brings is driven by how much of its path it chooses at runtime and how often it runs,
which the existing attribute does not capture. Two further fields carry that, populated
only on an AI System, and nothing here repurposes ``complexity``.

**Everything below is a seeded default, not a decision.** The spec leaves the frequency
scale, the rule combining autonomy with frequency, and the grid-to-intensity table open
(§12). They are held here as data precisely so that an adopter — and the ModelOne fork —
edits a table rather than a function (§4).
"""
from __future__ import annotations

from config.governance._inventory import VALID_COMPLEXITY, VALID_MATERIALITY

# --- The SR 26-2 boundary --------------------------------------------------------------

MODEL_CLASS_ML_APP = "ML_APP"
MODEL_CLASS_AI_SYSTEM = "AI_SYSTEM"
MODEL_CLASSES = (MODEL_CLASS_ML_APP, MODEL_CLASS_AI_SYSTEM)
MODEL_CLASS_LABELS = {
    MODEL_CLASS_ML_APP: "ML App (inside SR 26-2 MRM scope)",
    MODEL_CLASS_AI_SYSTEM: "AI System (generative or agentic)",
}

# A model in the inventory and an ML Application are both traditional quantitative or
# ML work; an AI System is not. Keyed by the aggregate type each domain registers under.
MODEL_CLASS_BY_RECORD_TYPE = {
    "ModelInventoryEntry": MODEL_CLASS_ML_APP,
    "MLApplication": MODEL_CLASS_ML_APP,
    "AISystem": MODEL_CLASS_AI_SYSTEM,
}

AI_SYSTEM_TYPE_GENERATIVE = "GENERATIVE"
AI_SYSTEM_TYPE_AGENTIC = "AGENTIC"
AI_SYSTEM_TYPES = (AI_SYSTEM_TYPE_GENERATIVE, AI_SYSTEM_TYPE_AGENTIC)
AI_SYSTEM_TYPE_LABELS = {AI_SYSTEM_TYPE_GENERATIVE: "Generative",
                         AI_SYSTEM_TYPE_AGENTIC: "Agentic"}

# --- The AI complexity axis ------------------------------------------------------------

# Anchored to the practice paper's system taxonomy. Ordered from least to most runtime
# choice, which is the order the combination table below reads them in. The same value
# sets how much a run's trace must record (§9.1).
AI_AUTONOMY_SINGLE_CALL = "SINGLE_CALL"
AI_AUTONOMY_WORKFLOW = "WORKFLOW"
AI_AUTONOMY_AGENT = "AGENT"
AI_AUTONOMY_LEVELS = (AI_AUTONOMY_SINGLE_CALL, AI_AUTONOMY_WORKFLOW, AI_AUTONOMY_AGENT)
AI_AUTONOMY_LABELS = {
    AI_AUTONOMY_SINGLE_CALL: "Single AI call — one inference step",
    AI_AUTONOMY_WORKFLOW: "AI workflow — a fixed sequence of steps",
    AI_AUTONOMY_AGENT: "AI agent — a trajectory chosen at runtime",
}

# No scale is prescribed by the source material. Seeded as four bands, least to most
# frequent, on the reasoning that what matters to governance is how many runs go
# unobserved between two looks at the system — not the exact rate.
AI_USAGE_FREQUENCIES = ("AD_HOC", "PERIODIC", "DAILY", "CONTINUOUS")
AI_USAGE_FREQUENCY_LABELS = {
    "AD_HOC": "Ad hoc — run on request, a handful of times",
    "PERIODIC": "Periodic — a scheduled cycle, weekly to quarterly",
    "DAILY": "Daily — part of a working day's routine",
    "CONTINUOUS": "Continuous — in the transaction or customer path",
}

# The combination rule, as a table rather than arithmetic: a committee can read and
# amend a cell, where it cannot amend a formula. The result is read on the existing
# complexity scale so that the grid's two axes share a vocabulary.
AI_COMPLEXITY_RULE: dict[tuple[str, str], str] = {
    (AI_AUTONOMY_SINGLE_CALL, "AD_HOC"): "Low",
    (AI_AUTONOMY_SINGLE_CALL, "PERIODIC"): "Low",
    (AI_AUTONOMY_SINGLE_CALL, "DAILY"): "Medium",
    (AI_AUTONOMY_SINGLE_CALL, "CONTINUOUS"): "Medium",
    (AI_AUTONOMY_WORKFLOW, "AD_HOC"): "Low",
    (AI_AUTONOMY_WORKFLOW, "PERIODIC"): "Medium",
    (AI_AUTONOMY_WORKFLOW, "DAILY"): "Medium",
    (AI_AUTONOMY_WORKFLOW, "CONTINUOUS"): "High",
    (AI_AUTONOMY_AGENT, "AD_HOC"): "Medium",
    (AI_AUTONOMY_AGENT, "PERIODIC"): "High",
    (AI_AUTONOMY_AGENT, "DAILY"): "High",
    (AI_AUTONOMY_AGENT, "CONTINUOUS"): "High",
}
AI_COMPLEXITY_LEVELS = VALID_COMPLEXITY

# --- Materiality × AI complexity → governance intensity --------------------------------

INTENSITY_BASELINE = "Baseline"
INTENSITY_STANDARD = "Standard"
INTENSITY_ENHANCED = "Enhanced"
INTENSITY_INTENSIVE = "Intensive"
GOVERNANCE_INTENSITIES = (INTENSITY_BASELINE, INTENSITY_STANDARD, INTENSITY_ENHANCED,
                          INTENSITY_INTENSIVE)

# Keyed (materiality, AI complexity). Rises along both axes, as proportionality asks,
# and never falls: a cell is at least as intense as any cell below or to its left. The
# test suite holds that property, so an edit that breaks it fails rather than ships.
GRID_INTENSITY: dict[tuple[str, str], str] = {
    ("Low", "Low"): INTENSITY_BASELINE,
    ("Low", "Medium"): INTENSITY_STANDARD,
    ("Low", "High"): INTENSITY_ENHANCED,
    ("Medium", "Low"): INTENSITY_STANDARD,
    ("Medium", "Medium"): INTENSITY_ENHANCED,
    ("Medium", "High"): INTENSITY_ENHANCED,
    ("High", "Low"): INTENSITY_ENHANCED,
    ("High", "Medium"): INTENSITY_INTENSIVE,
    ("High", "High"): INTENSITY_INTENSIVE,
}
GRID_MATERIALITY_LEVELS = VALID_MATERIALITY

# Shown when a record cannot be placed, naming what is missing. An unplaced system is
# reported as unplaced — never quietly given a cell, since the cell is what sets how much
# evidence is asked of it.
GRID_UNPLACED = "Not placed"

# --- The fields, as the AI System record carries them ----------------------------------

# Spread into ``AI_SYSTEM_FIELD_SPECS`` rather than written there, which sits at the line
# gate. Each stores the code the spec names and shows its label. ``model_class`` is
# immutable: registration stamps it from the record type, and the only way to move a
# record across the SR 26-2 boundary is to register it as the other kind of record.
AI_COMPLEXITY_FIELD_SPECS = {
    "model_class": {"label": "Model class", "type": "choice", "options": MODEL_CLASSES,
                    "option_labels": MODEL_CLASS_LABELS, "immutable": True,
                    "group": "Classification"},
    "ai_system_type": {"label": "AI system type", "type": "choice",
                       "options": AI_SYSTEM_TYPES, "option_labels": AI_SYSTEM_TYPE_LABELS,
                       "group": "Classification"},
    "ai_autonomy": {"label": "Autonomy", "type": "choice", "options": AI_AUTONOMY_LEVELS,
                    "option_labels": AI_AUTONOMY_LABELS, "group": "Classification"},
    "ai_usage_frequency": {"label": "Usage frequency", "type": "choice",
                           "options": AI_USAGE_FREQUENCIES,
                           "option_labels": AI_USAGE_FREQUENCY_LABELS,
                           "group": "Classification"},
}
# Offered on the register form, never demanded: a system is registered before anybody
# has measured how often it runs, and an unplaced system says so on its record.
AI_COMPLEXITY_REGISTER_OPTIONAL = ("ai_system_type", "ai_autonomy", "ai_usage_frequency")


__all__ = ["AI_COMPLEXITY_FIELD_SPECS", "AI_COMPLEXITY_REGISTER_OPTIONAL","AI_AUTONOMY_AGENT", "AI_AUTONOMY_LABELS", "AI_AUTONOMY_LEVELS",
           "AI_AUTONOMY_SINGLE_CALL", "AI_AUTONOMY_WORKFLOW", "AI_COMPLEXITY_LEVELS",
           "AI_COMPLEXITY_RULE", "AI_SYSTEM_TYPES", "AI_SYSTEM_TYPE_AGENTIC",
           "AI_SYSTEM_TYPE_GENERATIVE", "AI_SYSTEM_TYPE_LABELS", "AI_USAGE_FREQUENCIES",
           "AI_USAGE_FREQUENCY_LABELS", "GOVERNANCE_INTENSITIES", "GRID_INTENSITY",
           "GRID_MATERIALITY_LEVELS", "GRID_UNPLACED", "INTENSITY_BASELINE",
           "INTENSITY_ENHANCED", "INTENSITY_INTENSIVE", "INTENSITY_STANDARD",
           "MODEL_CLASSES", "MODEL_CLASS_AI_SYSTEM", "MODEL_CLASS_BY_RECORD_TYPE",
           "MODEL_CLASS_LABELS", "MODEL_CLASS_ML_APP"]
