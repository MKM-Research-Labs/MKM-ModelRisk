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

// The Evidence tab: what the system's runs have left on record.
//
// Three registers, one per concept that had nowhere to put its evidence
// (config/governance/_ai_evidence.py): references to run traces, runs of the stress-test
// suite, and calibrations of the judge against expert grading. Every verdict shown here —
// complete or not, passed or not, inside the level or not — was worked out by the server
// from what was sent; the console only draws it and sends raw material.
//
// Traces are written by the system's observability pipeline (POST .../traces), not typed,
// so there is no button for them. The stress-test cases are an ordinary register, drawn
// by the shared collection renderer beneath the runs.
//
// Assigns onto AISystemDetail; loads after detail_governance_edit.js.

Object.assign(AISystemDetail, {

  _evidenceTab() {
    const d = this._record.data || {};
    return this._coveragePanel(this._record.coverage) +
      '<div class="section-header" style="margin-top:var(--space-8)">Run traces</div>' +
      this._lead("Where each evidential run's trace lives, its content hash, and whether " +
                 "it holds everything a system of this autonomy owes. Recorded by the " +
                 "observability pipeline, never typed.") +
      this._tracesTable(d.run_traces || []) +
      '<div class="section-header" style="margin-top:var(--space-8)">Stress-test runs</div>' +
      this._lead("Each run of the whole suite, judged case by case against what the " +
                 "system should have done. The suite's version moves on its own when " +
                 "its cases change.") +
      this._stressRunsTable(d.stress_test_runs || []) + this._stressRunControls(d) +
      '<div class="section-header" style="margin-top:var(--space-8)">Judge calibration</div>' +
      this._lead("Experts and the judge grade the same items. The first calibration " +
                 "sets the level; one that falls below it suspends reliance on the " +
                 "judge until another clears it.") +
      this._calibrationTable(d.judge_calibrations || []) + this._calibrationControls() +
      '<div id="ais-stress-cases" style="margin-top:var(--space-8)"></div>';
  },

  // Property coverage, resolved server-side on every read (ai_system/coverage.py). Four
  // tiles — one per property — then the nine concepts that feed them. A concept the
  // system is not asked for (by its grid band, or its autonomy) is shown dimmed rather
  // than hidden: "not asked" is an answer a reviewer should be able to see given.
  _coveragePanel(cov) {
    if (!cov) return "";
    const tone = {"rests on live evidence": "green", "partly evidenced": "amber",
                  "not evidenced": "red"};
    const concept = {live: "green", stale: "amber", failing: "red"};
    const tiles = Object.keys(cov.properties).map((p) => {
      const v = cov.properties[p];
      const bg = tone[v.status] ? Theme.value(tone[v.status]) : Theme.value("grey");
      return '<div class="card" style="flex:1;min-width:150px;padding:var(--space-4)">' +
        '<div class="section-header" style="margin:0">' + esc(p) + "</div>" +
        '<span class="badge" style="background:' + bg + '">' + esc(v.status) + "</span>" +
        (v.gaps.length ? '<div class="muted" style="font-size:var(--size-xs);' +
          'margin-top:var(--space-2)">gaps: concepts ' + esc(v.gaps.join(", ")) + "</div>"
          : "") + "</div>";
    }).join("");
    const rows = cov.concepts.map((c) =>
      "<tr" + (c.asked ? "" : ' class="muted"') + "><td>" + esc(c.number) + ". " +
      esc(c.name) + '<div class="muted" style="font-size:var(--size-xs)">' +
      esc(c.phase) + "</div></td><td>" + (concept[c.status]
        ? '<span class="badge" style="background:' + Theme.value(concept[c.status]) +
          '">' + esc(c.status) + "</span>" : esc(c.status)) +
      (c.asked ? "" : ' <span class="pill">not asked</span>') + "</td><td>" +
      esc(c.detail) + "</td></tr>").join("");
    return '<div class="section-header">Property coverage</div>' +
      this._lead("Which of the four properties rest on evidence about the system as " +
                 "configured now. Held to " + esc(cov.held_to) +
                 (cov.placed ? "" : " &mdash; place the system on the grid (Overview) " +
                   "to be held only to what its band asks") + ".") +
      '<div class="row" style="gap:var(--space-4);flex-wrap:wrap">' + tiles + "</div>" +
      '<table style="margin-top:var(--space-5)"><thead><tr><th>Concept</th>' +
      "<th>Evidence</th><th>What it says</th></tr></thead><tbody>" + rows +
      "</tbody></table>";
  },

  _badge(ok, yes, no) {
    return '<span class="badge" style="background:' + Theme.value(ok ? "green" : "amber") +
      '">' + esc(ok ? yes : no) + "</span>";
  },

  _tracesTable(rows) {
    if (!rows.length) return '<div class="empty">No trace recorded.</div>';
    const labels = this._specs.trace_content_labels || {};
    return "<table><thead><tr><th>Run</th><th>Config</th><th>Purpose</th>" +
      "<th>Complete</th><th>Hash</th></tr></thead><tbody>" +
      rows.slice().reverse().map((t) => "<tr><td>" + '<span class="code">' +
        esc(t.run_id) + "</span><div class=\"muted\" style=\"font-size:var(--size-xs)\">" +
        esc(t.trace_uri) + "</div></td><td>v" + esc(t.config_version) + "</td><td>" +
        esc(t.purpose) + "</td><td>" + this._badge(t.complete, "complete", "incomplete") +
        (t.missing && t.missing.length
          ? '<div class="muted" style="font-size:var(--size-xs)">missing ' +
            esc(t.missing.map((m) => labels[m] || m).join(", ")) + "</div>" : "") +
        '</td><td><span class="code">' + esc(String(t.content_hash).slice(0, 12)) +
        "&hellip;</span></td></tr>").join("") + "</tbody></table>";
  },

  _stressRunsTable(rows) {
    if (!rows.length) return '<div class="empty">The suite has never been run.</div>';
    return "<table><thead><tr><th>Suite</th><th>Occasion</th><th>Config</th>" +
      "<th>Result</th><th>Run</th></tr></thead><tbody>" +
      rows.slice().reverse().map((r) => "<tr><td>v" + esc(r.suite_version) + "</td><td>" +
        esc(r.occasion) + "</td><td>v" + esc(r.config_version) + "</td><td>" +
        this._badge(r.passed, "passed", (r.failed || []).length + " failed") +
        (r.failed && r.failed.length ? ' <span class="muted">' +
          esc(r.failed.join(", ")) + "</span>" : "") + "</td><td>" +
        fieldDisplay(r.run_at) + "</td></tr>").join("") + "</tbody></table>";
  },

  // One select per case, then one button: a run is the whole suite or nothing.
  _stressRunControls(d) {
    const cases = d.stress_test_cases || [];
    if (this._record.retired || !cases.length) return "";
    const labels = this._specs.stress_response_labels || {};
    const opts = '<option value=""></option>' + (this._specs.stress_responses || [])
      .map((r) => '<option value="' + esc(r) + '">' + esc(labels[r] || r) + "</option>")
      .join("");
    return '<div style="margin-top:var(--space-4)">' + cases.map((c) =>
      '<div class="row" style="align-items:center;gap:var(--space-3)">' +
      '<span class="code">' + esc(c.item_id) + '</span><span style="flex:1">' +
      esc(c.scenario) + '</span><select data-stress-case="' + esc(c.item_id) + '">' +
      opts + "</select></div>").join("") +
      '<div class="row" style="gap:var(--space-3);margin-top:var(--space-3)">' +
      '<select id="ais-stress-occasion">' + (this._specs.stress_occasions || [])
        .map((o) => '<option>' + esc(o) + "</option>").join("") + "</select>" +
      '<button class="btn small primary" id="ais-record-stress">Record this run' +
      "&hellip;</button></div></div>";
  },

  _calibrationTable(rows) {
    if (!rows.length) return '<div class="empty">No calibration recorded.</div>';
    return "<table><thead><tr><th>Judge</th><th>Dimension</th><th>Items</th>" +
      "<th>Agreement</th><th>Level</th><th>Recorded</th></tr></thead><tbody>" +
      rows.slice().reverse().map((c) => '<tr><td><span class="code">' +
        esc(c.judge_ai_system_id) + "</span></td><td>" + esc(c.dimension) + "</td><td>" +
        esc(c.sample_size) + "</td><td>" + esc(Math.round(c.agreement * 100)) + "%</td><td>" +
        (c.is_baseline ? '<span class="pill">sets the level</span>'
          : this._badge(c.within_baseline, "inside", "outside — judge suspended")) +
        "</td><td>" + fieldDisplay(c.recorded_at) + "</td></tr>").join("") +
      "</tbody></table>";
  },

  _calibrationControls() {
    if (this._record.retired) return "";
    return '<div class="row" style="gap:var(--space-3);margin-top:var(--space-4)">' +
      '<input id="ais-cal-judge" placeholder="Judge (AI System id)" style="width:180px">' +
      '<select id="ais-cal-dim">' + (this._specs.ace_dimensions || [])
        .map((x) => "<option>" + esc(x) + "</option>").join("") + "</select>" +
      '<input id="ais-cal-pairs" style="flex:1;min-width:280px" placeholder="' +
      "expert:judge per item, comma separated &mdash; e.g. 5:5, 4:5, 3:1\">" +
      '<button class="btn small primary" id="ais-record-cal">Record&hellip;</button></div>';
  },

  _bindEvidence() {
    const self = this;
    const id = encodeURIComponent(this.recordId());
    const stress = document.getElementById("ais-record-stress");
    if (stress) stress.onclick = function () {
      const observed = {};
      document.querySelectorAll("[data-stress-case]").forEach((s) => {
        observed[s.getAttribute("data-stress-case")] = s.value;
      });
      App.amend("Record a stress-test run on " + self.recordId() + ".", "POST",
        "/api/ai-systems/" + id + "/stress-runs",
        { occasion: document.getElementById("ais-stress-occasion").value,
          observed: observed }, () => self.refresh());
    };
    const cal = document.getElementById("ais-record-cal");
    if (cal) cal.onclick = function () {
      const pairs = document.getElementById("ais-cal-pairs").value.split(",")
        .map((p) => p.trim()).filter(Boolean).map((p) => {
          const [e, j] = p.split(":");
          return { expert: (e || "").trim(), judge: (j || "").trim() };
        });
      App.amend("Record a judge calibration on " + self.recordId() + " from " +
        pairs.length + " items.", "POST", "/api/ai-systems/" + id + "/calibrations",
        { judge_ai_system_id: document.getElementById("ais-cal-judge").value.trim(),
          dimension: document.getElementById("ais-cal-dim").value, pairs: pairs },
        () => self.refresh());
    };
    // The cases register, drawn by the shared renderer into its own box.
    const box = document.getElementById("ais-stress-cases");
    if (box) {
      box.innerHTML = Collections.render(this._record.data || {},
        {collections: [this.collSpec("stress_test_cases")]}, this._record.retired,
        false, false);
      this.bindCollections(["stress_test_cases"]);
    }
  },
});
