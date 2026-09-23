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
"""The SR 26-2 boundary, as a field every governed model record carries.

SR 26-2 draws the line: generative and agentic AI fall outside Model Risk Management
scope, traditional quantitative and machine-learning models stay in it. Spec v0.5 §2.1
(the AIGov edition, adopted 2026-09-23) stores that line as ``model_class`` because it is
the first filter an exam response or coverage report applies.

A record's TYPE fixes its class — a model in the inventory and an ML Application are both
``ML_APP``, an AI System is ``AI_SYSTEM`` — so the field is stamped at registration and
immutable afterwards. It can be read without being able to disagree with what the record
is; moving a record across the boundary means registering it as the other kind of record.

Its own module, with no imports, because the model inventory's config needs it and the AI
complexity config already imports the inventory's.
"""
from __future__ import annotations

MODEL_CLASS_FIELD = "model_class"
MODEL_CLASS_ML_APP = "ML_APP"
MODEL_CLASS_AI_SYSTEM = "AI_SYSTEM"
MODEL_CLASSES = (MODEL_CLASS_ML_APP, MODEL_CLASS_AI_SYSTEM)
MODEL_CLASS_LABELS = {
    MODEL_CLASS_ML_APP: "ML App (inside SR 26-2 MRM scope)",
    MODEL_CLASS_AI_SYSTEM: "AI System (generative or agentic)",
}

# Keyed by the aggregate type each domain registers under.
MODEL_CLASS_BY_RECORD_TYPE = {
    "ModelInventoryEntry": MODEL_CLASS_ML_APP,
    "MLApplication": MODEL_CLASS_ML_APP,
    "AISystem": MODEL_CLASS_AI_SYSTEM,
}

MODEL_CLASS_FIELD_SPEC = {
    MODEL_CLASS_FIELD: {"label": "Model class", "type": "choice", "options": MODEL_CLASSES,
                        "option_labels": MODEL_CLASS_LABELS, "immutable": True,
                        "group": "Classification"},
}

__all__ = ["MODEL_CLASSES", "MODEL_CLASS_AI_SYSTEM", "MODEL_CLASS_BY_RECORD_TYPE",
           "MODEL_CLASS_FIELD", "MODEL_CLASS_FIELD_SPEC", "MODEL_CLASS_LABELS",
           "MODEL_CLASS_ML_APP"]
