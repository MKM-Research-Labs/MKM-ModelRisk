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
"""Seeding the AI System questionnaire, so Admin > AI Review shows what is asked."""
from __future__ import annotations

from config.governance._ai import AI_SYSTEM_QUESTION_LIST, AI_SYSTEM_QUESTIONS
from config.identity import SYSTEM_ACTOR
from src.governance.reference._store import load
from src.governance.reference.commands import add_option


def ensure_default_ai_system_questions(*, actor: str = SYSTEM_ACTOR, config=None) -> int:
    """Seed the AI System questionnaire on a fresh install; return how many.

    Until this ran, the AI list was never seeded: AI Systems were asked the shipped
    questions through the fallback in ``compose_questions``, while Admin > AI Review
    said "None yet" -- so the questions looked removed, and could not be reworded
    without first being retyped. Seeded like the ML and common lists now, with the
    same words, so nothing a record is asked changes. Seeds a vacuum, never
    reconciles a curated list.
    """
    collections, _ = load(config)
    if collections.get(AI_SYSTEM_QUESTION_LIST):
        return 0
    for question in AI_SYSTEM_QUESTIONS:
        add_option(list_name=AI_SYSTEM_QUESTION_LIST, fields=dict(question), actor=actor,
                   reason="Seed the AI System questions on first run", config=config)
    return len(AI_SYSTEM_QUESTIONS)
