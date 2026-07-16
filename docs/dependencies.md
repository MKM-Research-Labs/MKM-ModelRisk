# Dependency manifest

Every third-party package MKM-ModelRisk pulls in, with its licence, for review
through normal internal channels.

Two sets, and the distinction matters:

- **Runtime** — what a deployment installs (`pip install -e .`). These run in the
  hosting environment.
- **Development only** — test and tooling packages, pulled in by the `[dev]` extra
  (`pip install -e ".[dev]"`). They are never imported by the application and never
  reach a deployed instance.

Versions are those resolved at the time of writing against Python 3.13; the
declared floors live in [`pyproject.toml`](../pyproject.toml).

## Runtime (14)

Direct: `psycopg[binary]`, `flask`, `jsonschema`. The rest are transitive.

| Package | Version | Licence |
|---|---|---|
| attrs | 26.1.0 | MIT |
| blinker | 1.9.0 | MIT |
| click | 8.4.2 | BSD-3-Clause |
| flask | 3.1.3 | BSD-3-Clause |
| itsdangerous | 2.2.0 | BSD-3-Clause |
| jinja2 | 3.1.6 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| markupsafe | 3.0.3 | BSD-3-Clause |
| **psycopg** | 3.3.4 | **LGPL-3.0-only** — see [Licences needing a look](#licences-needing-a-look) |
| **psycopg-binary** | 3.3.4 | **LGPL-3.0-only** — same, via the `[binary]` extra |
| referencing | 0.37.0 | MIT |
| rpds-py | 2026.6.3 | MIT |
| werkzeug | 3.1.8 | BSD-3-Clause |

Verified by resolving `pip install -e .` into an empty Python 3.13 environment.
(`psycopg` and `referencing` declare `typing-extensions` only under
`python_version < "3.13"`; the project floor is 3.13, so it never enters the
runtime set.)

## Development only (20)

Direct: `pytest`, `pytest-cov`, `playwright`, `pytest-playwright`.

| Package | Version | Licence |
|---|---|---|
| certifi | 2026.6.17 | **MPL-2.0** |
| charset-normalizer | 3.4.9 | MIT |
| coverage | 7.14.2 | Apache-2.0 |
| greenlet | 3.5.3 | MIT AND PSF-2.0 |
| idna | 3.18 | BSD-3-Clause |
| iniconfig | 2.3.0 | MIT |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause |
| playwright | 1.60.0 | Apache-2.0 |
| pluggy | 1.6.0 | MIT |
| pyee | 13.0.1 | MIT |
| pygments | 2.20.0 | BSD-2-Clause |
| pytest | 9.1.1 | MIT |
| pytest-base-url | 2.1.0 | **MPL-2.0** |
| pytest-cov | 7.1.0 | MIT |
| pytest-playwright | 0.8.0 | Apache-2.0 |
| python-slugify | 8.0.4 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| **text-unidecode** | 1.3 | **Artistic-1.0 OR GPL-2.0-or-later** |
| typing-extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.7.0 | MIT |

## Licences needing a look

Most of the tree is MIT / BSD / Apache-2.0 / PSF — permissive, and unremarkable.
Four packages are not, and are called out here rather than left for a scanner to
find. None is presented as a blocker; each is a fact for counsel to weigh.

**`psycopg` and `psycopg-binary` — LGPL-3.0-only — runtime.** The PostgreSQL
driver, and the only copyleft licence in the runtime set. ModelRisk imports it
through its public API and does not modify, patch, or statically link it; the
`[binary]` extra ships prebuilt `libpq` wheels. LGPL-3.0 is a weak copyleft
licence whose reciprocity attaches to the library itself rather than to calling
code, and internal deployment is generally not "distribution" — but this is the
one dependency where that reasoning is worth confirming rather than assuming.

If the licence is unwelcome, the driver is replaceable. All database access is
already funnelled through the single `src/database/` utility (coding rule R6), so
the blast radius of swapping to a permissively-licensed driver is one module.

**`text-unidecode` — Artistic-1.0 OR GPL-2.0-or-later — development only.**
Reaches the tree four levels down: `pytest-playwright` → `python-slugify` →
`text-unidecode`. It is test tooling, never imported by the application, never
deployed. Dual-licensed, so the Artistic option is available. Worth naming because
"GPL" surfaces in any automated scan and is better explained than discovered.

**`certifi` and `pytest-base-url` — MPL-2.0 — development only.** File-level
copyleft, obligations attaching only to modified MPL files. Neither is modified.

## Regenerating this manifest

The versions above are a point-in-time resolution. To rebuild after a dependency
change:

```bash
pip install pip-licenses
pip-licenses --with-urls --format=markdown
```

That lists everything installed in the active environment; the runtime/dev split
above follows the closure of each root set in [`pyproject.toml`](../pyproject.toml).

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
