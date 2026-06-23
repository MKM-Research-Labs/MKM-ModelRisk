# MKM-ModelRisk — User Guide

This guide walks through every screen and feature of the MKM-ModelRisk
governance console. For installation, see the [README](../README.md).

---

## Contents

1. [Core concepts](#1-core-concepts)
2. [Getting around](#2-getting-around)
3. [Model Inventory](#3-model-inventory)
4. [MRC Meetings](#4-mrc-meetings)
5. [Documents](#5-documents)
6. [Bibliography](#6-bibliography)
7. [Audit Trail](#7-audit-trail)
8. [Admin](#8-admin)
9. [Reporting (PDFs)](#9-reporting-pdfs)
10. [Appendix: reference data](#10-appendix-reference-data)

---

## 1. Core concepts

A few ideas underpin every screen.

**Identity ("Acting as").** The console does not log you in — in production the
institution's SSO identifies you at the perimeter. Locally, the **Acting as**
field at the top right of the header carries your identity. Whatever you set
there is recorded as the author of every change you make. Set it to your
name or email before you start.

**Confirm-to-amend.** Nothing changes silently. Any action that writes data —
registering a model, editing a field, adding an item, scheduling a meeting —
opens a **confirmation dialog** first. You can add an optional *reason*, then
confirm. Only on confirmation is the change written and recorded. This makes
every mutation deliberate and attributable.

**Immutable, event-sourced audit.** Under the hood the platform is
*event-sourced*: each change is appended to a tamper-evident log rather than
overwriting state. The screens you see are *projections* rebuilt from that log.
Consequences you can rely on:

- The full history of every model and meeting is preserved — nothing is ever
  truly overwritten or deleted.
- Each event is chained to the previous one with a cryptographic hash, so any
  out-of-band tampering with the database is detectable.
- The **Audit Trail** tab is not a separate log that *describes* changes — it
  *is* the changes.

---

## 2. Getting around

The top navigation has six tabs:

| Tab | Purpose |
|---|---|
| **Model Inventory** | Register and manage models; the heart of the platform. |
| **MRC Meetings** | Schedule and document Model Risk Committee meetings. |
| **Documents** | Governance-wide document library. |
| **Bibliography** | References and BibTeX export. |
| **Audit Trail** | The immutable record of every change. |
| **Admin** | Committee settings, branding, people directory, and menu lists. |

---

## 3. Model Inventory

### 3.1 The inventory list

The landing tab shows summary cards (counts by status) and a table of all
models — ID, name, company, tier, RAG rating, owner, and lifecycle stage.
Click any row to open that model's detail. The **↓ Model Risk Report** button
(top right of the list) produces a committee status PDF (see
[Reporting](#9-reporting-pdfs)).

### 3.2 Registering a model

The **Register a model** card at the top takes a mandatory **Model ID** (e.g.
`MKM-CR-001`) and **Name**, plus a few headline fields (company, division,
department, repository, codebase, category, tier, owner). Click **Register…**,
confirm, and the model appears in the list.

On registration the platform automatically seeds the **nine SR 26-2 validation
questions** (see the [appendix](#10-appendix-reference-data)) against the model,
each starting as *Not Addressed* — so a newly registered model has a complete,
visible validation checklist from day one.

### 3.3 The model detail view

Opening a model shows a header (tier descriptor, computed risk badge, owner,
RAG dot, key review dates) and a row of tabs:

| Tab | What it holds |
|---|---|
| **Overview** | All scalar fields grouped into Organisation, Classification, Methodology, Governance, Review dates, and Testing. Each field has an inline **edit** link. |
| **Remediation** | Remediation steps (description, owner, priority, due date, status). |
| **Versions** | Version history (version, date, description, author, reference document). |
| **Limitations** | Known limitations (description, impact, monitoring trigger, compensating control). |
| **Assumptions** | Model assumptions (description, impact, monitoring, mitigation). |
| **Changes** | Change history (version, date, author, type, description). |
| **Validation** | The SR 26-2 validation questions and their status; the tab badge shows coverage as *addressed / total*. |
| **Risk Rating** | The computed composite risk rating and its components. |
| **Docs** | Uploaded documents in four categories (see below). |
| **Audit** | The change history for this model. |

### 3.4 Editing fields

On the **Overview** tab, click **edit** next to any field, change the value
(free text, a dropdown for choice fields, or a date picker), click **Save…**,
and confirm. Choice fields (e.g. RAG rating, validation status, lifecycle
stage, materiality, complexity) enforce their allowed values. Fields backed by
reference data — owner, peer reviewer — become dropdowns once the relevant
[admin lists](#8-admin) are populated.

### 3.5 Structured registers (collections)

Remediation, Versions, Limitations, Assumptions, Changes, and Validation are
all *collections*: each tab has an **Add…** form at the top, an editable table
of existing items, and inline remove. Adding, editing, or removing an item is
confirm-to-amend like everything else, and each item carries a stable ID
(e.g. `RM-001`).

### 3.6 Risk Rating

The **Risk Rating** tab shows an overall rating of **Acceptable**,
**Conditional**, or **Unacceptable**, derived from a weighted composite of five
components — validation coverage, remediation health, review currency,
assumption risk, and limitation risk. See the
[appendix](#10-appendix-reference-data) for the exact weights and thresholds.
The rating updates automatically as you address validation questions, close
remediation steps, and keep review dates current.

### 3.7 Documents on a model

The **Docs** tab has four category sub-tabs — **Core Documentation**,
**Test Results**, **Analysis**, and **Monitoring**. Choose a file, add an
optional description, and upload; documents can be downloaded or deleted. The
file is stored on disk while its metadata is recorded in the event stream.

### 3.8 Retiring a model

A retired model is read-only — it can no longer be edited, preserving its record
for audit. Retire it from the model detail (the action is confirm-to-amend).

---

## 4. MRC Meetings

### 4.1 Scheduling a meeting

The **MRC Meetings** tab mirrors the inventory: a **Schedule a meeting** card,
summary cards, and a list. Provide a **Meeting ID** (e.g. `MRC-2026-Q3`), a
**title**, and a **date** (mandatory), plus optional time, location, and chair.
Schedule and confirm, and the meeting appears in the list with count columns for
its sub-collections.

### 4.2 The meeting detail view

**Double-click** a meeting row to open its detail. The header shows the title,
status, and key fields (inline-editable), a **↓ Meeting Pack PDF** button, and
seven sub-tabs:

| Sub-tab | Contents |
|---|---|
| **Agenda** | Agenda items (title, description, presenter, status). |
| **Minutes** | Minute entries (title, presenter, text). |
| **Participants** | Attendees and their status (Invited / Attended / Apologies / Declined). |
| **Models** | Models in scope for the meeting (linked to the inventory, showing tier / RAG / review status). |
| **Decisions** | Decisions taken (description, date). |
| **Actions** | Action items (description, owner, target date, status). |
| **Documents** | Documents attached to the meeting. |

Each sub-tab works like the inventory collections: add, edit, remove — all
confirm-to-amend.

### 4.3 Meeting Pack PDF

**↓ Meeting Pack PDF** renders a formatted committee pack — institution
branding from the [Admin settings](#8-admin), meeting details, participants,
agenda, minutes, decisions, and actions. (Requires `tectonic`; see the README.)

---

## 5. Documents

The **Documents** tab is a governance-wide library, independent of any single
model. Upload a file with an optional description; the table lists each
document's name, description, date added, and size, with download and delete.
Use it for institution-level policies, frameworks, and committee papers.

---

## 6. Bibliography

The **Bibliography** tab manages a reference list — author(s), year, title,
journal / publisher, category, and URL. Add references, edit or delete them, and
filter by category. **Export BibTeX** downloads the whole bibliography as a
`.bib` file for use in LaTeX or reference managers.

---

## 7. Audit Trail

The **Audit Trail** tab is the immutable, chronological record of every change
across the platform — each entry shows what changed, on which aggregate (model
or meeting), the **actor**, the timestamp, and the **reason** they supplied at
confirmation. Because the platform is event-sourced, this trail is the source of
truth; the other screens are simply current views built from it.

---

## 8. Admin

The **Admin** tab maintains institution-level configuration. All of it is
confirm-to-amend.

**MRC settings & branding.** Organisation name and address, committee chair,
model owner, meeting frequency, handbook reference, and governance framework —
plus an **organisation logo** upload. These details populate the console header
and the headers of the Meeting Pack and Model Risk Report PDFs.

**People directory.** A list of people (name, email, role, organisation). Fields
across the app that reference people — a model's owner and peer reviewer, a
meeting's chair — turn into dropdowns sourced from this directory.

**Reference menus.** Editable lists for Company, Division, and Department. Once
populated, the corresponding model fields render as dropdowns instead of free
text, keeping organisational data consistent.

---

## 9. Reporting (PDFs)

Two committee-facing PDFs are produced on demand (both require `tectonic`):

- **Model Risk Report** — from the **Model Risk Report** button on the Model
  Inventory tab. A status report across the whole inventory for the MRC: a
  summary by risk acceptability, and per-model tier, RAG rating, validation
  coverage, computed risk rating, and review status.
- **Meeting Pack** — from the **Meeting Pack PDF** button inside a meeting. The
  full pack for a single committee meeting (see [section 4.3](#43-meeting-pack-pdf)).

Both carry the institution branding configured under [Admin](#8-admin).

---

## 10. Appendix: reference data

### Tiers

| Tier | Descriptor |
|---|---|
| 1 | Maximum |
| 2 | Substantial |
| 3 | Moderate |
| 4 | Minimal |
| 5 | Negligible |

### Risk-rating composite

The overall rating is a weighted sum of five components (weights sum to 1.0):

| Component | Weight |
|---|---|
| Validation coverage | 0.30 |
| Remediation health | 0.25 |
| Review currency | 0.20 |
| Assumption risk | 0.15 |
| Limitation risk | 0.10 |

The resulting score maps to a rating: **Acceptable** at ≥ 0.75, **Conditional**
at ≥ 0.50, otherwise **Unacceptable**.

### The nine SR 26-2 validation questions

Seeded automatically on registration (SR 26-2 supersedes SR 11-7; the questions
are unchanged):

1. **Ronseal Test** — Does the model do what it says on the tin?
2. **Accuracy & Stability** — Does the model provide timely, accurate and stable results?
3. **Resource Usage** — Does the model consume excessive computational resources?
4. **Override Controls** — Are there controls over manual overrides?
5. **Data Quality** — Is the input data accurate, complete and appropriate?
6. **Assumptions** — Are the model's assumptions documented and justified?
7. **Limitations** — Are the model's limitations understood and monitored?
8. **Benchmarking** — Has the model been benchmarked against credible alternatives?
9. **Independent Validation** — Has the model been independently validated?

### Controlled vocabularies

| Field | Values |
|---|---|
| RAG rating | Green, Amber, Red |
| Validation status | Initial, Pending, Validated, Conditionally Approved, Rejected |
| Lifecycle stage | Development, Validation, Production, Retired |
| Materiality / Complexity | Low, Medium, High |
| Review frequency | Monthly, Quarterly, Semi-annual, Annual |
| Validation question status | Addressed, Partially Addressed, Not Addressed, Not Applicable |
| Remediation status | Open, In Progress, Closed |
| Meeting status | Scheduled, Completed |
| Participant status | Invited, Attended, Apologies, Declined |

---

© 2022–2026 MKM Research Labs. All rights reserved.
