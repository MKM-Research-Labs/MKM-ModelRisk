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
"""Property coverage: which of the four properties an AI System's evidence actually holds up.

Spec v0.5 §3.8 (AIGov edition). For each of the practice paper's nine concepts, one
question — is there evidence, and is it about the system as configured NOW — and then,
for each property, the concepts that advance it (config/governance/_ai_concepts.py).

Pure, and resolved on read like the grid position: nothing is stored, so recording a
piece of evidence moves the view at once and a stale view cannot exist.

**Current means under the configuration in force.** Evidence produced under an earlier
configuration snapshot is STALE, not absent: it is on record and it describes a system
that no longer exists. A system whose fields have moved since its last snapshot has no
current configuration version at all, so everything bound to one reads stale.

**Which concepts count** is the grid's answer when the system is placed (its intensity
band, less what its autonomy exempts it from). An unplaced system is held to every
applicable concept and the result says so, rather than to none.
"""
from __future__ import annotations

from typing import Any, Callable

from config.governance._ai_concepts import (AI_CONCEPTS, CONCEPT_AUTONOMY,
                                            EVIDENCE_ABSENT, EVIDENCE_FAILING,
                                            EVIDENCE_LIVE, EVIDENCE_NOT_APPLICABLE,
                                            EVIDENCE_STALE, PROPERTY_LIVE,
                                            PROPERTY_NOT_ASKED, PROPERTY_PARTIAL,
                                            PROPERTY_UNCOVERED)
from config.governance._ai_system import CONFIGURATION_FIELDS
from config.governance._ai_triggers import TRIGGER_PROPERTIES
from src.governance.ai_system._rules_baseline import manifest_intact
from src.governance.ai_system._rules_evidence import (JUDGE_RELIANCE_SUSPENDED,
                                                      judge_reliance)
from src.governance.ai_system.envelope import envelope_status
from src.governance.ai_system.judges import judges_of
from src.governance.ai_system.trajectory import is_agentic

_FAILED_EVALUATION = "Failed"


def _current_version(data: dict[str, Any]) -> int | None:
    """The configuration version in force, or ``None`` when the record has moved past its
    last snapshot (or never had one)."""
    snapshots = data.get("configuration_snapshots") or []
    if not snapshots:
        return None
    live = {f: data.get(f) for f in CONFIGURATION_FIELDS}
    return snapshots[-1]["config_version"] if snapshots[-1].get("values") == live else None


def _result(status: str, detail: str) -> tuple[str, str]:
    return status, detail


def _design(data, version):
    if not data.get("configuration_snapshots"):
        return _result(EVIDENCE_ABSENT, "No configuration snapshot taken.")
    if version is None:
        return _result(EVIDENCE_STALE, "The configuration has moved since its last "
                                       "snapshot.")
    return _result(EVIDENCE_LIVE, f"Configuration v{version} is pinned and unchanged.")


def _bound(rows, version, noun):
    """The rows produced under the configuration in force, or why there are none."""
    if not rows:
        return None, _result(EVIDENCE_ABSENT, f"No {noun} recorded.")
    current = [r for r in rows if r.get("config_version") == version]
    if version is None or not current:
        return None, _result(EVIDENCE_STALE, f"Every {noun} predates the configuration "
                                             "in force.")
    return current, None


def _traces(data, version):
    current, why = _bound(data.get("run_traces") or [], version, "trace")
    if why:
        return why
    if not current[-1].get("complete"):
        return _result(EVIDENCE_FAILING, f"The latest trace ({current[-1]['run_id']}) "
                                         "is incomplete.")
    return _result(EVIDENCE_LIVE, f"{len(current)} trace(s) under v{version}; the latest "
                                  "is complete.")


def _suspended(data) -> list[str]:
    reliance = judge_reliance(data.get("judge_calibrations") or [])
    return [j for j, s in reliance.items() if s == JUDGE_RELIANCE_SUSPENDED]


def _benchmark(data, version):
    rows = data.get("evaluations") or []
    if not rows:
        return _result(EVIDENCE_ABSENT, "No evaluation recorded.")
    suspended = [j for j in judges_of({"evaluations": rows}) if j in _suspended(data)]
    if suspended:
        return _result(EVIDENCE_FAILING, f"Scored by a suspended judge: "
                                         f"{', '.join(suspended)}.")
    if rows[-1].get("passed") == _FAILED_EVALUATION:
        return _result(EVIDENCE_FAILING, "The latest evaluation failed.")
    return _result(EVIDENCE_LIVE, f"{len(rows)} evaluation(s); the latest did not fail.")


def _envelope(data, version):
    rows = data.get("variability_envelopes") or []
    if not rows:
        return _result(EVIDENCE_ABSENT, "No variability envelope measured.")
    status = envelope_status(rows[-1], version)
    if status.get("status") == "ok":
        return _result(EVIDENCE_LIVE, f"Measured under v{version}.")
    if rows[-1].get("config_version") != version:
        return _result(EVIDENCE_STALE, "Measured under a configuration no longer in force.")
    return _result(EVIDENCE_FAILING, f"The envelope reads: {status.get('status')}.")


def _monitoring(data, version):
    if _suspended(data):
        return _result(EVIDENCE_FAILING, "Reliance on the judge is suspended: "
                                         f"{', '.join(_suspended(data))}.")
    observations = data.get("monitoring_observations") or []
    calibrations = data.get("judge_calibrations") or []
    if not observations and not calibrations:
        return _result(EVIDENCE_ABSENT, "No monitoring observation or judge calibration.")
    return _result(EVIDENCE_LIVE, f"{len(observations)} observation(s), "
                                  f"{len(calibrations)} calibration(s) in force.")


def _trajectory(data, version):
    # No trajectory score is stored anywhere yet: the scorer exists, its results do not.
    return _result(EVIDENCE_ABSENT, "No trajectory score recorded.")


def _stress(data, version):
    current, why = _bound(data.get("stress_test_runs") or [], version, "stress-test run")
    if why:
        return why
    latest = current[-1]
    if not latest.get("passed"):
        return _result(EVIDENCE_FAILING, f"Suite v{latest['suite_version']} failed "
                                         f"{', '.join(latest.get('failed') or [])}.")
    return _result(EVIDENCE_LIVE, f"Suite v{latest['suite_version']} passed under "
                                  f"v{version}.")


def _triggers(data, version):
    held = data.get("trigger_thresholds") or {}
    set_ = [p for p in TRIGGER_PROPERTIES if (held.get(p) or {}).get("threshold") is not None]
    if not set_:
        return _result(EVIDENCE_ABSENT, "No trigger threshold set.")
    if len(set_) < len(TRIGGER_PROPERTIES):
        return _result(EVIDENCE_FAILING, f"{len(set_)} of {len(TRIGGER_PROPERTIES)} "
                                         "properties have a threshold.")
    return _result(EVIDENCE_LIVE, "Every property has a threshold and a fallback.")


def _revalidation(data, version):
    rows = data.get("release_manifests") or []
    if not rows:
        return _result(EVIDENCE_ABSENT, "No release manifest sealed.")
    latest = rows[-1]
    if not manifest_intact(latest):
        return _result(EVIDENCE_FAILING, f"Release {latest.get('release')} no longer "
                                         "matches its sealed digest.")
    if (latest.get("contents") or {}).get("config_version") != version or version is None:
        return _result(EVIDENCE_STALE, "The last sealed release predates the "
                                       "configuration in force.")
    return _result(EVIDENCE_LIVE, f"Release {latest.get('release')} sealed at v{version}.")


_CHECKS: dict[int, Callable] = {1: _design, 2: _traces, 3: _benchmark, 4: _envelope,
                                5: _monitoring, 6: _trajectory, 7: _stress,
                                8: _triggers, 9: _revalidation}


def _applies(number: int, data: dict[str, Any]) -> bool:
    if number not in CONCEPT_AUTONOMY:
        return True
    # Trajectory scoring: an agent by its autonomy, or — for a record not yet
    # classified — by the deployment pattern the older rule read.
    return data.get("ai_autonomy") in CONCEPT_AUTONOMY[number] or (
        not data.get("ai_autonomy") and is_agentic(data))


def property_coverage(data: dict[str, Any], grid: dict[str, Any]) -> dict[str, Any]:
    """``{concepts: [...], properties: {name: {...}}, held_to, placed}`` for one system."""
    version = _current_version(data)
    required = set(grid.get("concepts") or ()) if grid.get("placed") else None
    concepts = []
    for concept in AI_CONCEPTS:
        n = concept["number"]
        if not _applies(n, data):
            status, detail = EVIDENCE_NOT_APPLICABLE, "Not asked of a system at this autonomy."
        else:
            status, detail = _CHECKS[n](data, version)
        asked = status != EVIDENCE_NOT_APPLICABLE and (required is None or n in required)
        concepts.append({**concept, "properties": list(concept["properties"]),
                         "status": status, "detail": detail, "asked": asked})
    properties = {}
    for prop in TRIGGER_PROPERTIES:
        counted = [c for c in concepts if c["asked"] and prop in c["properties"]]
        live = [c["number"] for c in counted if c["status"] == EVIDENCE_LIVE]
        if not counted:
            verdict = PROPERTY_NOT_ASKED
        elif len(live) == len(counted):
            verdict = PROPERTY_LIVE
        else:
            verdict = PROPERTY_PARTIAL if live else PROPERTY_UNCOVERED
        properties[prop] = {"status": verdict, "live": live,
                            "gaps": [c["number"] for c in counted
                                     if c["status"] != EVIDENCE_LIVE]}
    return {"placed": bool(grid.get("placed")), "config_version": version,
            "held_to": ("the concepts its grid band asks for" if required is not None
                        else "every applicable concept"),
            "concepts": concepts, "properties": properties}


__all__ = ["property_coverage"]
