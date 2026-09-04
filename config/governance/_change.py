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
"""The four-tier change taxonomy, and what depth of revalidation each tier calls for.

Moody's classes -- Administrative, Bounded, Measurement, Material -- shared by both
workflows, which is the whole point of the engine: a change to an ML Application and a
change to an AI System are classified by the same rules and differ only in what the
resulting tier makes somebody do. That difference lives in ``REVALIDATION_DEPTH``,
keyed by ``(change_class, workflow)``, and nowhere else.

Everything here is data (R1). No tier name, depth or trigger appears as a literal in
``src/`` -- an institution whose Bounded changes require more than ours edits this file,
and the one-way ModelOne fork means anything that leaks into ``src/`` is permanent
divergence rather than a configuration difference.

**Ordering carries meaning.** ``CHANGE_CLASSES`` is ascending severity, and the engine
relies on it: a change touching several fields takes the most severe tier any one of
them triggers. Reorder the tuple and you change every classification in the estate.
"""
from __future__ import annotations

from typing import Any

# --- The taxonomy ------------------------------------------------------------

# Ascending severity. See the module docstring before reordering.
CHANGE_CLASSES: tuple[str, ...] = (
    "Administrative", "Bounded", "Measurement", "Material",
)

# What a change is classified as when nothing it touches triggers anything higher.
# Administrative rather than Material: the register exists to draw attention to the
# changes that matter, and a default of "most severe" trains people to ignore it.
DEFAULT_CHANGE_CLASS = "Administrative"

CHANGE_CLASS_NOTES: dict[str, str] = {
    "Administrative": "Descriptive or custodial. Recorded, not revalidated.",
    "Bounded": "Movement within an envelope already approved for this record.",
    "Measurement": "Changes how the record is measured, evaluated or monitored, so "
                   "past evidence no longer speaks to the current configuration.",
    "Material": "Changes what the record is or does. The approval it holds was given "
                "for something else.",
}

# --- The two workflows -------------------------------------------------------

# The AI and ML processes are deliberately separate and share utilities rather than
# merging (spec Part B/Part C). The engine is one of those shared utilities; the depth
# each tier calls for is where the two part company.
WORKFLOW_ML = "ml"
WORKFLOW_AI = "ai"
CHANGE_WORKFLOWS: tuple[str, ...] = (WORKFLOW_ML, WORKFLOW_AI)

WORKFLOW_LABELS: dict[str, str] = {
    WORKFLOW_ML: "Model / ML Application",
    WORKFLOW_AI: "AI System",
}

# Which workflow a record type is governed by. The keys are ``Subject.kind`` from
# ``src/web/_signoff_subject.py`` -- the record-type vocabulary the committee routing
# already uses -- rather than a second spelling of the same five nouns.
SUBJECT_WORKFLOWS: dict[str, str] = {
    "model": WORKFLOW_ML,
    "ml_application": WORKFLOW_ML,
    "ai_system": WORKFLOW_AI,
}

# --- What each tier costs, per workflow --------------------------------------

# The vocabulary of revalidation depths. A depth is what somebody must actually do;
# the label is what the screen says.
REVALIDATION_DEPTHS: dict[str, str] = {
    "record_only": "Record the change. No revalidation.",
    "targeted": "Revalidate the affected components against the existing approval.",
    "monitoring_recalibration": "Rebaseline the monitoring measures and thresholds "
                                "before the next monitoring cycle is read.",
    "evaluation_stack_revalidation": "Revalidate the evaluation stack -- benchmark, "
                                     "judge and rubric -- before its scores are "
                                     "trusted again.",
    "validation_pack_refresh": "Refresh the validation pack and put it back through "
                               "review.",
    "rebaseline": "Re-baseline the system: configuration snapshot, variability "
                  "envelope and trigger thresholds, then back to the committee.",
}

# The 4x2 matrix. Total by construction -- every class resolves a depth for every
# workflow -- and a test asserts it stays that way, because a missing cell is a change
# that classifies successfully and then tells nobody what to do about it.
REVALIDATION_DEPTH: dict[tuple[str, str], str] = {
    ("Administrative", WORKFLOW_ML): "record_only",
    ("Administrative", WORKFLOW_AI): "record_only",
    ("Bounded", WORKFLOW_ML): "targeted",
    ("Bounded", WORKFLOW_AI): "targeted",
    ("Measurement", WORKFLOW_ML): "monitoring_recalibration",
    ("Measurement", WORKFLOW_AI): "evaluation_stack_revalidation",
    ("Material", WORKFLOW_ML): "validation_pack_refresh",
    ("Material", WORKFLOW_AI): "rebaseline",
}


# --- What moving implies which tier ------------------------------------------

# Ordered, most severe first, and the FIRST rule matching a given field decides that
# field's tier -- so a field named twice takes the more severe reading rather than
# whichever rule happens to sit lower in the tuple.
#
# ``applies_to`` empty means every record type. Field names are the real keys from
# ``MODEL_FIELD_SPECS``, ``ML_APPLICATION_FIELD_SPECS`` and ``AI_SYSTEM_FIELD_SPECS``;
# a name here that no record type has is dead data, and the audit's own field checks
# are what catch it.
#
# Anything not named below is ``DEFAULT_CHANGE_CLASS``. That is deliberate rather than
# lazy: names, descriptions, owners, roles, repository locations, the dated fields and
# every ``*_rationale`` are administrative, and enumerating them here would only create
# a second list to keep in step with the field specs.
CHANGE_TRIGGERS: tuple[dict[str, Any], ...] = (
    {
        "change_class": "Material",
        "applies_to": (),
        "fields": ("tier", "materiality", "complexity"),
        "artifacts": ("validation_pack", "training_data"),
        "note": "A re-rating changes the governance the record owes, so the approval "
                "it holds was granted against a different set of obligations.",
    },
    {
        "change_class": "Material",
        "applies_to": ("model",),
        "fields": ("type", "category", "methodology", "source_module", "vendor"),
        "artifacts": (),
        "note": "What the model is. A methodology change is a different model wearing "
                "the same id.",
    },
    {
        "change_class": "Material",
        "applies_to": ("ml_application",),
        "fields": ("estimator", "methodology", "source_module", "vendor"),
        "artifacts": (),
        "note": "Swapping the estimator is the ML Application equivalent of swapping "
                "a model's methodology.",
    },
    {
        "change_class": "Material",
        "applies_to": ("ai_system",),
        "fields": ("foundation_model", "provider", "hosting", "deployment_pattern",
                   "data_egress", "eu_ai_act_class", "human_oversight", "guardrails",
                   "grounding"),
        "artifacts": (),
        "note": "The system's identity and its containment. Moving any of these "
                "invalidates the baseline the committee approved -- a swapped "
                "foundation model behind unchanged guardrails is still a new system.",
    },
    {
        "change_class": "Measurement",
        "applies_to": (),
        "fields": ("monitoring_approach", "validation_status", "review_frequency",
                   "unit_tests", "integration_tests", "benchmark_tests"),
        "artifacts": ("benchmark_set", "judge_model", "rubric", "finos_taxonomy"),
        "note": "How the record is measured. Past evidence was produced by a "
                "different instrument. The FINOS taxonomy sits here on the spec's own "
                "instruction: a version bump is a Measurement-class change against "
                "the mapping engine, not a Material one against every mapped record.",
    },
    {
        "change_class": "Measurement",
        "applies_to": ("ai_system",),
        "fields": ("pinned_version", "output_variability", "explainability_approach"),
        "artifacts": (),
        "note": "A pinned-version bump keeps the system but not its scores -- the "
                "same treatment §9.6 gives a judge model's version bump.",
    },
    {
        "change_class": "Measurement",
        "applies_to": ("ml_application",),
        "fields": ("estimator_version",),
        "artifacts": (),
        "note": "The direct analogue of an AI System's pinned version, and classified "
                "the same way for the same reason.",
    },
    {
        "change_class": "Bounded",
        "applies_to": (),
        "fields": ("division", "line_of_business", "status", "lifecycle_stage",
                   "version", "review_scope", "review_trigger"),
        "artifacts": (),
        "note": "Movement inside the approved envelope. ``division`` is here rather "
                "than higher because it re-homes the record under another division's "
                "risk policy and MRC -- consequential, and bounded by both policies "
                "already being ratified.",
    },
    {
        "change_class": "Bounded",
        "applies_to": ("ai_system",),
        "fields": ("version_policy", "data_egress_basis", "use_case"),
        "artifacts": (),
        "note": "``version_policy`` governs how future versions arrive; changing it "
                "does not itself move the system.",
    },
)


def workflow_for(subject_type: str) -> str | None:
    """Which workflow governs a record type, or ``None`` if it is not one we classify.

    ``None`` rather than a default: a Product or a handoff has no revalidation depth to
    resolve, and silently filing it under the ML workflow would produce a confident
    answer to a question nobody asked.
    """
    return SUBJECT_WORKFLOWS.get(subject_type)


def revalidation_depth_for(change_class: str, workflow: str) -> str:
    """The depth a tier calls for in a workflow. Raises on a cell that does not exist."""
    try:
        return REVALIDATION_DEPTH[(change_class, workflow)]
    except KeyError:  # pragma: no cover - the totality test makes this unreachable
        raise KeyError(f"no revalidation depth for {change_class!r} in {workflow!r}")


__all__ = [
    "CHANGE_CLASSES", "CHANGE_CLASS_NOTES", "CHANGE_TRIGGERS", "CHANGE_WORKFLOWS",
    "DEFAULT_CHANGE_CLASS", "REVALIDATION_DEPTH", "REVALIDATION_DEPTHS",
    "SUBJECT_WORKFLOWS", "WORKFLOW_AI", "WORKFLOW_LABELS", "WORKFLOW_ML",
    "revalidation_depth_for", "workflow_for",
]
