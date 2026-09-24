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
"""The run evidence an AI System's owner — or its observability pipeline — records.

Three routes, one per record in ``config/governance/_ai_evidence.py``: a hashed trace
reference, a run of the stress-test suite, and a calibration of the judge against expert
grading. Each body carries raw material and the domain works out the verdict — whether
the trace is complete, which cases failed, what agreement the judge showed — for the
reason the envelope route gives: a caller that posts its own verdict has answered the
question the record exists to ask.

Attaches to ``ai_system_bp``; imported for its side effects in app.py.
"""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch
from src.governance.ai_system import (get_ai_system, rebuild_ai_system_view,
                                      record_judge_calibration, record_run_trace,
                                      record_stress_test_run)
from src.governance.ai_system._rules_evidence import judge_reliance
from src.web._helpers import context_from_request, json_body
from src.web.api_ai_system import ai_system_bp


def _data(ai_system_id: str) -> dict:
    return (get_ai_system(ai_system_id) or {}).get("data", {})


def _missing(ai_system_id: str):
    if get_ai_system(ai_system_id) is None:
        return jsonify({"error": "AI System not found"}), 404
    return None


@ai_system_bp.post("/<ai_system_id>/traces")
def record_trace(ai_system_id: str):
    """Reference one run's trace by where it lives and its SHA-256 content hash, and
    declare which parts of the required content it holds."""
    if (gone := _missing(ai_system_id)):
        return gone
    body = json_body()
    dispatch("record_run_trace", record_run_trace, context=context_from_request(body),
             ai_system_id=ai_system_id, run_id=body.get("run_id", ""),
             trace_uri=body.get("trace_uri", ""),
             content_hash=body.get("content_hash", ""),
             contents=body.get("contents") or [], purpose=body.get("purpose", ""))
    rebuild_ai_system_view()
    return jsonify({"trace": _data(ai_system_id)["run_traces"][-1]}), 201


@ai_system_bp.post("/<ai_system_id>/stress-runs")
def record_stress_run(ai_system_id: str):
    """Record what each case in the suite did: ``observed`` maps case id to response."""
    if (gone := _missing(ai_system_id)):
        return gone
    body = json_body()
    dispatch("record_stress_test_run", record_stress_test_run,
             context=context_from_request(body), ai_system_id=ai_system_id,
             occasion=body.get("occasion", ""), observed=body.get("observed") or {})
    rebuild_ai_system_view()
    return jsonify({"run": _data(ai_system_id)["stress_test_runs"][-1]}), 201


@ai_system_bp.post("/<ai_system_id>/calibrations")
def record_calibration(ai_system_id: str):
    """Reconcile expert and judge grading: ``pairs`` is ``[{expert, judge}]`` per item."""
    if (gone := _missing(ai_system_id)):
        return gone
    body = json_body()
    dispatch("record_judge_calibration", record_judge_calibration,
             context=context_from_request(body), ai_system_id=ai_system_id,
             judge_ai_system_id=body.get("judge_ai_system_id", ""),
             pairs=body.get("pairs") or [], dimension=body.get("dimension", ""))
    rebuild_ai_system_view()
    data = _data(ai_system_id)
    return jsonify({"calibration": data["judge_calibrations"][-1],
                    "judge_reliance": judge_reliance(data["judge_calibrations"])}), 201
