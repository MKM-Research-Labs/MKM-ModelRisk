# Design: centralising look and feel into `config/theme`

**Status:** Step 1 shipped 2026-08-22 (the token module, the served stylesheet and the
vocabulary); steps 2–7 outstanding
**Date:** 2026-08-21
**Area:** `src/static`, `src/templates`, `config/`, `audit/`
**Driver:** An ERM vendor is cloning ModelRisk into their suite as a new pillar. Their
visual language is close to ours but not ours, so every brand value has to be
changeable without forking the code.
**Scope:** the console only — the CSS and the JavaScript. The generated PDFs carry the
same problem and are deliberately left out of this pass; see §9.

---

## 1. Why this exists

The DB layer migrated to MS SQL cheaply because every connection parameter had exactly
one home (`config/database.py`) and nothing in `src/` was allowed to spell one out. The
look and feel has no such home. It is spread across four languages and 56 files, and it
has already drifted.

This is the visual sibling of `docs/design/adopter-configurable-vocabulary.md`: that
document says a closed set of *words* shown to a user belongs to the adopting
institution. The same is true of every *colour*, and for the same reason — the day the
adopter changes one, every place the platform wrote it down becomes a lie.

## 2. What the scan found (2026-08-21, `main`)

| Surface | Size | Literals |
|---|---|---|
| `src/static/css/app.css` | 286 lines, 1 file | 75 hex colours — **15** in `:root`, **60** bypassing it; 7 `rgba()`; 362 `px` |
| `src/static/js/**` | 54 files, 11,375 lines | **190** hex colours, **493** inline `style="…"` attributes |
| `src/governance/latex.py` *(out of scope, §9)* | PDF preamble + title page | `\definecolor{mkmblue}{HTML}{1565C0}`, `\textcolor{gray}` ×4 |
| `src/governance/risk_policy/_defaults.py` | lines 45–49 | 3 seeded colour maps, in `src/` rather than `config/` — an R1 violation on its own |

Two findings matter more than the counts.

**The brand blue has already forked.** `#1976d2` in the CSS and the JS; `#1565C0` in the
PDF preamble and in `src/static/js/gov_docs.js:305`. Both are "our blue", in two values
and two letter-cases. A rebrand today is a find-and-replace over four spellings in three
languages, and it would miss some.

**`:root` exists and is already ignored.** `app.css` opens with a 17-token block and then
writes 60 hex values straight into the rules below it. Nothing keeps anyone honest. That
is the whole difference between this and R6: the data-access rule holds because
`python -m audit` fails on a violation, not because it is written down.

## 3. The pattern is already in the repo

`src/static/js/helpers.js` has `Policy` — a registry loaded once from `/api/risk-policy`
at boot, with the built-in constants demoted to *fallbacks used only until the fetch
lands*. Risk-band colours are therefore already server-owned and already adopter-
configurable.

`Theme` is the same object, for the same reason, applied to the rest of the palette. We
are extending an accepted architecture to a second domain, not inventing one.

## 4. Proposed shape

### 4.1 One source of truth

`config/theme.py` — R1's home, exactly as `config/database.py` is for the DB:

```python
BRAND    = {"accent": "#1976d2", "accent_soft": "#e3f2fd", "accent_border": "#bbdefb",
            "header_gradient": ("#f5f7fa", "#c3cfe2"), "logo_ink": "#2a3a4d"}
SEMANTIC = {"ok": "#388e3c", "warn": "#f57c00", "danger": "#d32f2f", "neutral": "#9e9e9e"}
SURFACE  = {"bg": "#eef1f5", "panel": "#ffffff", "line": "#e0e0e0", "line_soft": "#eeeeee",
            "head_bg": "#fafafa", "text": "#333333", "text_2": "#555555", "muted": "#888888"}
TYPE     = {"family": "Arial, Helvetica, sans-serif",
            "base": 13, "sm": 12, "xs": 11, "xxs": 10}
SPACE    = {"1": 4, "2": 6, "3": 8, "4": 12, "5": 16}
RADIUS   = {"sm": 3, "md": 6, "lg": 8, "modal": 10}
```

If it approaches 300 lines (R2), split it as a `config/theme/` package —
`_palette.py`, `_scale.py`, `_status.py` — with an `__init__.py` that re-exports only (R4).

### 4.2 Two emitters off that one dict

1. **CSS** — a `GET /theme.css` route rendering `:root { --accent: …; }`, linked from
   `index.html` *before* `app.css` and cache-busted by the existing `asset_version`
   (`src/web/_assets.py`). A route rather than a Jinja partial, so it sidesteps the
   `debug=False` template-caching trap in CLAUDE.md §4. `app.css` ends with zero colour
   literals.
2. **JS** — `Theme` in `helpers.js`, hydrated from `/api/theme` alongside `Policy.load()`.
   The six hardcoded status maps — `RAG_COLORS`, `TIER_COLORS`, `MEETING_STATUS_COLORS`,
   `VQ_COLORS`, `MRC_STATE_COLORS`, `LIFECYCLE_COLORS` — collapse into one server-supplied
   `statusColour(domain, value)`.
A third emitter — the LaTeX preamble — falls out of the same dict for free once this
exists. It is described in §9 rather than built here.

### 4.3 How an adopter overrides it

Two tiers, only the first of which is needed for the clone:

- **Now — a theme file.** `THEME` ships as the defaults, overridden by JSON at
  `MODELRISK_THEME=themes/<adopter>.json`. Same env-var shape as `DB_NAME`, so the
  vendor ships a theme file and never forks code.
- **Later — Admin → Branding.** Stored like the MRC settings, which already hold
  `org_name` and the report wording (`config/governance/_mrc.py`, `MRC_SETTINGS_SPECS`).
  Deferred deliberately: env-first is what makes the *clone* cheap, and that is the
  immediate goal.

## 5. Migration order

Sequenced so the risky, high-value work lands first and every step ships on its own.

| # | Step | Why here |
|---|---|---|
| 1 | ✅ `config/theme.py` + `/theme.css` route + expand `:root` to the full token set | Nothing changes visually; the vocabulary now exists |
| 2 | `risk_policy/_defaults.py` reads from it | Small; removes seeded colour literals from `src/` (an R1 fix), and they reach the console through `/api/risk-policy` |
| 3 | The six colour maps in `helpers.js` → `Theme` | 28 hexes in one file, and every badge on every screen inherits |
| 4 | `app.css`'s 60 raw hexes → `var(--…)` | Mechanical, CSS-only, easy to eyeball |
| 5 | The remaining 162 JS hexes | Needs the SVG decision in §6 |
| 6 | The 493 inline `style` attributes | Lowest value; cosmetic consistency, not rebrand-blocking |
| 7 | `audit/styling.py` + rule **R10** | What makes all of the above hold |

Steps 1–4 are what the vendor actually needs. 5 and 6 are ours to finish afterwards.

**Step 1, as built (2026-08-22).** 72 tokens in `config/theme.py`, serialised by
`src/web/_theme.py` and served at `/theme.css`, which `index.html` links immediately
ahead of `app.css` under its own content-hash stamp (`asset_version` watches files
under `src/static` and cannot see a generated route, so the theme carries its own).
`app.css` no longer declares a `:root` block. All 15 tokens it used to define carry
through byte-identical; `--head-bg` was renamed `--raised` and its one reference
updated. The remaining 57 tokens are the vocabulary steps 3–5 will consume, and are
unreferenced until then. `tests/web/test_theme.py` holds the load-bearing invariant:
every `var(--…)` the front end reads resolves to a token that exists — a missing one is
silently dropped by the browser, so a rename would otherwise reach a screen as a
colour quietly falling back to black.

## 6. Three traps to know before starting

**SVG presentation attributes do not accept `var()`.** `fill="var(--accent)"` renders
black, silently. The three biggest hex offenders are all SVG builders —
`product/model_map.js` (35), `inventory/neighbourhood.js` (23), `chain.js` (19): 77 of
the 190. Those want CSS *classes* (`.chain-node--terminal { fill: var(--teal); }`), not
token substitution. That is the better answer regardless: `chain.js:304-309` currently
encodes node *state* as a colour inside JS, and a class moves the state to the markup and
the colour to the stylesheet, where it can be themed.

**Most inline styles are not colour — they are an undocumented scale.** Of the 493:
`margin-top` appears 82 times across 9 distinct values (42 of them `8px`, 24 `6px`), and
`font-size` 78 times across 8 values, of which 132 of 145 total are just `11px` or `12px`.
That is a four-value spacing scale and a two-value type scale that nobody ever wrote
down. Worth a small utility layer eventually; it does not block the adopter.

**The existing gates apply.** R3 wants ≥99% coverage, so the new config module, the route
and `Theme` all need tests. R2 caps `config/theme.py` at 300 lines (see §4.1). R5 wants
the canonical header on every new `.py` and `.js` file.

## 7. Enforcement — rule R10

Without a gate this is undone within a month. `audit/hardcoding.py` already does exactly
this job for Python parameters — same walk (`audit/_walk.py`), same finding shape — so
`audit/styling.py` is a close sibling:

- No hex or `rgb()`/`rgba()` colour literal in `src/static/**` or `src/templates/**`.
  (Extending it to `.py` outside `config/theme` waits on §9 — `latex.py` would fail such a
  rule today, and a gate that ships red is a gate nobody trusts.)
- Every `var(--x)` referenced anywhere resolves to a token the theme actually defines.

The second check is the one that matters for the clone: a partial adopter theme fails the
gate loudly instead of rendering half-branded. Register it in `audit/__main__.py` and
write it up in `docs/rules/coding_rules.md` as **R10 — All visual parameters come from
`config/theme`**, next to R7 (which already owns where front-end assets live).

## 8. Cost and payoff

Roughly three days for steps 1–4 plus the audit rule; steps 5–6 are a further day or two
of mechanical work that can follow at leisure.

After it, an adopter changes one `themes/<company>.json` — about 25 values — and their
pillar matches their suite across every screen and graph canvas in the console. The same
trade the database migration bought: the migration costs days, and every rebrand after it
costs an hour. The generated PDFs join the same file for a further half-day whenever §9.1
is picked up.

## 9. Ideas for further consolidation

None of these block the vendor. They are recorded here so the next pass is chosen
deliberately rather than discovered by an adopter.

### 9.1 The generated PDFs

**The requirement.** Every governance artefact the platform issues — the Meeting Pack, the
Model Risk Report, the Risk Categorisation PDF, the coding-rule and completeness audits —
is a LaTeX document assembled by `src/governance/latex.py`. An adopting institution puts
these in front of its own committee and, in the Moody's case, in front of a regulator.
They are the most *externally visible* thing the platform produces, and today they carry
our house style with no way to change it short of editing Python.

**What is already theirs.** More than half the problem is solved. The wording —
classification banner, "Prepared by", the legal notice — is adopter-configurable through
Admin › Misc (`MRC_SETTINGS_SPECS` in `config/governance/_mrc.py`), and the title-page
logo is uploaded, not shipped (`LOGO_ASSET`). What remains is purely visual.

**What is still ours, and hardcoded** — all of it in the preamble and title page of
`latex.py`:

| Element | Today | Belongs in |
|---|---|---|
| Link / accent colour | `\definecolor{mkmblue}{HTML}{1565C0}` | `BRAND["accent"]` |
| Header, footer, subtitle ink | `\textcolor{gray}` ×4 | `SURFACE["muted"]` |
| Classification mark | `\textcolor{red}` | `SEMANTIC["danger"]` |
| Body typeface | LaTeX default (Computer Modern) | `TYPE["family"]` |
| Title fonts | `\font\myverylargefont=cmr12 at 35pt`, `\mylargefont` at 25pt | a `TYPE` display scale |
| Page geometry | `a4paper, left=20mm, right=20mm, top=20mm, bottom=25mm` | a `PAGE` block |
| Line spacing, rule weights | `\onehalfspacing`, `0.4pt` head/foot rules | same |

Two things fall out of writing that table. The first is that the accent is the *wrong
blue*: `#1565C0` here against `#1976d2` on screen, so a report and the console it came
from have never quite matched. The second is bigger — the PDFs are set in Computer
Modern while the console is Arial. The divergence is already wider than colour, and any
adopter who looks at the two side by side will see it.

**What it would take.** The work is small once §4 exists, because `config/theme.py` is
already the right dict: add a third emitter that renders the preamble's colour, font and
geometry declarations from it, and delete the literals. Half a day, plus tests — the
compile path shells out to `tectonic`, so the cheap test asserts on the generated preamble
string rather than on a rendered PDF. Doing it also unblocks the second half of the R10
gate (§7), which currently has to stop at `src/static` because `latex.py` would fail it.

**When.** Worth doing before an adopter's first regulator-facing pack, not before the
clone ships.

### 9.2 Runtime theming, not just deploy-time

§4.3 proposes a theme file read at start-up. The tier above it is Admin › Branding,
stored the way the MRC settings already are, so an adopter tunes the palette without a
deploy. Only worth building once a second adopter asks — one vendor with one JSON file
does not need it.

### 9.3 A validated theme contract

An adopter's `theme.json` is an interface, and `contracts/` is where this repo puts those.
A JSON Schema for the theme would let a partial or malformed adopter theme fail at
start-up with a named missing token, rather than rendering half-branded. Natural companion
to the R10 token-resolution check, and cheap alongside it.

### 9.4 Graph geometry

The SVG builders (`chain.js`, `product/model_map.js`, `inventory/neighbourhood.js`) carry
node widths, spacings and radii as inline numbers as well as colours. Those are R1
parameters by the same argument as the palette, and the same `Theme` object can hold them.
Bundle it with step 5 if the SVG classes are being reworked anyway.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
