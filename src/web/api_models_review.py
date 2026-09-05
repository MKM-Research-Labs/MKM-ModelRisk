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
"""The model's review stages: the shared workflow, attached to the model inventory.

The machinery is in ``_review_stages`` and is identical for every governed record type
-- see that module for why. What is left here is the attachment, and the names this
module has always exported, which the review report, the sign-off gate and the tests
import from it.
"""
from __future__ import annotations

from src.web._review_stages import (REVIEW_PROGRESS, approvals, cycles,
                                    register_review_stage_routes, stage_by_key,
                                    stamped_now)
from src.web._monitoring_position import register_monitoring_route
from src.web._signoff_subject import MODEL_SUBJECT
from src.web.api_models import models_bp

VALIDATION_QUESTIONS = MODEL_SUBJECT.questions_collection()

# Kept as a module-level name because ``api_models_review_notes`` validates a note's
# stage against it. A model's stages are the shared stages in the model's own wording.
_STAGE_BY_KEY = stage_by_key(MODEL_SUBJECT)

# Retained under its original private name: this module has always exported it.
_stamped_now = stamped_now

register_review_stage_routes(models_bp, MODEL_SUBJECT)
register_monitoring_route(models_bp, MODEL_SUBJECT)

__all__ = ["REVIEW_PROGRESS", "VALIDATION_QUESTIONS", "approvals", "cycles",
           "stage_by_key", "stamped_now"]
