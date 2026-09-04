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
"""The ML Application's review stages: the same workflow a model's review runs.

Deliberately this short. From a model-governance perspective a ML Application is a
model-governed record like any other, so it is reviewed through the same seven stages,
the same interim approvals and the same append-only progress register -- not through a
workflow of its own that would drift from the model's within a release. Everything is
in ``_review_stages``; the only thing particular to a ML Application is which record type
this attaches to.
"""
from __future__ import annotations

from src.web._review_stages import register_review_stage_routes
from src.web._review_signoff import register_review_signoff_routes
from src.web._review_thread import register_review_note_route
from src.web._signoff_subject import ML_APPLICATION_SUBJECT
from src.web.api_ml_application import ml_application_bp

register_review_stage_routes(ml_application_bp, ML_APPLICATION_SUBJECT)
register_review_note_route(ml_application_bp, ML_APPLICATION_SUBJECT)
register_review_signoff_routes(ml_application_bp, ML_APPLICATION_SUBJECT)
