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
"""The measured monitoring position, for the console.

Served rather than computed in the browser: the measures are one implementation with
hand-checked arithmetic, and a second one in JavaScript would be a second answer. The
screen asks and prints.

Attached to every governed record type, because "has this drifted, and did what it
predicted happen" is one question whatever produced the number.
"""
from __future__ import annotations

from flask import jsonify

from src.governance.monitoring.measured import measured_position


def register_monitoring_route(blueprint, subject) -> None:
    # The Subject carries how its record type reads in a sentence written for a
    # person. Derived from ``kind`` here until main brought a better answer:
    # "the ai_system was not found" is what string-munging a machine key gets you.
    noun = subject.noun

    @blueprint.get("/<subject_id>/monitoring")
    def monitoring(subject_id: str):
        """What the statistics say about this record, or what is missing and why."""
        record = subject.get(subject_id)
        if record is None:
            return jsonify({"error": f"{noun} not found"}), 404
        return jsonify(measured_position(record.get("data") or {}))

    return monitoring
