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
"""Admin > AI Review shows the questions AI Systems are actually asked."""
from __future__ import annotations

from config.governance._ai import AI_SYSTEM_QUESTION_LIST, AI_SYSTEM_QUESTIONS
from src.governance.reference import (ensure_default_ai_system_questions,
                                      get_reference_lists)


def test_the_ai_questionnaire_is_seeded_with_the_shipped_questions():
    assert ensure_default_ai_system_questions() == len(AI_SYSTEM_QUESTIONS)
    seeded = get_reference_lists()[AI_SYSTEM_QUESTION_LIST]
    assert [(q["short_label"], q["question"]) for q in seeded] == [
        (q["short_label"], q["question"]) for q in AI_SYSTEM_QUESTIONS]
    # Seeds a vacuum only: a curated list is never topped back up.
    assert ensure_default_ai_system_questions() == 0
