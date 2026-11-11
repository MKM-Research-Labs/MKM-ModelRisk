# Design: the Model Review template

**Status:** Proposed 2026-11-11. Report fixes (stage numbering, remediation columns,
challenge summary) built; sections A, B and E are not.
**Area:** Model inventory / Review & Validation / MRC
**Builds on:** [review-workflow.md](review-workflow.md)

## Decision

A model review has one canonical set of nine questions: **the platform's
`SR262_QUESTIONS`** (`config/governance/_inventory.py`). The core documentation is where
the owner *answers* them. The review is where the reviewer gives a *verdict* on each
answer. The review registers (assumptions, weaknesses, limitations, monitoring,
remediation) are the evidence behind those verdicts. So no question is asked twice: once
by the document and again by the review.

## Why a decision was needed

On 2026-11-11 the estate's documentation used four different sets of nine questions:

| Where | The nine |
|---|---|
| Platform, seeded on every model | Ronseal, Accuracy & Stability, Resource Usage, Override Controls, Data Quality, Assumptions, Limitations, Benchmarking, Independent Validation |
| MKM-MP-001, MKM-PR-001, MKM-SG-001 | Q1–4 as the platform; then Output Consumption, Model Chaining, Weaknesses, Monitoring, Overall Risk |
| MKM-DE-001 | Ronseal, Methodology, Alternative Methods, Assumptions, Data Quality, Model Chaining, Weaknesses, Monitoring, Overall Risk |
| MKM-SS-001 v3.0, MKM-SP-001 v2.0 | Purpose, Conceptual Soundness, Data Quality, Developmental Evidence, Outcomes Analysis, Ongoing Monitoring, Benchmarking, Implementation, Overall Risk |

MKM-DD-001, MKM-EF-001 and MKM-FPO-001 have no validation-questions section at all.
None of the documents matches the platform's set in full. So a reviewer's verdict in
the console and the owner's answer in the PDF could be about different questions.

## The template

Sections in the order the report prints them. The seven workflow stages are unchanged.

### A. Identification — *not yet built*

The record and its name, the **version under review** (`version`), the documentation
version, owner, reviewer, why this review is happening, scope, expected completion,
tier, materiality, complexity, the **current risk rating** (`rag_rating`), and the date
and opinion of the last signed review. The report prints only the record, owner,
reviewer, trigger and sign-off today. A review that doesn't name the version it
reviewed can't be checked against the version that went live.

### B. Documents reviewed — *not yet built*

The pack the reviewer read: each document and its version, for example "documentation
v3.0, Wolfram benchmark v0.2". Today the Preliminary documents stage prints only the
scope text, so the report never says which documents the review was based on.

### Challenge in summary — *built*

The number of challenges raised, answered and still open, in total and by stage. It is
printed ahead of the stages, so the full record of notes reads as support for a stated
number. Promised in review-workflow.md and missing until now.

### C. The nine questions

For each question: the owner's status and rationale, with a **section reference to the
documentation** where it is answered; the reviewer's verdict and comment; and the stage
whose register holds the evidence.

| # | Question | Evidence lives in |
|---|---|---|
| 1 | Ronseal Test | Limitations of use (what it must not be used for); the documentation's purpose and scope |
| 2 | Accuracy & Stability | Sensitivities and backtests in the documentation; the benchmark |
| 3 | Resource Usage | The documentation's computational-complexity section |
| 4 | Override Controls | The documentation; any compensating control on a limitation |
| 5 | Data Quality | The model's data sources and lineage |
| 6 | Assumptions | **The Assumptions stage** (it runs before the questions for this reason) |
| 7 | Limitations | **The Limitations and Monitoring stages** |
| 8 | Benchmarking | The benchmark document (for example the Wolfram oracle) |
| 9 | Independent Validation | This review itself, and any external validation on file |

For questions 6 and 7 the verdict and the stage are one judgement: a reviewer who agrees
the Assumptions stage and then challenges question 6 has contradicted themselves.

### D. Findings

Weaknesses, Limitations of use, Monitoring and Remediation, as today. Proposed: each
weakness and limitation gets a **severity** and a link back to the question it came
from, and each remediation item links to the finding it closes. That way the committee
can follow a challenged question through to the work that answers it.

The Remediation table now prints the register's own fields (finding, owner, priority,
due date, status). It used to print an "Action" column from a field the register has
never had, so the column was blank on every report.

### E. The reviewer's opinion — *not yet built*

The platform's set has **no "overall risk" question**, unlike all three document sets.
So the review has to give the conclusion itself:

- **Opinion:** *Fit for use* / *Fit for use with conditions* / *Not fit for use*.
- **Conditions:** remediation items, by id, that the opinion depends on.
- **Recommended rating:** the reviewer's RAG. The MRC still decides the rating; this is
  what the reviewer advises it to decide.

These are captured at sign-off, next to the final commentary. They join the
append-only `review_signoffs` row, so an opinion can't be rewritten after the fact.

### F. Record of challenge and attestation

The full record of notes under each stage, then the final commentary and who signed it
and when. Unchanged.

## Consequences

- **Reissue the core documents to the platform's nine.** As each document next goes
  through a version change, its validation-questions section is rewritten to the
  platform's wording and order, and the answers it no longer has a question for move
  to where the template now puts them:
  - **Overall Risk** goes to the reviewer's opinion.
  - **Weaknesses** and **Monitoring** go to their stages.
  - **Model Chaining** goes to the model's dependencies register.
  - **Output Consumption** goes to the use case.

  The three documents with no such section get one.
- **Existing models keep the questions they were registered with.** The questions are
  copied onto a record at registration and never rewritten. This changes nothing about
  what is seeded, only what the documents answer.
- **The opinion is a new sign-off input,** so the sign-off endpoint, its form and the
  report change together. It is not a new workflow stage.

## Build order

1. ~~Report: number stages from 1, the remediation columns, the challenge summary.~~ Done.
2. Identification and documents reviewed in the report (A, B). Report-only; the data is
   already on the record.
3. The reviewer's opinion at sign-off (E): config, endpoint, form, report.
4. Severity and question links on findings (D).
5. Document reissues, one per model as it next changes version.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
