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
"""The model's challenge thread: the shared record of challenge, attached to models.

The machinery is in ``_review_thread`` and is identical for every governed record type.
What is left here is the attachment, and the names this module has always exported.
"""
from __future__ import annotations

from src.web._review_thread import (REVIEW_NOTES, challenges, open_challenges,
                                    register_review_note_route, role_of)
from src.web._signoff_subject import MODEL_SUBJECT
from src.web.api_models import models_bp

# Retained under its original private name: this module has always exported it.
_role = role_of

register_review_note_route(models_bp, MODEL_SUBJECT)

__all__ = ["REVIEW_NOTES", "challenges", "open_challenges", "role_of"]
