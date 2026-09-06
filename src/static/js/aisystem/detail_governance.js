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
// What an AI System answers to, which a model does not.
//
// Three loaders, each fetched on demand rather than served with the record: the legal
// regimes that apply to it, the configuration snapshots recording what it was actually
// running, and the operating envelope it must stay inside.
//
// They are together because they are one question asked at three depths — what are the
// rules, what was this thing when it ran, and what is it allowed to do. A reviewer
// reads them in that order, and an incident is investigated in the reverse one.
//
// The write side lives here too: recording a baseline run, setting the bar a trigger
// fires on, and sealing what a release contained. Those three commands existed in the
// domain from Phases 3-5 and had no route and no button, so the envelope panel could
// only ever read "not measured" -- which is the most flattering reading of the least
// evidence, and precisely what the envelope exists to prevent.
//
// Assigns onto AISystemDetail; loads after detail_core.js.

Object.assign(AISystemDetail, {

  // Which regimes bite, and why. Resolved server-side: applicability is config the
  // institution can extend, and a copy of the rules in the console would answer
  // differently the moment somebody added a regime.
  async _loadRegimes() {
    const box = document.getElementById("ais-regimes");
    if (!box) return;
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/regimes");
      if (!body.regimes.length) {
        box.className = "empty";
        box.textContent = "No regime applies on the markets recorded for this system.";
        return;
      }
      box.className = "";
      box.innerHTML = body.regimes.map((r) =>
        '<div class="inforow"><div class="k">' + esc(r.name) + '</div><div class="v">' +
        esc(r.because) + '<span class="muted" style="font-size:var(--size-xs)"> &middot; ' +
        r.clauses + " obligations</span></div></div>").join("");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  // The configuration history, with what moved at each version. Fetched rather than
  // read off the record: the record carries the CURRENT values, and the whole point of
  // the history is the gap between those and what was written down.
  async _loadSnapshots() {
    const box = document.getElementById("ais-snapshots");
    if (!box) return;
    const btn = document.getElementById("ais-snapshot");
    if (btn) {
      btn.onclick = () => App.amend(
        "Take a configuration snapshot of " + this.recordId() + ".", "POST",
        "/api/ai-systems/" + encodeURIComponent(this.recordId()) + "/snapshots", {},
        () => this.refresh());
    }
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/snapshots");
      if (!body.snapshots.length) {
        box.className = "empty";
        box.textContent = "No snapshot taken. The configuration is whatever the fields " +
          "above say today, with nothing recording what it was before.";
        return;
      }
      box.className = "";
      box.innerHTML = body.snapshots.slice().reverse().map((s) => {
        const moved = (s.changed || []).length
          ? (s.changed || []).map((c) => "<code>" + esc(c.field) + "</code> " +
              esc(String(c.before == null || c.before === "" ? "—" : c.before)) +
              " &rarr; " + esc(String(c.after == null || c.after === "" ? "—" : c.after))
            ).join("<br>")
          : '<span class="muted">first snapshot</span>';
        return '<div class="inforow"><div class="k">v' + esc(s.config_version) +
          '<div class="muted" style="font-size:var(--size-xs)">' +
          esc(String(s.taken_at || "").replace("T", " ").slice(0, 16)) +
          "</div></div><div class=\"v\">" + moved + "</div></div>";
      }).join("");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  // The envelope, read against the configuration in force now. Staleness comes from
  // the server: a console deciding it here would decide it differently from the report.
  async _loadEnvelope() {
    const box = document.getElementById("ais-envelope");
    if (!box) return;
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/envelope");
      const e = body.envelope;
      if (!e) {
        box.className = "empty";
        box.textContent = "No envelope measured. How much this system's output varies " +
          "under a fixed configuration is unrecorded.";
        return;
      }
      box.className = "";
      const limits = e.limits
        ? Object.keys(e.limits).sort((a, b) => a - b)
            .map((p) => "p" + esc(p) + " " + Math.round(e.limits[p] * 10000) / 10000)
            .join(" &ndash; ")
        : "&mdash;";
      // Stale and refused are both findings, not gaps, and are coloured as such.
      const tone = e.status === "ok" ? "green" : "amber";
      box.innerHTML = '<div class="inforow"><div class="k">Envelope</div><div class="v">' +
        limits + ' <span class="badge" style="background:' + Theme.value(tone) + '">' +
        esc(e.status) + "</span>" +
        '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">' +
        esc(e.runs) + " runs, configuration v" + esc(e.config_version) +
        (e.detail ? " &mdash; " + esc(e.detail) : "") + "</div></div></div>";
    } catch (err) {
      box.className = "empty";
      box.textContent = err.message;
    }
  },

  // --- Recording a baseline run --------------------------------------------
  // The scores go up raw and the envelope is computed server-side. A screen that
  // asked for a range would be asking the owner to answer the question the
  // measurement exists to ask.
  _envelopeControls() {
    if (this._record.retired) return "";
    return '<div class="row" style="align-items:center;gap:var(--space-3);' +
      "margin-top:var(--space-4)\">" +
      '<input id="ais-runs" style="flex:1;min-width:320px" ' +
      'placeholder="Scores from repeated runs of the same input, comma separated">' +
      '<button class="btn small primary" id="ais-record-runs">Record a baseline' +
      "&hellip;</button></div>" +
      '<p class="muted" style="font-size:var(--size-xs);margin:var(--space-2) 0 0">' +
      "Fewer runs than the minimum is refused rather than narrowed: a tight range " +
      "from a handful of runs reads as a well-behaved system.</p>";
  },

  _bindEnvelopeControls() {
    const btn = document.getElementById("ais-record-runs");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const raw = (document.getElementById("ais-runs") || {}).value || "";
      const scores = raw.split(",").map((s) => s.trim()).filter(Boolean).map(Number);
      if (!scores.length || scores.some(isNaN)) {
        App.toast("Enter the score from each run, separated by commas.", "error");
        return;
      }
      App.amend("Record a variability envelope for " + self.recordId() +
        " from " + scores.length + " runs.", "POST",
        "/api/ai-systems/" + encodeURIComponent(self.recordId()) + "/envelope",
        { scores: scores }, () => self.refresh());
    };
  },

  // --- Trigger thresholds ---------------------------------------------------
  // One row per property the institution declared, whether or not a bar is set:
  // a property with no threshold is the gap worth seeing, and a table that listed
  // only what was configured would hide exactly that.
  _triggersPanel(d) {
    const held = d.trigger_thresholds || {};
    const props = (this._specs.trigger_properties || Object.keys(held));
    if (!props.length) return '<div class="empty">No trigger properties configured.</div>';
    const rows = props.map((p) => {
      const t = held[p] || {};
      const bar = (t.threshold === undefined || t.threshold === null)
        ? '<span class="badge" style="background:var(--amber)">not set</span>'
        : esc(String(t.threshold));
      return "<tr><td>" + esc(p) + "</td><td>" + bar + "</td><td>" +
        fieldDisplay(t.fallback) + "</td><td>" + fieldDisplay(t.rationale) + "</td></tr>";
    }).join("");
    return "<table><thead><tr><th>Property</th><th>Threshold</th>" +
      "<th>When it breaks</th><th>Why this bar</th></tr></thead><tbody>" +
      rows + "</tbody></table>" +
      (this._record.retired ? "" :
        '<button class="btn small primary" id="ais-set-threshold" ' +
        'style="margin-top:var(--space-4)">Set a threshold&hellip;</button>');
  },

  _bindTriggers() {
    const btn = document.getElementById("ais-set-threshold");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const prop = window.prompt("Which property? (" +
        (self._specs.trigger_properties || []).join(", ") + ")");
      if (!prop) return;
      const bar = window.prompt("The bar it is judged against:");
      if (!bar) return;
      const fallback = window.prompt("What happens when it breaks? (" +
        (self._specs.fallback_states || []).join(" / ") + ")");
      if (!fallback) return;
      App.amend("Set the " + prop + " threshold on " + self.recordId() + " to " + bar +
        ", falling back to: " + fallback + ".", "POST",
        "/api/ai-systems/" + encodeURIComponent(self.recordId()) + "/thresholds",
        { property_name: prop, threshold: Number(bar), fallback: fallback,
          rationale: window.prompt("Why this bar? (optional)") || "" },
        () => self.refresh());
    };
  },

  // --- Release manifests ----------------------------------------------------
  _releasesPanel(d) {
    const sealed = d.release_manifests || [];
    const add = this._record.retired ? "" :
      '<button class="btn small primary" id="ais-seal-release" ' +
      'style="margin-top:var(--space-4)">Seal a release&hellip;</button>';
    if (!sealed.length) {
      return '<div class="empty">No release sealed yet.</div>' + add;
    }
    const rows = sealed.map((m) =>
      "<tr><td>" + '<span class="code">' + esc(m.release || "") + "</span></td><td>" +
      fieldDisplay(m.change_class) + "</td><td>" + fieldDisplay(m.sealed_at) +
      "</td><td>" + fieldDisplay(m.note) + "</td></tr>").join("");
    return "<table><thead><tr><th>Release</th><th>Change class</th>" +
      "<th>Sealed</th><th>Note</th></tr></thead><tbody>" + rows +
      "</tbody></table>" + add;
  },

  _bindReleases() {
    const btn = document.getElementById("ais-seal-release");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const release = window.prompt("Which release? (a version or a tag)");
      if (!release) return;
      const cls = window.prompt("Change class for this release: " +
        (self._specs.change_classes || []).join(" / "));
      if (!cls) return;
      App.amend("Seal the manifest for release " + release + " on " + self.recordId() +
        " as a " + cls + " change. A sealed manifest is never edited again.", "POST",
        "/api/ai-systems/" + encodeURIComponent(self.recordId()) + "/release-manifest",
        { release: release, change_class: cls,
          note: window.prompt("What did it contain? (optional)") || "" },
        () => self.refresh());
    };
  },
});
