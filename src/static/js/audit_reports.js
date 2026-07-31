// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// Audit Reports tab: the generated artefacts, split into two sub-tabs because the
// tab has two audiences that share nothing but the Generate button — whoever governs
// the estate (User: its reports and the guides) and whoever maintains the code (Code:
// the R1-R10 rule evidence and the test artefacts). Which group an artefact belongs to
// is the API's answer (config/audit.py), not this file's.
const AuditReports = {
  _tab: "user",
  _TABS: [["user", "User"], ["code", "Code"]],
  _BLURB: {
    user: "The reports the institution publishes about its own estate, and the guides " +
      "that come with the console.",
    code: "The coding-rule audit: one report per rule (R1&ndash;R10), the consolidated " +
      "overview, and the test evidence behind R3 &mdash; coverage (XML + browsable HTML), " +
      "JUnit results and the Test Report.",
  },
  _reports: [],

  async render() {
    this._reports = await App.get("/api/audit-reports");
    const bar = this._TABS.map(([k, label]) =>
      '<button class="dtab' + (k === this._tab ? " active" : "") + '" data-rtab="' + k + '">' +
      label + "</button>").join("");
    const el = document.getElementById("tab-reports");
    el.innerHTML =
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">Audit reports</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="ar-generate">Generate reports</button></div>' +
      '<p class="muted">Generate produces every artefact below in one click, under both ' +
      "tabs. The test suite then runs in the background, adding coverage, JUnit results " +
      "and the Test Report. Files are written to uploads/audit/ (gitignored).</p>" +
      '<p class="muted" id="ar-cov-note"></p>' +
      '<div class="dtabs">' + bar + '</div><div id="ar-body"></div></div>';
    el.querySelectorAll("[data-rtab]").forEach((btn) => {
      // Switching sub-tab re-draws from what was already fetched — no round trip.
      btn.onclick = () => {
        this._tab = btn.getAttribute("data-rtab");
        el.querySelectorAll("[data-rtab]").forEach((b) =>
          b.classList.toggle("active", b === btn));
        this._draw();
      };
    });
    document.getElementById("ar-generate").onclick = () => this._generate();
    this._draw();
    this._resumeCoverage();          // reflect an in-flight coverage refresh, if any
  },

  // The selected group's artefacts. Sorted by filename with numeric collation, which
  // is what puts the rule reports first and in rule order (R2 before R10, not after
  // R1) without this file having to know the set of rules.
  _draw() {
    const cards = this._reports
      .filter((r) => r.group === this._tab)
      .sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true }))
      .map((r) => this._card(r)).join("");
    document.getElementById("ar-body").innerHTML =
      '<p class="muted">' + this._BLURB[this._tab] + "</p>" +
      (cards
        ? '<div class="rgrid" style="margin-top:var(--space-6)">' + cards + "</div>"
        : '<div class="empty">Nothing generated yet. Click \u201cGenerate reports\u201d.</div>');
  },

  // One artefact card. The coverage HTML report opens its own page (r.href);
  // PDFs render inline, other artefacts (XML/JSON/TXT) download.
  _card(r) {
    const badge = r.type ? '<span class="pill">' + esc(r.type) + "</span> " : "";
    const meta = '<div class="rmeta">' + badge + esc(r.filename) + " &middot; " +
      fmtSize(r.size) + " &middot; " + esc((r.modified || "").slice(0, 10)) + "</div>";
    let actions;
    if (r.href) {
      actions = '<a class="btn small primary" href="/api/audit-reports/' + esc(r.href) +
        '" target="_blank">Open</a>';
    } else {
      const url = "/api/audit-reports/" + esc(r.filename);
      const view = r.type === "PDF"
        ? '<a class="btn small primary" href="' + url + '" target="_blank">View</a>'
        : "";
      actions = view + '<a class="btn small" href="' + url + '" download>Download</a>';
    }
    return '<div class="rcard"><div class="rlabel">' + esc(r.label) + "</div>" + meta +
      '<div class="row" style="margin-top:var(--space-5)">' + actions + "</div></div>";
  },

  // Poll the background coverage refresh: show progress, and re-render (so the
  // R3 report picks up its new timestamp/coverage) once it finishes.
  _resumeCoverage() {
    fetch("/api/audit-reports/coverage-status").then((r) => r.json()).then((s) => {
      if (s.running) { this._covActive = true; this._pollCoverage(); }
    }).catch(() => {});
  },

  _pollCoverage() {
    const tick = () => {
      fetch("/api/audit-reports/coverage-status").then((r) => r.json()).then((s) => {
        const note = document.getElementById("ar-cov-note");
        if (s.running) {
          if (note) note.textContent = "Coverage refreshing (running the test suite, ~1 min)…";
          setTimeout(tick, 3000);
        } else if (this._covActive) {
          this._covActive = false;
          if (s.error) {
            if (note) note.textContent = "Coverage refresh failed: " + s.error;
          } else {
            App.toast("Coverage report updated", "ok");
            this.render();
          }
        }
      }).catch(() => {});
    };
    tick();
  },

  _generate() {
    const btn = document.getElementById("ar-generate");
    btn.disabled = true;
    btn.textContent = "Generating…";
    fetch("/api/audit-reports/generate", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() },
    }).then(async (res) => {
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.error || "generation failed");
      }
      const failures = body.failures || [];
      if (failures.length) {
        // Some reports were refreshed, others failed and kept their old file
        // (and old date) — name them so a stale card is never a silent surprise.
        App.toast("Some reports failed to regenerate: " +
          failures.map((f) => f.file).join(", "), "error");
      } else {
        App.toast("Reports generated", "ok");
      }
      this._covActive = true;          // generate() kicked off a coverage refresh
      this.render();
      this._pollCoverage();
    }).catch((e) => {
      App.toast(e.message, "error");
      btn.disabled = false;
      btn.textContent = "Generate reports";
    });
  },
};
