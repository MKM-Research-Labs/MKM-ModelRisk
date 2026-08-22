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
"""The shape every admin-managed vocabulary takes (coding rule R1).

``value`` is what a record STORES and what the code matches on; ``label`` is what a
screen shows. Seeding the value to today's word is what makes these free of
migration: renaming an entry edits the label and moves nothing in the estate.

Held in its own module because more than one area defines vocabularies now -- the
status words in ``_reference``, the training enumerations in ``_ml_training`` -- and
a second copy of this shape is a second thing to keep in step.
"""
from __future__ import annotations


def status_vocabulary_spec(label: str, prefix: str, hint: str = "") -> dict:
    """A two-column vocabulary: the word shown, and the word records carry.

    ``value`` is immutable once the entry exists: records already carry it, and
    editing it would orphan every one of them.

    ``hint`` says what the list is FOR. Several vocabularies share one admin page, and
    without it a reader meets eleven tables of words with nothing to say which governs
    what -- the definition already exists in config and simply was not being shown.
    """
    return {"label": label, "id_prefix": prefix, "display": "label", "value_key": "value",
            "hint": hint,
            "fields": [
                {"key": "label", "label": "Shown as", "type": "text", "required": True},
                {"key": "value", "label": "Stored as", "type": "text", "required": True,
                 "immutable": True},
            ]}
