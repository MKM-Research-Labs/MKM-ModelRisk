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
"""The AI System record: field metadata and collections (coding rule R1).

An AI System is *a deployed use of a generative or agentic model*. It is the third
record type in the same family, and it is built on exactly the reasoning that built
the second (see ``_ml_application.py``):

**The governance half uses THE SAME FIELD NAMES A MODEL USES.** Not similar names --
the same ones. The clause probes in ``src.governance.completeness.framework`` are
field-name lambdas over one population: ``analysis`` reads tier/materiality/
complexity, ``accountability`` reads owner, ``independence`` reads peer_reviewer
against owner, ``criteria`` reads division, ``monitoring`` reads next_review_date.
Match the names and every one of them counts AI Systems with no change at all.
Diverge and each grows a per-type branch.

**The AI half** is what neither a model nor an ML Application has a place for, and
each field here exists because a named FINOS risk turns on it. That is the test a
field had to pass to be in this list -- not "an AI system has one of these" but
"a row of the coverage table cannot be answered without it":

``provider`` / ``foundation_model``   AIR-OP-005, AIR-SEC-008
``pinned_version`` / ``version_policy``  AIR-OP-005, AIR-PREV-010
``hosting`` / ``data_egress``         AIR-RC-001, AIR-SEC-002
``deployment_pattern``                AIR-OP-014, AIR-OP-028, the agentic controls
``human_oversight``                   AIR-OP-018, AIR-RC-022
``output_variability``                AIR-OP-006
``grounding``                         AIR-OP-004
``explainability_approach``           AIR-OP-017
``guardrails``                        AIR-SEC-010, AIR-PREV-003, AIR-PREV-017
``fairness_assessments`` (collection)  AIR-OP-016 -- one row per attribute assessed.
                                   A scalar "fairness approach" field lived here
                                   first and was removed when the collection
                                   arrived: two places to answer one question is
                                   two answers free to disagree.
``eu_ai_act_class``                   AIR-RC-022
``agent_tools`` (collection)          AIR-SEC-024/025, AIR-PREV-018/019

What this record deliberately does NOT carry:

``estimator`` / ``training_runs``  Nobody in the firm fitted this. Provenance is the
                                   provider and the version, not a train.
``validation_questions``           It has its own questionnaire, seeded from its own
                                   admin list -- not one of the seven ML-specific
                                   questions is answerable about a model the firm
                                   did not train.
``dependencies``                   Phase 3, with the Product binding.
"""
from __future__ import annotations

from config.governance._ai_regimes import DEFAULT_MARKETS, MARKETS_LIST
from config.governance._review import REVIEW_FIELD_SPECS
from config.governance._ai_complexity import (AI_COMPLEXITY_FIELD_SPECS,
                                              AI_COMPLEXITY_REGISTER_OPTIONAL)

from config.governance._ai import (AI_SYSTEM_QUESTION_LIST, DATA_EGRESS_CLASSES,
                                   DEPLOYMENT_PATTERNS, EU_AI_ACT_CLASSES,
                                   FOUNDATION_MODEL_LIST, HOSTING_MODES,
                                   HUMAN_OVERSIGHT_MODES, VERSION_POLICIES)
from config.governance._collections import (COLLECTION_SPECS, EVALUATIONS_COLLECTION,
                                            FAIRNESS_COLLECTION,
                                            MONITORING_COLLECTION)
from config.governance._inventory import (VALID_COMPLEXITY,
                                          VALID_LIFECYCLE_STAGES, VALID_MATERIALITY,
                                          VALID_RAG_RATINGS, VALID_REVIEW_FREQUENCIES,
                                          VALID_REVIEW_STATUSES,
                                          VALID_VALIDATION_STATUSES,
                                          VALIDATION_STATUS_LIST)
from config.governance._review import REVIEW_COLLECTION_SPECS
from config.governance._signoff_collections import SIGNOFF_COLLECTION_SPECS

AI_SYSTEM_ID_PREFIX = "AIS"


AI_SYSTEM_FIELD_SPECS = {
    # --- Organisation. Same names as a model's; ``division`` is what the criteria
    #     probe reads and what routes the record to its MRC. ---
    "division": {"label": "Division", "type": "text", "group": "Organisation",
                 "reference": "division"},
    "line_of_business": {"label": "Line of Business", "type": "text",
                         "group": "Organisation", "reference": "line_of_business"},
    # What the record is FOR, as this division's MRC has carved its estate up --
    # a different question from ``type``, which is what it IS. ``options`` is empty
    # because there is no firm-wide list: a division's groups come from its ratified
    # policy and are resolved per record (config/governance/_functional_groups).
    "functional_group": {"label": "Functional Group", "type": "choice", "options": (),
                         "group": "Organisation"},
    "repo_location": {"label": "Repository location", "type": "text",
                      "group": "Organisation"},
    "codebase": {"label": "Codebase", "type": "text", "group": "Organisation",
                 "reference": "codebase"},
    # --- Identity ---
    "name": {"label": "Name", "type": "text", "group": "Identity"},
    "short_name": {"label": "Short name", "type": "text", "group": "Identity"},
    "description": {"label": "Description", "type": "textarea", "group": "Identity"},
    # --- The AI half: what it is built on ---
    # First, because every other answer is judged against it: a guardrail means
    # nothing until somebody has said what the system is for.
    "use_case": {"label": "Use case", "type": "textarea", "group": "The AI system"},
    # Strict, like a model's ``type``: a record may not name a model the institution
    # has never approved. That is the whole point of the list.
    "foundation_model": {"label": "Foundation model", "type": "text",
                         "group": "The AI system", "reference": FOUNDATION_MODEL_LIST,
                         "strict_reference": True},
    "provider": {"label": "Provider", "type": "text", "group": "The AI system",
                 "reference": "vendor", "strict_reference": True},
    # AIR-OP-005 is not "which version" but "can it change without telling us". Both
    # are recorded because both are asked: the version pinned, and the policy that
    # says whether it stays pinned.
    "pinned_version": {"label": "Pinned version", "type": "text", "group": "The AI system"},
    "version_policy": {"label": "Version policy", "type": "choice",
                       "options": VERSION_POLICIES, "group": "The AI system"},
    "hosting": {"label": "Hosting", "type": "choice", "options": HOSTING_MODES,
                "group": "The AI system"},
    "deployment_pattern": {"label": "Deployment pattern", "type": "choice",
                           "options": DEPLOYMENT_PATTERNS, "group": "The AI system"},
    # Where the system is placed on the market or used, which is what regulatory
    # regimes turn on — and deliberately not where the team sits: a London desk serving
    # EU customers is in scope of the EU AI Act, and a field asking for the firm's
    # domicile would have said otherwise. Multi-valued, because a system usually serves
    # more than one.
    "markets": {"label": "Markets served", "type": "multichoice",
                "options": DEFAULT_MARKETS, "reference": MARKETS_LIST,
                "group": "Exposure"},
    # The two parameters that change what the system DOES without changing what it
    # is. A pinned model with different sampling parameters is a different system in
    # every way a reviewer cares about, and neither was recorded — so a configuration
    # snapshot taken before these existed could not have said why two runs differed.
    #
    # Free text rather than typed: sampling parameters differ by provider (temperature
    # and top_p on one, a reasoning-effort setting on another), and a fixed schema of
    # ours would be wrong for the next model released.
    "sampling_params": {"label": "Sampling parameters", "type": "textarea",
                        "group": "The AI system"},
    # The order of precedence between system prompt, developer instruction, retrieved
    # content and user input. What an injection attack attacks, and the thing a
    # reviewer needs in order to say whether the attack would work.
    "instruction_hierarchy": {"label": "Instruction hierarchy", "type": "textarea",
                              "group": "The AI system"},
    # --- Exposure ---
    "data_egress": {"label": "Data sent for inference", "type": "choice",
                    "options": DATA_EGRESS_CLASSES, "group": "Exposure"},
    "data_egress_basis": {"label": "Contractual basis",
                          "type": "textarea", "group": "Exposure"},
    "eu_ai_act_class": {"label": "EU AI Act classification", "type": "choice",
                        "options": EU_AI_ACT_CLASSES, "group": "Exposure"},
    "eu_ai_act_rationale": {"label": "Classified by",
                            "type": "textarea", "group": "Exposure"},
    # --- Controls. Prose rather than flags: what a reviewer needs is the
    #     arrangement described well enough to disagree with, and a Yes/No on
    #     "guardrails" would be the least informative field in the record. ---
    "human_oversight": {"label": "Human oversight", "type": "choice",
                        "options": HUMAN_OVERSIGHT_MODES, "group": "Controls"},
    "guardrails": {"label": "Guardrails", "type": "textarea",
                   "group": "Controls"},
    "grounding": {"label": "Grounding", "type": "textarea",
                  "group": "Controls"},
    "output_variability": {"label": "Output variability",
                           "type": "textarea", "group": "Controls"},
    "explainability_approach": {"label": "Explainability approach", "type": "textarea",
                                "group": "Controls"},
    # --- Classification. The same three dimensions, bands and heatmap a model
    #     carries, so an AI System is challenged on the same terms. ---
    "tier": {"label": "Tier", "type": "tier", "group": "Classification"},
    "tier_rationale": {"label": "Tier rationale", "type": "text", "group": "Classification"},
    "materiality": {"label": "Materiality", "type": "choice", "options": VALID_MATERIALITY,
                    "group": "Classification"},
    "materiality_rationale": {"label": "Materiality rationale", "type": "text",
                              "group": "Classification"},
    "complexity": {"label": "Complexity", "type": "choice", "options": VALID_COMPLEXITY,
                   "group": "Classification"},
    "complexity_rationale": {"label": "Complexity rationale", "type": "text",
                             "group": "Classification"},
    "rating_rationale": {"label": "Rating rationale", "type": "text",
                         "group": "Classification"},
    "rag_rating": {"label": "RAG rating", "type": "choice", "options": VALID_RAG_RATINGS,
                   "group": "Classification"},
    # The SR 26-2 boundary and the AI complexity axis (spec v0.5 §2, AIGov edition).
    **AI_COMPLEXITY_FIELD_SPECS,
    # --- Governance. ``owner`` and ``peer_reviewer`` are what the accountability
    #     and independence probes read; independence compares the two. ---
    "owner": {"label": "Owner", "type": "text", "group": "Governance", "reference": "people"},
    "peer_reviewer": {"label": "Peer reviewer", "type": "text", "group": "Governance",
                      "reference": "people"},
    "status": {"label": "Status", "type": "text", "group": "Governance"},
    "review_status": {"label": "Review status", "type": "choice",
                      "options": VALID_REVIEW_STATUSES, "group": "Governance"},
    # From the division's ratified stage list, resolved by the console per record --
    # see the model inventory's spec for the whole of the reasoning. ``options`` is the
    # catalogue default, shown until the registry loads.
    "lifecycle_stage": {"label": "Lifecycle stage", "type": "choice",
                        "options": VALID_LIFECYCLE_STAGES, "group": "Governance"},
    "validation_status": {"label": "Validation status", "type": "choice",
                          "options": VALID_VALIDATION_STATUSES, "group": "Governance",
                          "reference": VALIDATION_STATUS_LIST},
    "version": {"label": "Version", "type": "text", "group": "Governance"},
    "review_frequency": {"label": "Review frequency", "type": "choice",
                         "options": VALID_REVIEW_FREQUENCIES, "group": "Governance"},
    # --- Review dates. ``next_review_date`` is the monitoring probe. ---
    "last_review_date": {"label": "Last review", "type": "date", "group": "Review dates"},
    "validation_date": {"label": "Validation date", "type": "date", "group": "Review dates"},
    "recertification_date": {"label": "Recertification", "type": "date",
                             "group": "Review dates"},
    "next_review_date": {"label": "Next review", "type": "date", "group": "Review dates"},
    "mrc_signoff_date": {"label": "MRC sign-off", "type": "date", "group": "Review dates"},
    "mrc_signoff_meeting": {"label": "MRC sign-off meeting", "type": "text",
                            "group": "Review dates"},
    # --- Review. The workflow's own fields, shared with the model inventory and
    # the other governed record types (config/governance/_review.py). This record
    # type is reviewed through the same seven stages a model is, so it records the
    # same things about why the review is happening and what its scope is.
    **REVIEW_FIELD_SPECS,
    # --- Monitoring ---
    "monitoring_approach": {"label": "Monitoring approach", "type": "textarea",
                            "group": "Monitoring"},
    # --- Testing. The same three flags a model carries -- and the flags the FINOS
    #     acceptance-testing mitigation is evidenced from. ---
    "unit_tests": {"label": "Unit tests", "type": "choice", "options": ("Yes", "No"),
                   "group": "Testing"},
    "integration_tests": {"label": "Integration tests", "type": "choice",
                          "options": ("Yes", "No"), "group": "Testing"},
    "benchmark_tests": {"label": "Benchmark tests", "type": "choice",
                        "options": ("Yes", "No"), "group": "Testing"},
}

# Short on purpose, like the ML Application's: a record is created before most of it
# is known, and a form demanding the narrative up front is answered with placeholders.
# What is missing afterwards is a completeness finding, which is where somebody acts
# on it. ``deployment_pattern`` earns its place here because it decides which of the
# agentic risks apply at all, and a record whose pattern is unknown cannot be triaged.
AI_SYSTEM_REGISTER_FIELDS = ("name", "division", "owner", "use_case", "deployment_pattern")

# Shown on the register form but NOT required, which is the distinction
# ``AI_SYSTEM_REGISTER_FIELDS`` alone could not make: for this record type that tuple is the
# MANDATORY set -- ``decide_register`` refuses a registration missing any of it.
#
# Line of Business is the field that forced the split. Without it a record can only
# ever route to its DIVISION's committee, because ``committee_at_levels`` skips the
# Line of Business level when the record names none; a model has carried it since the
# beginning and these two did not. It cannot be mandatory, though: a division may have
# no lines of business defined, and a record genuinely governed at division level has
# no honest answer to give.
AI_SYSTEM_REGISTER_OPTIONAL = ("line_of_business",) + AI_COMPLEXITY_REGISTER_OPTIONAL
from config.governance._ai_system_collections import (  # noqa: E402
    AGENT_TOOLS_COLLECTION, AI_REVIEW_QUESTIONS_COLLECTION,
    AI_SYSTEM_COLLECTION_SPECS)

AI_SYSTEM_EDITABLE_FIELDS = tuple(AI_SYSTEM_FIELD_SPECS.keys())
AI_SYSTEM_FIELD_CHOICES = {
    key: spec["options"] for key, spec in AI_SYSTEM_FIELD_SPECS.items()
    if spec["type"] == "choice"
}

__all__ = ["AI_SYSTEM_ID_PREFIX", "AI_SYSTEM_FIELD_SPECS", "AI_SYSTEM_COLLECTION_SPECS",
           "AI_SYSTEM_REGISTER_FIELDS", "AI_SYSTEM_REGISTER_OPTIONAL", "AI_SYSTEM_EDITABLE_FIELDS",
           "AI_SYSTEM_FIELD_CHOICES", "AI_REVIEW_QUESTIONS_COLLECTION",
           "AGENT_TOOLS_COLLECTION", "AI_SYSTEM_QUESTION_LIST"]


# --- What a configuration snapshot captures -----------------------------------
# The fields whose values, taken together, are what produced the system's behaviour on
# a given day. Named here rather than inferred, because "what counts as the
# configuration" is a governance judgement an institution may disagree with — and
# because a snapshot that quietly widened would make two snapshots incomparable.
#
# The test is reproducibility: if changing a field could make the same input give a
# different answer, it belongs. That takes in the model and how it is pinned, the
# parameters it is sampled with, what it is told and in what order, what grounds it,
# and what stands between it and its consumer. It leaves out the record's governance
# half — owner, tier, review dates — which describe how the system is GOVERNED rather
# than how it behaves, and which change for reasons that have nothing to do with it.
CONFIGURATION_FIELDS = (
    "foundation_model", "provider", "pinned_version", "version_policy",
    "hosting", "deployment_pattern", "sampling_params", "instruction_hierarchy",
    "grounding", "guardrails", "human_oversight", "output_variability",
)

__all__ = list(__all__) + ["CONFIGURATION_FIELDS"]
