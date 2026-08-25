# ModelRisk → ERM contract

The JSON Schemas under `v1/` are the **contract** an enterprise risk platform codes
against. ModelRisk is the system of record for model risk; the ERM pulls from it.

**The ERM calls us. We never call it, and it can never write.** There is no write
endpoint on this surface at any version — if the ERM could change the governance
record, the record would no longer be the thing the committee signed.

## Endpoints

```
GET /api/erm/v1/model-risk             the panel: verdict, operational, direction, estate
GET /api/erm/v1/model-risk/attention   the queue: every outstanding obligation
GET /api/erm/v1/model-risk/estate      the position: counts by kind, tier, rating, division
```

All three accept `?as_of=YYYY-MM-DD`, which moves the dated rules (review currency,
remediation dates). It does **not** replay history: the registers hold current state.

Authentication is a shared token in `X-ERM-Token` (`ERM_TOKEN_HEADER` /
`ERM_DEV_TOKEN`). This is the same Phase 0 stub the ingest contract describes and
is replaced by a real API-key or mTLS scheme before any external party is
onboarded. The ERM token is deliberately **separate from the ingest token**: the
two surfaces have opposite privileges, and one credential for both would collapse
that distinction.

## Layout

```
v1/
  model_risk.schema.json   the panel
  attention.schema.json    the queue
  examples/                one validated example per schema
```

## Where model risk lands

The payload's blocks follow the receiving function, not our storage:

| block | consumed by | carries |
|---|---|---|
| `verdict` | the C-suite tile | whether anything needs a response, as a sentence |
| `operational` | operational risk | failures that actually happened; controls not holding |
| `direction` | strategic view | how much of the estate meets the standard, and the trend |
| `estate` | either | what the estate is made of |

## Two conventions to rely on

**Fixed machine values beside adopter labels.** Every enumerated field ships both —
`state`/`label`, `reason`/`reason_label`. An institution renames its risk
vocabulary; the contract does not move when it does. Code against `state` and
`reason`; display `label` and `reason_label`.

**Items come back individually.** The console collapses twenty overdue remediation
steps into three rows, one per owner. That is a presentation decision and it stays
in the console. Each item carries `group` — the reason it would collapse under, or
`null` — so a consumer can reproduce that rollup or list every record instead.
Rolling up inside the contract would leave no way back to the records.

## Things the payload will not do

- **Report a score it did not compute.** `direction.share_meeting_standard` is a
  count ratio — records meeting their division's own threshold, over records
  audited. The completeness audit publishes no estate-wide figure, and a weighted
  average would be a number nobody chose sitting on a governance record.
- **Infer a deadline.** `due` is a date a person set, or `null`. A committee action
  is agreed without a target date, so it is reported as outstanding and never as
  late.
- **Truncate silently.** `total`, `returned` and `truncated` are always present.
- **Emit a link that 404s.** `href` is `null` where the console has no screen for
  that kind of thing. A dead link in somebody else's dashboard is worse than none,
  because it is found by a person who cannot fix it.
- **Hide "no history".** `direction.trend` is `null` until a finding history exists,
  rather than absent — a strategic view that cannot tell "no history yet" from
  "flat" would read a new install as a stable one.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
