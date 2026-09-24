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
"""The run-evidence vocabularies, as the console is served them.

One function so the AI System's ``/fields`` payload gains them in one line rather than
nine: the route module sits close to the line gate, and a console holding its own copy of
these lists would offer a response the domain then refuses.
"""
from __future__ import annotations

from typing import Any

from config.governance._ai_ace import ACE_DIMENSIONS, ACE_MIN_SAMPLES, ACE_SCALE
from config.governance._ai_evidence import (STRESS_OCCASIONS, STRESS_RESPONSE_LABELS,
                                            STRESS_RESPONSES, TRACE_CONTENT_LABELS,
                                            TRACE_PURPOSES, TRACE_REQUIRED_CONTENT)


def evidence_specs() -> dict[str, Any]:
    return {
        "trace_purposes": list(TRACE_PURPOSES),
        "trace_content_labels": dict(TRACE_CONTENT_LABELS),
        "trace_required_content": {k: list(v) for k, v in TRACE_REQUIRED_CONTENT.items()},
        "stress_occasions": list(STRESS_OCCASIONS),
        "stress_responses": list(STRESS_RESPONSES),
        "stress_response_labels": dict(STRESS_RESPONSE_LABELS),
        "ace_dimensions": list(ACE_DIMENSIONS),
        "ace_scale": list(ACE_SCALE),
        "ace_min_samples": ACE_MIN_SAMPLES,
    }


__all__ = ["evidence_specs"]
