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
"""The models in scope at a meeting, and the analysis presented for each.

The endpoints themselves are in ``_scope``, generated from ``MEETING_SCOPE`` — a
model, an ML Application, an AI System and a Product are presented to the committee
identically, and this file existing separately is what let a model's tabled paper be
filed on the record while a product's was not.

Kept as its own module so the URL space and the import in ``api_mrc/__init__`` are
unchanged.
"""
from __future__ import annotations

from src.web._signoff_subject import MODEL_SUBJECT
from src.web.api_mrc._scope import register_scope_routes

register_scope_routes(MODEL_SUBJECT)
