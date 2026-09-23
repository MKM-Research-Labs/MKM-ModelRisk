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
"""The practice paper's nine concepts, the lifecycle phase each sits in, and which of the
four properties each advances.

Transcribed from Moody's *From Principles to Practice: Governing Generative and Agentic
AI Systems* (August 2026), the concept table and the lifecycle overview, as spec v0.5 §3.8
asks: the mapping is configuration, so that the property coverage view can say, for any
AI System, which of correctness, consistency, robustness and predictability currently rest
on live evidence — and so that a revised paper is an edit here, not a code change.

``INTENSITY_CONCEPTS`` is the second open table from spec §12 — which evidence each grid
cell requires — seeded as cumulative bands: each intensity asks for everything the one
below it does, and more. Concept 6 is asked of agents only, whatever the band, because a
system with no runtime path has no trajectory to score.
"""
from __future__ import annotations

from config.governance._ai_complexity import (AI_AUTONOMY_AGENT, INTENSITY_BASELINE,
                                              INTENSITY_ENHANCED, INTENSITY_INTENSIVE,
                                              INTENSITY_STANDARD)
from config.governance._ai_triggers import (PROPERTY_CONSISTENCY, PROPERTY_CORRECTNESS,
                                            PROPERTY_PREDICTABILITY, PROPERTY_ROBUSTNESS)

PHASE_DESIGN = "Design & Instrument"
PHASE_BASELINE = "Establish Baseline"
PHASE_OPERATE = "Operate & Measure"
PHASE_ESCALATE = "Escalate"
PHASE_REVALIDATE = "Revalidate"
AI_LIFECYCLE_PHASES = (PHASE_DESIGN, PHASE_BASELINE, PHASE_OPERATE, PHASE_ESCALATE,
                       PHASE_REVALIDATE)

_C, _K, _R, _P = (PROPERTY_CORRECTNESS, PROPERTY_CONSISTENCY, PROPERTY_ROBUSTNESS,
                  PROPERTY_PREDICTABILITY)

# (number, name, phase, properties advanced). The numbers are the paper's and are what a
# reader cross-references, so they are part of the key rather than a display order.
AI_CONCEPTS: tuple[dict, ...] = (
    {"number": 1, "name": "Design-time choices", "phase": PHASE_DESIGN,
     "properties": (_C, _K, _R)},
    {"number": 2, "name": "Observability & trace completion", "phase": PHASE_DESIGN,
     "properties": (_C, _K, _R, _P)},
    {"number": 3, "name": "Expert-grounded benchmarking", "phase": PHASE_BASELINE,
     "properties": (_C,)},
    {"number": 4, "name": "The variability envelope", "phase": PHASE_BASELINE,
     "properties": (_C, _K, _R)},
    {"number": 5, "name": "Continuous monitoring", "phase": PHASE_OPERATE,
     "properties": (_C, _K)},
    {"number": 6, "name": "Agentic trajectory governance", "phase": PHASE_OPERATE,
     "properties": (_C, _K, _R, _P)},
    {"number": 7, "name": "Adversarial & operational robustness", "phase": PHASE_OPERATE,
     "properties": (_R,)},
    {"number": 8, "name": "Triggers, escalations & fallback", "phase": PHASE_ESCALATE,
     "properties": (_C, _R, _P)},
    {"number": 9, "name": "Revalidation & version control", "phase": PHASE_REVALIDATE,
     "properties": (_C, _K)},
)
AI_CONCEPT_NUMBERS = tuple(c["number"] for c in AI_CONCEPTS)

# Concepts asked of a system only at one autonomy level. Anything absent applies to all.
CONCEPT_AUTONOMY: dict[int, tuple[str, ...]] = {6: (AI_AUTONOMY_AGENT,)}

# Which concepts each governance intensity asks to rest on evidence. Seeded (spec §12
# leaves it open): design, trace, benchmark and revalidation are the floor — without
# them no accuracy claim can be made at all — and each band above adds the controls whose
# cost is only justified by more exposure.
_FLOOR = (1, 2, 3, 9)
INTENSITY_CONCEPTS: dict[str, tuple[int, ...]] = {
    INTENSITY_BASELINE: _FLOOR,
    INTENSITY_STANDARD: _FLOOR + (4, 5),
    INTENSITY_ENHANCED: _FLOOR + (4, 5, 6, 8),
    INTENSITY_INTENSIVE: _FLOOR + (4, 5, 6, 7, 8),
}


__all__ = ["AI_CONCEPTS", "AI_CONCEPT_NUMBERS", "AI_LIFECYCLE_PHASES",
           "CONCEPT_AUTONOMY", "INTENSITY_CONCEPTS", "PHASE_BASELINE", "PHASE_DESIGN",
           "PHASE_ESCALATE", "PHASE_OPERATE", "PHASE_REVALIDATE"]
