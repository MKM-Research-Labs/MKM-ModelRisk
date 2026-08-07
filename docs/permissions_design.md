# Permissions — design proposal

**Status:** proposal for decision. Nothing here is built. Written 2026-08-07 after an
ad-hoc script authored 24 events on the live estate under the test suite's identity
(`alice@corp`), which the audit trail recorded faithfully and nothing prevented.

---

## 1. What exists today

**Authentication** is perimeter-delegated and *trusted verbatim*. `resolve_principal`
(`src/identity/resolver.py`) reads `X-Auth-Request-User`, wraps it in a `Principal`, and
records it as `actor` on every event. Whatever string arrives becomes the author. That is a
legitimate architecture behind an SSO proxy — but there is no check that the actor is a
person this institution knows, so anything that can reach the port can author governance
history under any name.

**Authorization does not exist.** `authorize(principal, command_name)` in
`src/command/dispatch.py` is a documented no-op — the seam was left deliberately. Every
authenticated actor can today register models, edit any field, approve MRC sign-offs,
ratify risk policy, close meetings and retire models.

For a model-risk platform this is the wrong way round: the product's entire value is that
decisions are attributable and segregated, and the two controls that would make them so are
the two that are missing.

## 2. Principle: permissions come from the domain, not a parallel user store

The domain already knows almost everything an authorization layer needs:

| Question | Already answered by |
|---|---|
| Who is a real person? | the People reference list (Admin → People) |
| Who owns this model? | the model's `owner` field |
| Who sits on the committee that governs it? | the MRC committee (chair, members) and its division / line-of-business scope |
| Which committee governs this subject? | existing sign-off routing (`_signoff_routing.py`) |

So: **no user table, no parallel role store.** A person gains rights by being recorded in
the governance record — as a named person, as a model's owner, as a committee member. That
keeps one truth, and it means permissions are themselves auditable and MRC-ratifiable,
exactly like everything else here.

## 3. Roles

Five, mapped to the roles the framework already names:

- **Reader** — sees everything, changes nothing. The default for a known person.
- **Owner** — the model/product's recorded owner: sets classification and rationales,
  uploads evidence, answers validation questions, *requests* MRC sign-off. Scoped to the
  subjects they own.
- **Validator** — independent review: validation status and questions, validation date.
  Scoped by division. **Must not be the subject's owner** (see §4).
- **Committee** — MRC members and chair: approve/reject sign-off, ratify risk policy,
  ratify retire/reactivate, close meetings. Scoped to their committee's subjects.
- **Administrator** — reference lists, risk-policy drafts, MRC configuration, company
  settings. Explicitly *not* able to approve sign-offs: configuring the framework and
  ruling under it are different jobs.

Plus **system** actors (`ingest:<source>`), which may only append ingested facts.

## 4. Segregation of duties — the part that matters to a regulator

Roles alone are table stakes. The controls worth building are the negative ones:

1. **An owner cannot approve their own model.** The sign-off request and the sign-off are
   different people, always.
2. **A validator cannot validate a model they own.**
3. **An administrator cannot ratify the policy they drafted** — the draft goes to the MRC,
   which is already how the risk policy works; this generalises it.
4. **The chair cannot be the sole approver of their own tabled paper** (the existing
   escalation-to-a-higher-tier-MRC path already anticipates this).

These are assertions a validator can demonstrate to an examiner, and they are cheap here
because every decision is already an event with an actor.

## 5. Where it is enforced

**One place: `dispatch`.** Every mutating command already passes through it, alongside the
confirm-to-amend gate. `authorize()` becomes real and is called there — so a new endpoint
cannot forget to check, in the same way R6 means no module can forget how to reach the
store.

```python
# src/command/dispatch.py — the seam that already exists
def authorize(principal: Principal, command_name: str, **kwargs) -> None:
    """Raise AuthorizationError unless this principal may run this command
    on this subject."""
```

The permission map is **data, not code** (rule R1): `config/permissions.py` holds
`COMMAND_ROLES = {"update_field": ("owner", "administrator"), "approve_signoff":
("committee",), ...}`, which an adopting institution re-sets to its own framework — the
same treatment the risk vocabulary and completeness weights already get.

The UI stops offering what the caller may not do, but that is cosmetic: the server is the
control.

## 6. Rollout

Sequenced so nothing is enforced before it can be satisfied.

- **P1 — Know who is real.** Reject an actor absent from the People list while `DB_NAME` is
  protected. Closes the breach that prompted this. Small, and independently useful.
- **P2 — Roles as data.** Add role assignment to the People record (a person may hold
  several); expose it in Admin → People. Events, so assignment is audited.
- **P3 — Authorize, in report-only mode.** Implement `authorize()` but only *log* refusals,
  for a week of real use. This is the phase that prevents a permissions rollout from
  blocking the day job; the log says exactly what would have broken.
- **P4 — Enforce.** Turn refusals into `AuthorizationError` (HTTP 403), with a message that
  names the missing role rather than "denied".
- **P5 — Segregation of duties.** The negative rules in §4, which need P2's data to express.
- **P6 — Machine actors.** Scope `ingest:*` principals to append-only.

## 7. Decisions needed before P1

1. **Is the SSO header trusted in production?** If a proxy authenticates it, P1 is a
   defence-in-depth check. If not, verification has to move up a layer and that is a bigger
   piece of work.
2. **What happens to events already authored by unknown actors?** They stay — the log is
   append-only. Proposal: surface them on the Audit tab as "unrecognised actor" so they can
   be explained rather than silently trusted.
3. **Does a role assignment need MRC ratification,** or is it an administrative act? Making
   *committee* membership ratifiable is defensible; making every reader ratifiable is not.
4. **Break-glass.** Someone must be able to act when the committee cannot convene. Named,
   time-boxed and loudly audited — or explicitly refused. This should be a deliberate
   decision, not an oversight.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
