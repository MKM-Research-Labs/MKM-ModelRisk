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
"""The FINOS AI Governance Framework catalogue (coding rule R1).

Held apart from ``_frameworks.py`` for two reasons. The mechanical one: forty-six
entries with their notes is more than that module has room for under R2. The real
one: FINOS is not shaped like the frameworks already there.

ISO 31000, COSO and BCBS 239 are clause lists, and each flattens into one sequence
of rows. FINOS is TWO catalogues, and they are different kinds of statement:

``FINOS_RISK_CATALOGUE``        Exposures a deployer carries. AIR-OP-004 is true of
                                every LLM in an estate whether or not anybody has
                                written it down. Evidenced from the RECORD.
``FINOS_MITIGATION_CATALOGUE``  Controls the institution runs, largely outside this
                                platform. Evidenced from a FILED DOCUMENT -- the
                                firm's own description of how it implements the
                                control, tagged with the references it covers.

They enter ``FRAMEWORK_COVERAGE`` as two separate entries rather than as one
framework with a catalogue dimension. The report already renders one table per
entry, so two names give two tables, two tallies and correct grouping in the
not-evidenced list with no structural change -- and, more to the point, a reader
can never mistake "we are exposed to prompt injection" for "here is our
prompt-injection control", which is exactly what merging them would invite.

**On the risk catalogue reading almost entirely Not evidenced.** It does, and that
is the honest position rather than a defect in this table. The risks are exposures
of generative and agentic systems, and the platform has no record type for one:
``config/governance/_ml.py`` scopes LLMs and agentic AI out by design. The three
measured rows below count the estate the platform DOES govern, and each says so.
The rest name what would have to exist. When an AI System record arrives, these
rows gain probes; until then a blank cell would teach an assessor nothing and a
green one would be false.

Reference numbering is FINOS's own (``AIR-OP-004`` and so on). Unlike ISO 31000,
the framework is openly published, so the references here can be checked against
the source rather than taken on trust: ``docs/finos/``.
"""
from __future__ import annotations

FINOS_RISKS = "FINOS AIGF -- Risk catalogue"
FINOS_MITIGATIONS = "FINOS AIGF -- Mitigation catalogue"

# The probe every mitigation row uses unless the platform evidences it from the
# record itself. It reads the FINOS shelf and asks whether any filed document names
# this row's reference -- so it is the one probe here that depends on which row it
# is being run for (``REF_PROBES`` in src.governance.completeness.framework).
EVIDENCE_PROBE = "finos_evidence"

# (reference, title, probe, note) -- the same four-tuple the other frameworks use,
# so nothing in the counting has to know which framework a row came from.
FINOS_RISK_CATALOGUE = (
    # --- Operational ---
    ("AIR-OP-004", "Hallucination and Inaccurate Outputs", "ai_grounding",
     "How the output is grounded, and the human who would catch it being wrong. "
     "Neither closes this alone. What is still not held is an evaluation record: "
     "a test flag says testing happened, not what it found."),
    ("AIR-OP-005", "Foundation Model Versioning", "ai_versioning",
     "The version pinned and the policy that keeps it pinned. Both, because a "
     "pinned version with no policy behind it is an accident rather than a "
     "control. The provider's own change notification is still not tracked."),
    ("AIR-OP-006", "Non-Deterministic Behaviour", "ai_determinism",
     "Output variability described, and what controls it."),
    ("AIR-OP-007", "Availability of Foundational Model", "ai_provider",
     "Provider and hosting recorded, so the dependency is at least visible and "
     "concentration across the estate is a query. Service levels and failover "
     "arrangements are not held."),
    ("AIR-OP-014", "Inadequate System Alignment", "ai_alignment",
     "The use case the system is meant to serve, bounded by the filtering that "
     "keeps it there."),
    ("AIR-OP-016", "Bias and Discrimination", "ai_fairness",
     "A recorded fairness and bias assessment. Counted over AI Systems only: the "
     "model and ML estate still carries no protected attributes and no subgroup "
     "performance, which is a gap this row does not report."),
    ("AIR-OP-017", "Lack of Explainability", "ai_explainability",
     "The explainability approach recorded against the system. An explanation of "
     "one particular output remains a runtime artefact the platform does not hold."),
    ("AIR-OP-018", "Model Overreach / Expanded Use", "identification",
     "Assumptions, limitations and weaknesses recorded -- where the bound on a "
     "record's use is written down and can be challenged."),
    ("AIR-OP-019", "Data Quality and Drift", "monitoring",
     "Review scheduled and not overdue, with the feeds and the monitoring approach "
     "recorded. This is the governance cycle around drift; nothing here detects "
     "drift, which the platform does not see."),
    ("AIR-OP-020", "Reputational Risk", "absent",
     "The three risk dimensions are structural. None of them is conduct or "
     "customer-facing exposure, so nothing carries this."),
    ("AIR-OP-028", "Multi-Agent Trust Boundary Violations", "ai_multi_agent",
     "Counted over multi-agent systems only -- a single agent has no boundary to "
     "violate, and scoring one against this would manufacture a gap nobody can "
     "close. Their tools are enumerated and their filtering described."),
    # --- Security. Nine of nine, and all for one reason. ---
    ("AIR-SEC-002", "Information Leaked to Vector Store", "absent",
     "No embedding store, cache or prompt log is a governed record."),
    ("AIR-SEC-008", "Tampering With the Foundational Model", "absent",
     "A vendor is a name in an admin list. No due diligence, contract reference, "
     "model card or provenance attestation is held against it."),
    ("AIR-SEC-009", "Data Poisoning", "absent",
     "Training data is recorded per train for the ML estate, but nothing records "
     "its integrity controls or a third-party feed's trust basis."),
    ("AIR-SEC-010", "Prompt Injection", "ai_guardrails",
     "The filtering standing between untrusted input and the model. The prompt "
     "itself is still not a governed artefact."),
    ("AIR-SEC-024", "Agent Action Authorization Bypass", "ai_agency",
     "Counted over agentic systems only. Each tool enumerated with what it may do "
     "and whether a human must approve, against a recorded oversight mode."),
    ("AIR-SEC-025", "Tool Chain Manipulation and Injection", "ai_agency",
     "Counted over agentic systems only. The tool list is what makes this "
     "answerable; validation of a call in flight is a runtime control, evidenced "
     "on the mitigation side."),
    ("AIR-SEC-026", "MCP Server Supply Chain Compromise", "absent",
     "External capability providers are not registered as dependencies."),
    ("AIR-SEC-027", "Agent State Persistence Poisoning", "absent",
     "No agent state exists to be described."),
    ("AIR-SEC-029", "Agent-Mediated Credential Discovery and Harvesting", "absent",
     "No agent credential boundary is recorded."),
    # --- Regulatory and Compliance ---
    ("AIR-RC-001", "Information Leaked To Hosted Model", "ai_egress",
     "What is sent for inference, and the contractual basis for it leaving. "
     "Residency is not held."),
    ("AIR-RC-022", "Regulatory Compliance and Oversight", "committee",
     "Committee sign-off recorded against the record, on the same route, with the "
     "same attributed append-only trail every other record takes. An AI System also "
     "carries its own EU AI Act classification and the basis for it; that is scored "
     "as a field by the completeness audit rather than given a row here, because "
     "FINOS has no such reference and inventing one would be a citation an assessor "
     "cannot check."),
    ("AIR-RC-023", "Intellectual Property (IP) and Copyright", "absent",
     "No licensing, training-provenance or output-ownership record."),
)

# Every mitigation is evidenced by a document on the FINOS shelf naming it, with one
# exception: system acceptance testing is a thing this platform already holds against
# the record itself, and reporting it as unevidenced because nobody had also written a
# paper about it would be the register disowning its own evidence.
FINOS_MITIGATION_CATALOGUE = (
    # --- Preventative ---
    ("AIR-PREV-002", "Data Filtering From External Knowledge Bases", EVIDENCE_PROBE, ""),
    ("AIR-PREV-003", "User/App/Model Firewalling/Filtering", EVIDENCE_PROBE, ""),
    ("AIR-PREV-005", "System Acceptance Testing", "acceptance",
     "Unit, integration and benchmark testing recorded against the record, with the "
     "evidence filed under the Testing categories. The one mitigation the platform "
     "evidences from the register rather than from a filed description."),
    ("AIR-PREV-006", "Data Quality & Classification/Sensitivity", EVIDENCE_PROBE,
     "The platform holds the feeds a record draws on, but not their sensitivity "
     "classification, so the filed description carries this on its own."),
    ("AIR-PREV-007", "Legal and Contractual Frameworks for AI Systems", EVIDENCE_PROBE,
     "Artefact shelves already hold policies and terms of reference; contracts and "
     "supplier due diligence are not modelled, so this is the filed description."),
    ("AIR-PREV-008", "Quality of Service (QoS) and DDoS Prevention for AI Systems",
     EVIDENCE_PROBE, ""),
    ("AIR-PREV-010", "AI Model Version Pinning", EVIDENCE_PROBE,
     "A pinned version belongs on the record as well as in a description; there is "
     "no field for one until an AI System record exists."),
    ("AIR-PREV-012", "Role-Based Access Control for AI Data", EVIDENCE_PROBE, ""),
    ("AIR-PREV-014", "Encryption of AI Data at Rest", EVIDENCE_PROBE, ""),
    ("AIR-PREV-017", "AI Firewall Implementation and Management", EVIDENCE_PROBE, ""),
    ("AIR-PREV-018", "Agent Authority Least Privilege Framework", EVIDENCE_PROBE, ""),
    ("AIR-PREV-019", "Tool Chain Validation and Sanitization", EVIDENCE_PROBE, ""),
    ("AIR-PREV-020", "MCP Server Security Governance", EVIDENCE_PROBE, ""),
    ("AIR-PREV-022", "Multi-Agent Isolation and Segmentation", EVIDENCE_PROBE, ""),
    ("AIR-PREV-023", "Agentic System Credential Protection Framework", EVIDENCE_PROBE, ""),
    # --- Detective ---
    ("AIR-DET-001", "AI Data Leakage Prevention and Detection", EVIDENCE_PROBE, ""),
    ("AIR-DET-004", "AI System Observability", EVIDENCE_PROBE,
     "Operational failure events are recorded against a record after the fact. "
     "Runtime telemetry is not something the platform sees."),
    ("AIR-DET-009", "AI System Alerting and Denial of Wallet (DoW) / Spend Monitoring",
     EVIDENCE_PROBE, ""),
    ("AIR-DET-011", "Human Feedback Loop for AI Systems", EVIDENCE_PROBE,
     "The challenge thread is attributed, append-only human feedback -- but on the "
     "governance record, not on the system's outputs. Counting it here would be "
     "answering a different question than the one asked."),
    ("AIR-DET-013", "Providing Citations and Source Traceability for AI-Generated "
     "Information", EVIDENCE_PROBE, ""),
    ("AIR-DET-015", "Using Large Language Models for Automated Evaluation "
     "(LLM-as-a-Judge)", EVIDENCE_PROBE, ""),
    ("AIR-DET-016", "Preserving Source Data Access Controls in AI Systems",
     EVIDENCE_PROBE, ""),
    ("AIR-DET-021", "Agent Decision Audit and Explainability", EVIDENCE_PROBE,
     "The platform keeps exactly the attributed, append-only log this asks for, "
     "over governance events. The mechanism transfers; the subject does not exist "
     "yet."),
)

# Printed under each FINOS table, before its rows. The other frameworks share one
# basis paragraph because they are all clause lists read the same way; these two are
# read differently from each other, and a reader who does not know that will
# misread the mitigation table as a claim about controls operating.
FINOS_RISK_NOTE = (
    "These are exposures a deployer carries, evidenced from the register. The "
    "platform has no record type for a generative or agentic system, so most rows "
    "name what would have to exist rather than counting anything. Where a row is "
    "counted, it is counted over the models and ML Applications on the register."
)
FINOS_MITIGATION_NOTE = (
    "These are controls the institution runs, most of them outside this platform. "
    "A row is evidenced by a document filed on the FINOS shelf naming its "
    "reference, and the evidence names that document and the date it was filed. "
    "That is a record that the control has been DESCRIBED, which is what a "
    "governance register can attest; it is not a statement that the control was "
    "found to be operating."
)

# Keyed by framework name, for the general FRAMEWORK_NOTES mechanism next door. The
# content lives here with the tables it qualifies: an adopter re-wording one of these
# is re-wording FINOS, and should not have to go looking in another module for it.
FINOS_NOTES = {FINOS_RISKS: FINOS_RISK_NOTE, FINOS_MITIGATIONS: FINOS_MITIGATION_NOTE}

# The two catalogues in the order the report shows them: exposures first, then what
# the institution does about them.
FINOS_COVERAGE = ((FINOS_RISKS, FINOS_RISK_CATALOGUE),
                  (FINOS_MITIGATIONS, FINOS_MITIGATION_CATALOGUE))

# What a document on the FINOS shelf can be tagged with, ready for the upload form.
# Derived here rather than in the API so the picker and the coverage table cannot
# come to disagree about which references exist: edit the catalogue above and both
# follow. Only mitigations -- a risk is an exposure, and no filed paper evidences one.
FINOS_MITIGATION_REFS = tuple(
    {"ref": ref, "title": title} for ref, title, _probe, _note in
    FINOS_MITIGATION_CATALOGUE)

__all__ = ["FINOS_RISKS", "FINOS_MITIGATIONS", "FINOS_RISK_CATALOGUE",
           "FINOS_MITIGATION_CATALOGUE", "FINOS_COVERAGE", "FINOS_NOTES",
           "FINOS_MITIGATION_REFS", "EVIDENCE_PROBE"]
