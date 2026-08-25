# The Dashboard, and the ERM model-risk API

**Status:** Proposed — not started
**Date:** 2026-08-24
**Landing surface:** a new first tab, shown before Models
**Consumers:** the firm's C-suite ERM reader (in-console) and the firm's ERM
platform (over HTTP)

Two deliverables, one computation. The console gets a landing tab; the ERM
platform gets a read-only API. Both serialise the same module, so the number on
the executive's screen and the number in the ERM's model-risk panel cannot
disagree.

---

## 1. The question the dashboard answers

> *"Do I need to respond to what I am seeing on the dashboard?"*

This is the specification, not a nice framing of it. Every element on the page
earns its place by helping answer it, and anything that does not is left off.

The consequence is a rule we hold to throughout: **no number appears without the
state it implies.** "14 open findings" is not information — an executive cannot
tell from it whether to do anything. "14 open findings, all with named owners
and inside their deadlines — nothing for you" is information, and it is shorter
to read.

A C-suite reader has only four available responses, so the dashboard sorts
everything into exactly four states and uses them everywhere:

| State | Means | The reader's response |
|---|---|---|
| **Clear** | Nothing owed. | Nothing. |
| **Monitor** | Owed, not yet due, with a named owner. | Nothing today. Note it. |
| **Act** | Owed and past its date. | Chase the named owner. |
| **Escalate** | A governance rule is breached that no owner can clear alone. | Yours. Take it to the committee. |

Four states, fixed forever, in the API as well as on the screen. The *labels*
are adopter-configurable like every other vocabulary in the platform
(`docs/design/adopter-configurable-vocabulary.md`); the four machine values are
not, because an ERM integration written against them has to survive a rename.

## 2. The rule that decides "needs your response"

The verdict must be derivable and defensible — a rule an assessor can check,
not an impression. An item needs the executive's response when, and only when,
one of these holds:

1. **A date the record itself carries has passed.** A review past
   `next_review_date`; a remediation step past its `due_date`.

   *Corrected during Phase 1.* The original draft said "a committee action past
   its due date". An MRC action has no target date — `config.governance._mrc`
   records progress as dated updates instead — so calling one late would put a
   deadline in front of an executive that no committee ever set. The dated
   commitment in this platform is the **remediation step**, which carries an
   owner, a due date and a priority. Open committee actions are still reported,
   as outstanding rather than as late.
2. **A hard governance rule is breached.** Four of these, and each is
   deliberately something an owner *cannot* quietly close by filling in a field:
   - the recorded reviewer is the record's own owner (`_independent()` fails —
     ISO 31000 5.4.3, COSO principle 2, and `ENFORCE_REVIEWER_INDEPENDENCE`);
   - a division is running on a risk policy its committee has never ratified
     (outside `ratified_divisions()`);
   - the register cites a document the store cannot produce (a
     `document_broken` gap — the record asserts evidence that does not exist);
   - a record carries no MRC sign-off, at any tier. Decided 2026-08-24, to match
     limb 3: only the committee can sign a record off, so an owner cannot clear
     this one whatever the tier. Like limb 3 it is aggregated into a single queue
     row, so a large backlog cannot crowd out the singular findings.
3. **A record is materially incomplete, at any tier** — its weighted
   completeness sits below its division's `acceptable_at` (0.85 on the firm-wide
   seed). Decided 2026-08-24: this limb does not stop at Tier 1, because a
   division's own threshold is already the statement of what it will accept, and
   applying it to some records and not others makes it mean two things.

Everything else that is open is **with an owner**, and the dashboard says so
rather than counting it against the executive. That distinction is the whole
value of the page: it converts a backlog into a queue with somebody else's name
on it.

**Because limb 3 bites at any tier, incompleteness enters the queue as one row,
not one row per record.** On a real estate that limb is the largest single
contributor, and thirty rows saying the same thing would bury the two findings
that are genuinely singular — which would defeat the page. So the queue carries
*"12 records below the acceptable standard — 4 Tier 1, 5 Tier 2, 3 Tier 3"* on a
single line, and the drill-down behind it is ordered by the audit's own severity,
so `tier_weight` still floats the worst to the top without the rule having to
mention tiers at all. Dated items stay one row each, because each has its own
owner and its own date. Breaches stay one row each, because each needs its own
committee decision.

This is also why the estate panel carries *records below standard* beside the
estate-wide figure.

*Corrected during Phase 1.* That figure is **the share of records meeting the
standard**, not a weighted average of their completeness scores. The audit
reports completeness per record against each division's own threshold and
publishes no estate-wide number; averaging those would put a figure nobody set on
the front page of a governance record. A count ratio is checkable against the
register by hand, and no weighting can flatter it. The tail still matters — which
is why the count of records below standard sits beside the share, not behind
it.

**Note what is deliberately absent from the rule.** A completeness finding
("Record the validation date on EF001") has no age today — the audit is computed
fresh each run with no memory of when a gap first appeared — so it cannot yet be
called past-deadline honestly. Rather than invent an age, v1 leaves those in
*Monitor* and §7 adds the memory that promotes them.

## 3. What the page looks like

One verdict, four cards, one queue, two context panels. Nothing else.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Model risk                                     as at 06:00, 24 Aug    │
│                                                                        │
│  ⬤  Yes — 15 items need your response.                                 │
│     Twelve are records below your completeness standard, two are past   │
│     their deadline, and one is a breach only the committee can clear.   │
│     The other 21 open items are with named owners and in date.          │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┬──────────────┐
│ NEEDS YOU    │ BREACHES     │ COMING DUE   │ WITH OWNERS  │
│      14      │      1       │      7       │      14      │
│ past their   │ rules only   │ next 30      │ open and     │
│ deadline, or │ the committee│ days         │ in date      │
│ below standard│ can clear   │              │              │
│    ACT       │  ESCALATE    │   MONITOR    │    CLEAR     │
└──────────────┴──────────────┴──────────────┴──────────────┘

┌── What needs your response ────────────────────────────────────────────┐
│ Record             What is owed           Owner       Due      Over    │
│ Retail Banking     Risk policy never      A. Okonjo   —        —     › │
│   ESCALATE           ratified                                          │
│ EF001  Tier 1 Red  Annual review          J. Patel    14 Jul   41 d  › │
│   ACT                                                                  │
│ A-12   Group MRC   Evidence for closure   R. Ndlovu   01 Aug   23 d  › │
│   ACT                                                                  │
│ 12 records         Below the acceptable   9 owners    —        —     › │
│   ACT                standard                                          │
│                      4 Tier 1 · 5 Tier 2 · 3 Tier 3                    │
└────────────────────────────────────────────────────────────────────────┘

┌── The estate ─────────────────────┬── Direction ──────────────────────┐
│ 46 models · 12 products           │ Governance coverage, 12 months    │
│ 8 ML applications                 │  ▁▂▃▃▄▅▅▆▆▇▇█   78% → 86%         │
│ Tier 1: 9    Red: 3               │  Closed 31, opened 12             │
│ Coverage 86%  (acceptable at 85%) │  Improving                        │
│ Below standard: 12                │                                   │
└───────────────────────────────────┴───────────────────────────────────┘
```

Design notes that matter more than they look:

- **The verdict line is a sentence, not a score.** No index, no traffic light
  with a number under it. A composite "model risk score" would immediately raise
  the question of what it is made of, and the honest answer would take the rest
  of the page. The same argument `model_inventory/risk.py` already makes about
  not deriving a second rating applies here.
- **Every row ends in a named person and a date.** A queue an executive cannot
  hand to somebody is an observation, which is exactly the standard
  `REMEDIATION_ACTIONS` already holds the audit to.
- **Every row is a link into the record**, never a dead end.
- **One chart.** The trend, because "is it getting better?" is the second
  question every executive asks and the one a snapshot of today cannot answer.
- **Colour comes from `config/theme.py`** through `/api/theme`, like every other
  badge in the console (rule R10). Nothing here names a colour.
- **The page never writes.** See §6.

## 4. Where each number comes from

Nothing on the dashboard is newly computed. Every feed already exists:

| Signal | Source | Cost |
|---|---|---|
| Overdue review | `next_review_date` + `compute_review_status` (`src/governance/model_inventory/review.py:28`) | cheap — projection read |
| Overdue committee action | `outstanding_actions_for_committee` (`src/governance/mrc/projection.py:214`) | cheap |
| Operational failures in window | `compute_risk_rating` over `EVENTS_WINDOW_DAYS` (365) | cheap |
| Tier / rating counts | `compute_risk_rating` heatmap | cheap |
| Reviewer independence | `framework._independent()` | cheap |
| Un-ratified division policy | `scan.ratified_divisions()` | cheap |
| Materially incomplete records | `scan()` row `completeness` vs `acceptable_at` | **expensive** — stats every document file |
| Broken evidence references | `_document_gaps` via `scan()` | **expensive** |
| Framework coverage | `framework.coverage()` / `tally()` | **expensive** |

That split drives the loading design: **the verdict, the four cards and the
queue render from projections alone**, so the landing tab is instant. Coverage
and framework figures arrive in a second request and fill in beneath. An
executive waiting on a filesystem walk before seeing whether anything is on fire
is the wrong trade.

*Task for Phase 0: measure `scan()` against a restored copy of the real estate
before deciding whether the second half needs caching. Guessing at this is how
a landing tab becomes the slowest screen in the product.*

## 5. How this sits with the completeness audit

The user raised this, and it is the design's main risk: dashboards bolted onto
audits drift, and then the firm has two numbers and an argument.

The resolution is a rule with no exceptions:

> **The audit is the evidence. The dashboard is the verdict. The dashboard
> computes nothing the audit does not.**

| | Completeness audit | Dashboard |
|---|---|---|
| Question | *Is each record complete, and how bad is each gap?* | *Does any of this need me?* |
| Unit | One finding, per record | One response, per person |
| Audience | The committee, an assessor | The executive, the ERM |
| Output | A signed PDF, defensible line by line | A sentence and a queue |
| Cadence | Run and minuted at a meeting | Every time the page opens |
| Depth | Every gap, scored `0.90 × 1.00 × 1.25 … = 1.42, Critical` | The band and the deadline only |

The dashboard reads `scan()`'s own rows, `band`, `sla_days` and `action`
unchanged. It re-derives no severity and invents no threshold. Where it adds
anything it is *subtraction*: dropping to four states, and dropping everything
inside its deadline out of the executive's count.

Concretely, the drill-down from **Needs you** is the same finding an auditor
would read in the PDF, with the same wording — so a committee member who has
read the audit recognises the row rather than having to reconcile it.

## 6. What this is deliberately not

Stated so the build does not quietly grow one:

- **Not configurable.** No widget picker, no drag-and-drop, no per-user layout.
  Every reader sees the same page, which is what lets two executives discuss it.
- **Not a second scoring model.** No composite index, no "model risk score".
- **Not a place to act.** The dashboard routes you to the record or the
  committee; it has no "acknowledge" or "dismiss" button. An executive clearing
  an item from a dashboard would be an ungoverned decision with no minute
  attached to it — the platform's whole premise is that the response is recorded
  where it can be challenged. The dashboard's job ends at *"yes, and here it
  is"*.
- **Not scoped by division or committee.** Decided 2026-08-24: the C-suite view
  is firm-wide. Four tabs carry the committee-region bar; this one does not, and
  an ERM that wants the divisional split takes it from the `estate` endpoint. A
  region bar here would let two executives read the same screen and see different
  answers to the same question.
- **Not real-time.** It carries an `as of` stamp and means it.

## 7. The one piece of new state: finding age and trend

Everything above ships with no new persistence. Two things do need it, and they
are worth it:

- **Ageing a completeness finding.** To say a gap is past its `sla_days` we must
  know when it first appeared. The audit has no memory today.
- **The trend line.** "Are we getting better?" needs a series.

Both fall out of one mechanism: a **daily snapshot of the finding set** —
`(as_of, entity_kind, entity_id, gap_key, band, severity)` — written
append-only, plus a derived first-seen date per `(entity, gap_key)`. That gives
finding age, opened-vs-closed counts, and the ERM's time series from one table.

Keep it minimal: one view, one scheduled writer modelled on the existing backup
scheduler, no UI of its own. It is Phase 4 precisely because Phases 1–3 are
useful without it.

## 8. The ERM API

The ERM platform calls us; we never call it. Read-only, three endpoints, one
frozen contract.

```
GET /api/erm/v1/model-risk             the panel: verdict, estate, coverage
GET /api/erm/v1/model-risk/attention   the queue: rows with owner, date, action
GET /api/erm/v1/model-risk/estate      the position: counts by tier/rating/division
```

All three accept `?as_of=YYYY-MM-DD`, which moves the dated rules without replaying
history. The `estate` endpoint returns `direction` alongside the counts, so an ERM
rolling model risk into a divisional view gets the position and the trend in one
read rather than having to fetch the panel for it.

The first is what an ERM dashboard's model-risk tile renders. The second is what
it links to. The third is for an ERM that wants to roll model risk into its own
divisional view.

**The blocks follow where model risk lands, not how we happen to store it.**
Confirmed 2026-08-24: model risk feeds the ERM's *operational risk* view and its
*strategic direction*, so the payload is split the way the receiving function is.
`operational` carries what an operational-risk team consumes — failures that
actually happened in the rolling window, and the controls not holding right now.
`direction` carries what a strategic view consumes — how much of the estate meets
the standard its own divisions set, and which way that is moving. A single
undifferentiated dump of counts would leave both consumers to guess which numbers
were theirs.

```jsonc
// GET /api/erm/v1/model-risk
{
  "schema_version": "v1",
  "as_of": "2026-08-24",
  "generated_at": "2026-08-24T06:00:11Z",
  "institution": "…",                     // MRC settings org_name

  // --- for the C-suite tile ------------------------------------------
  "verdict": {
    "response_required": true,
    "state": "act",                       // clear | monitor | act | escalate
    "headline": "15 items need your response.",
    "detail": "12 records below the acceptable standard, 2 reviews are overdue, "
              "and 1 division runs on an unratified risk policy.",
    "counts": { "escalate": 1, "act": 14, "monitor": 7, "clear": 14 },
    "breakdown": [ { "reason": "record_below_standard", "state": "act",
                     "count": 12, "label": "12 records below the acceptable standard" } ]
  },

  // --- for the ERM's OPERATIONAL RISK view ----------------------------
  "operational": {
    "window_days": 365,
    "failures_in_window": 3,              // events that actually happened
    "records_with_failures": 2,
    "control_breaches": 1,                // controls not holding, right now
    "control_breaches_by_reason": [ … ]
  },

  // --- for the ERM's STRATEGIC view -----------------------------------
  "direction": {
    "records_audited": 66,
    "records_meeting_standard": 54,
    "records_below_standard": 12,
    "share_meeting_standard": 0.8182,
    "trend": null                          // null until the snapshot exists
  },

  "estate": { "total": 66, "by_kind": {…}, "by_tier": {…},
              "by_rating": {…}, "by_division": {…} },
  "attention": { "total": 15, "href": "/api/erm/v1/model-risk/attention" }
}
```

```jsonc
// GET /api/erm/v1/model-risk/attention
{
  "as_of": "2026-08-24", "generated_at": "…",
  "total": 3, "returned": 3, "truncated": false,
  "items": [{
    "id": "review:EF001",
    "state": "act",
    "reason": "review_overdue",                 // fixed vocabulary, see below
    "reason_label": "Annual review overdue",    // the adopter's wording
    "group": null,                              // or "below_standard"
    "entity": { "kind": "Model", "id": "EF001", "name": "…",
                "tier": 1, "rating": "Red", "division": "…" },
    "owner": { "name": "J. Patel", "email": "…" },
    "committee": "Group MRC",
    "due": "2026-07-14", "days_over": 41,
    "action": "Complete the scheduled review and record its outcome.",
    "href": "/#model/EF001"
  }]
}
```

The `reason` vocabulary is frozen at v1: `review_overdue`, `action_overdue`,
`signoff_missing`, `reviewer_not_independent`, `risk_policy_unratified`,
`evidence_missing`, `record_below_standard`, `operational_failure`. Note
`signoff_missing` rather than `signoff_missing_tier1`: the rule no longer
mentions a tier.

**The API returns items individually; the grouping is the console's.** Every item
carries a `group` key (`null`, or `"below_standard"`), so an ERM that wants the
same one-line rollup the dashboard draws can reproduce it, and one that would
rather list every record can. Rolling up inside the contract would make the
`total` mean something different from the `counts` in the summary, and a consumer
would have no way to get back to the records.

Contract rules, each with a reason:

- **Versioned in the path.** An ERM integration outlives our refactors, and the
  adopter cannot redeploy their ERM when we rename something.
- **Fixed machine values beside adopter labels.** The vocabulary is
  configurable by design; the contract cannot be. Every enumerated field ships
  both.
- **`as_of` and `generated_at` on every response.** An ERM panel showing a stale
  figure without saying so is worse than showing none.
- **Read-only, always.** No write endpoint on this surface at any version. The
  ERM cannot change the governance record — if it could, the record would no
  longer be the thing the committee signed.
- **Truncation is declared.** The attention list is capped from config; the
  response carries `total`, `returned` and `truncated`. Silent truncation reads
  as "that is all there is".
- **Auth is the ingest pattern, shared not copied.** Ingest already guards a
  machine surface with a shared token (`src/web/api_ingest/_bp.py`). Extract
  that `before_request` guard into a helper both blueprints use, with a separate
  read-only ERM token — a second copy of the same eight lines is how the two
  drift apart. Like ingest's, this is a Phase 0 stub pending a real API-key or
  mTLS scheme.
- **The schema is checked in** under `contracts/erm/v1/`, beside the ingest
  contract, with a validated example — the ERM's developers code against a file,
  not against our prose.

**One computation, two presentations.** `src/governance/attention/` is pure and
returns the verdict and the queue; `api_dashboard.py` serialises it with the
extra ids the console needs for deep links, and `api_erm/` serialises the frozen
contract. Neither blueprint holds any logic. This is the same lesson as the
`_grouped_specs` extraction: four copies of an almost-identical helper, and only
one of them right.

## 9. Project plan

Rough effort in working days, assuming the existing gates stay green.

| Phase | What | Days | Ships something useful? |
|---|---|---|---|
| **0** | Decide and measure | 0.5 | — |
| **1** | `src/governance/attention/` — pure classification + queue, fully tested | 2 | — |
| **2** | The dashboard tab, landing by default | 2.5 | **Yes — the whole ask, in-console** |
| **3** | The ERM API + contract + schema | 2 | **Yes — the integration** |
| **4** | Finding history: age, past-SLA, trend | 2 | Upgrades the queue |
| **5** | User guide + integration-guide sections | 1 | Rollout |

All six phases are built. What remains is the work the plan never claimed: merging
to `main`, and whatever the first real ERM integration asks for.

**Phase 0 — decide and measure.**
Confirm the response rule in §2 with the user (this is the one decision the rest
depends on). Measure `scan()` and `framework.coverage()` wall-time against a
restored copy of the real estate on 5016. Output: a go/no-go on caching.

**Phase 1 — the domain module. BUILT 2026-08-24.**

```
config/governance/_attention.py   the four states, the reasons, the precedence
src/governance/attention/
  _rules.py     classify one obligation                        (pure)
  queue.py      assemble the items                             (pure)
  summary.py    the verdict sentence, the counts, the rollup   (pure)
  position.py   the estate / operational / direction feeds     (pure)
  collect.py    the reads that feed all four                   (I/O)
tests/governance/test_attention.py                             43 tests
```

Four of the five modules are pure, so the rule an executive is asked to trust is
exercised against fixtures rather than against a database. `collect.py` runs
**one** completeness scan and feeds all three views from it, which is what makes
the queue, the operational feed and the direction feed three views of one set of
facts rather than three opinions of it.

Two changes to shared code fell out of it, both removing duplication rather than
adding any. `outstanding_actions()` now sits beside
`outstanding_actions_for_committee()` in the MRC projection, sharing one filter for
what "still owed" means. And `config/governance/_attention.py` declares its own
`__all__` and is star-imported by the package aggregate, following the
`_ml_exports` precedent, which is what kept that aggregate inside the R2 gate.

*A wrong turn worth recording.* The first attempt had the aggregate compose its
`__all__` from each area's — `[...] + list(_attention_all) + list(_ml_all)` — which
removed the duplication more thoroughly and passed the R2 gate. It failed R4: a
package re-exports, it does not compute, and the init-file audit requires `__all__`
to be a *literal*. `pytest` caught it where `python -m audit` did not, which is the
argument for running both.

**Phase 2 — the dashboard tab.**
`src/web/api_dashboard.py`, `src/static/js/dashboard.js`, a `<section
id="tab-dashboard">` in `index.html`, the tab first in the bar, and
`main.js`'s landing `showTab("inventory")` becomes `showTab("dashboard")`.
Two-stage load per §4. Verified in the browser on 5016, not by tests alone —
and remember a *new* `<script>` tag needs a gunicorn restart, since Jinja caches
`index.html` with `debug=False`.

**Phase 3 — the ERM API. BUILT 2026-08-25.**

```
config/erm.py                    prefix, token, cap, console tab map
src/web/_token_auth.py           the shared guard — ingest now uses it too
src/web/api_erm/
  _bp.py                         the blueprint and its guard
  model_risk.py                  the three endpoints
contracts/erm/README.md          what an integrator reads first
contracts/erm/v1/*.schema.json   the frozen contract, + validated examples
tests/web/test_erm_api.py        19 tests, schema-validated
```

Verified end to end against a restored copy of the estate: unauthenticated and
wrong-token both 401, every write verb 405, and the live responses validate
against the checked-in schemas rather than against a copy of them in the test.

Three things the build settled that the design had left loose:

**The guard was extracted, not copied.** `src/web/_token_auth.py` now serves both
machine surfaces and ingest was re-pointed at it, so there is one constant-time
comparison rather than two. The tokens stay separate: ingest writes the governance
record and the ERM may only read it, and a single credential would collapse that
distinction.

**`href` had to become real.** The contract promises a link back to the record, and
the console had no routing to answer one — an ERM tile linking to a page that
ignores the link is worse than a tile with no link. `main.js` now reads
`#<tab>/<id>` on load and on `hashchange`; `href` is `null` for anything the
console has no screen for, rather than a plausible URL that strands a reader.

**`group` carries the reason, not a separate vocabulary.** The design sketched
`"below_standard"` as a magic value. It is simply the reason the item would collapse
under, or `null` — one less thing for an integrator to learn, and it stays correct
as reasons are added.

**Phase 4 — finding age and trend. BUILT 2026-08-25.**

```
src/database/migrations/0012_attention_history.sql   two tables
config/history.py                                    the observer's settings
src/governance/attention/history.py                  observe / ages / trend
src/web/_history.py                                  the daily schedule
tests/governance/test_attention_history.py           16 tests
```

Three decisions the build made that §7 had left open:

**A daily snapshot of the finding set became a first-seen record.** The sketch was
one row per finding per day, which grows at the speed of the calendar — a year of a
270-finding estate is a hundred thousand rows saying mostly the same thing. What is
stored instead is one row per finding *ever seen*, carrying `first_seen`,
`last_seen` and `closed_at`. That grows at the speed of the estate's problems, and
it answers strictly more: age, opened-versus-closed, and the trend, from three
dates.

**A finding's identity excludes its severity.** Severity moves with a record's tier
and rating, so keying on it would close every finding on a model and open an
identical set the same day somebody re-rated it — resetting every clock. The key is
the record and the thing that is missing, nothing else. A finding that closes and
returns keeps its original `first_seen` for the same reason: otherwise a record
escapes a deadline by being briefly fixed.

**It observes on a schedule, never on a request.** Observing when the dashboard is
opened would have been simpler and needed no thread — but the console and the ERM
API are both documented as reads, and a GET that wrote would make both claims false
as well as writing at whatever rate the ERM happened to poll. One observation a day,
from the gunicorn master, alongside the backup schedule.

The tables are deliberately not named `*_view`: every other table here is a read
model replayed from the event log, and these two are the only state that is not.
Nothing in the log records what the audit found on a Tuesday, because nobody decided
it. They are added to the test suite's per-test reset for the same reason the views
are — left behind, one test's history ages another test's findings and the verdict
starts depending on test order.

**Phase 5 — documentation. BUILT 2026-08-25.**

`docs/user_guide.md` gains §21 (the dashboard, the four states, how it relates to
the completeness audit) and §22 (feeding an ERM), plus the Dashboard in §2's tab
list — the guide described a tab bar the console no longer had.

`docs/integration_guide.tex` gains §"Feeding an ERM": the three endpoints, which
block each ERM function reads, the token model, the two conventions to code
against, and the five things the payload deliberately will not do. The environment
reference gains the ERM and finding-history variables; the file map gains
`contracts/` and the new `src/web` modules; the verification checklist gains three
`curl` checks, the first of which — *does the ERM surface 401 an unauthenticated
caller* — is the one an operator most needs to have actually run.

Both are published as PDFs by the Audit Reports tab, so both were rendered rather
than assumed: the LaTeX compiles with no new overfull boxes (one was introduced and
fixed), the Markdown survives conversion, and the extracted text of each carries the
new sections. The committed `docs/integration_guide.pdf` was regenerated through the
app's own renderer, not a bare `tectonic` run, so it matches what the console would
publish.

**The smallest useful thing is Phases 0–2** (5 days): the landing tab, answering
the question, with no new persistence and no new API surface. Phase 3 is the
ERM integration and is independent of Phase 4.

## 10. Decided, and still open

**Decided 2026-08-24.**

- **Limb 3 bites at any tier**, not Tier 1 only (§2), which is why incompleteness
  enters the queue as one aggregated row rather than one row per record.
- **The missing-sign-off breach bites at any tier too**, on the same reasoning,
  and is aggregated the same way.
- **"You" is the C-suite, not the individual reader.** Every reader sees the same
  page, which is what lets two executives discuss it. No per-user queue, in v1 or
  later; the People roles stay out of this surface.
- **Model risk feeds operational risk and strategic direction** in the ERM, which
  is why the API carries those two blocks by name (§8).
- **The coming-due horizon is 30 days**, and deliberately not a new constant: it
  is `REVIEW_DUE_SOON_DAYS`, the same window the model register already calls Due
  Soon. An adopter on a quarterly cycle raises that one value and both move.
- **The dashboard is firm-wide in v1** — no committee-region bar (§6). The
  divisional split lives on the ERM's `estate` endpoint.

**Still open.**

1. **Which reasons aggregate?** Two do today (`record_below_standard`,
   `signoff_missing`). If a third grows large on a real estate, the grouping
   should follow it rather than being decided per-reason in code.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
