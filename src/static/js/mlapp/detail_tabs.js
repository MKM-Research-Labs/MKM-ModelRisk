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
// ML Application detail: what each tab draws.
//
// One dispatcher and one body per tab. Split from detail_core when the file passed 700
// lines: the difference between "what an ML Application is" and "what the Trains tab
// puts on screen" is the difference between changing the record and changing a view of
// it, and they were being changed for different reasons in the same place.
//
// The Trains table lives here rather than with detail_training because it is the other
// tab: Training shows one fit in six sections, Trains shows the sequence.
//
// Loads after detail_core.js, which defines MLAppDetail.

Object.assign(MLAppDetail, {


  _renderContent() {
    const d = this._record.data || {};
    const box = document.getElementById("mla-content");
    if (this._tab === "overview") { box.innerHTML = this._overview(); this._bindEdits(); return; }
    if (this._tab === "training") {
      // Testing evidence sits here, beside the record's other technical facts, exactly
      // where an AI System keeps it. It used to be on the Review tab, which is now the
      // staged review itself — and validation status and test coverage are properties
      // of the build, not steps of a review.
      box.innerHTML = this._trainingSections(d) +
        '<div class="section-header" style="margin-top:var(--space-8)">Testing evidence</div>' +
        this._TESTING_FIELDS.map((k) => this._row(k)).join("");
      this._bindEdits();
      this._bindFirstTrain();
      this._bindSectionRail();
      this._bindTrainEdits(d);
      this._bindArtefacts();
      this._bindWhy();
      return;
    }
    if (this._tab === "risk") {
      box.innerHTML =
        '<div class="section-header">Risk assessment</div>' +
        '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">The owner sets these; they ' +
        "place the ML Application on the heatmap below, which becomes its rating once the " +
        "MRC signs it off.</p>" +
        policyNotice(d.division) +
        this.riskTable() +
        DetailTabs.risk(this._risk, false, d.division);  // events are product-only
      this._bindEdits();
      return;
    }
    if (this._tab === "changes") {
      box.innerHTML = '<div id="mla-changes"></div>';
      Changes.render("ml_application", this.recordId(), "mla-changes",
                     this._record.retired);
      return;
    }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "training_runs") {
      box.innerHTML =
        '<div class="section-header">Monitoring</div>' +
        this._TRAINS_FIELDS.map((k) => this._row(k)).join("") +
        '<div class="section-header" style="margin-top:var(--space-8)">Trains</div>' +
        '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">Every fit, each with ' +
        "its own snapshot, seed and metrics. There is no version: the record of change " +
        "is this sequence, and the Training tab shows the most recent one in full.</p>" +
        this._trainsTable(d);
      this._bindEdits();
      this._bindAddTrain();
      return;
    }
    if (this._tab === "linkage") {
      const signoffs = d.signoff_history || [];
      box.innerHTML = signoffs.length
        ? DetailTabs.signoffHistory(signoffs, d.division)
        : '<div class="section-header">Sign-off history</div>' +
          '<div class="empty">No MRC sign-offs granted yet.</div>';
      return;
    }
    if (this._tab === "docs") {
      // The record's own evidence pack, plus the ML Application Document generated
      // from the current record. Generated on request rather than filed as a row
      // that could go stale -- and every issued copy is kept under History, so the
      // trail shows what the record said on the day the document went out.
      const id = this._record.ml_application_id;
      box.innerHTML =
        '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:var(--space-5)">' +
        '<span class="muted" style="font-size:var(--size-sm)">The full write-up for this ML ' +
        "Application \u2014 its use case, the estimator it is built on, what it was trained " +
        "on, and every register \u2014 generated from the current record.</span>" +
        '<span><a class="btn small primary" target="_blank" rel="noopener" id="mla-issue" ' +
        'href="/api/ml-applications/' + encodeURIComponent(id) + '/document.pdf">' +
        "ML Application Document (PDF)</a></span></div>" +
        '<div id="mladocs-host"></div>';
      ModelDocs.render(id, d.documents || [], this._specs.doc_tab_categories || [],
        this._record.retired, "/api/ml-applications/", () => this.refresh(), "mladocs-host");
      // Fetch the PDF ourselves so we know when the server has finished generating
      // and filing it, then refresh so the History copy appears at once. The tab is
      // opened inside the click so the browser does not treat it as a pop-up.
      const issue = document.getElementById("mla-issue");
      if (issue) {
        issue.addEventListener("click", async (e) => {
          e.preventDefault();
          const win = window.open("", "_blank");
          try {
            const res = await fetch(issue.getAttribute("href"), { headers: App.headers() });
            if (!res.ok) throw new Error("The document could not be generated.");
            if (win) win.location = URL.createObjectURL(await res.blob());
            await this.refresh();
          } catch (err) {
            if (win) win.close();
            App.toast(err.message || "Document generation failed.", "error");
          }
        });
      }
      return;
    }
    // Retiring an ML Application is the MRC's decision, exactly as it is for a model,
    // so the tab is DangerZone's three states rather than a button of its own.
    if (this._tab === "danger") {
      box.innerHTML = DangerZone.content("ML Application", this._record);
      DangerZone.bind({
        api: "/api/ml-applications", id: this.recordId(),
        onDone: () => { this.show(this.recordId(), "danger"); MLApps.loadList(); },
      });
      return;
    }
    if (this._tab === "review") {
      // The shared review panel: the same seven stages, interim approvals, record of
      // challenge and sign-off a model's review runs. This tab used to be the testing
      // fields plus a flat question list, which is not a review — nothing recorded how
      // far through one had got, and nothing carried the reviewer's verdict.
      box.innerHTML = this._reviewTab(d);
      this._bindReviewRail();
      return;
    }
    // Everything else is an ordinary spec-driven collection.
    this.renderCollection(this._tab, {autosave: this._tab === "review"});
  },

  // --- Trains ---------------------------------------------------------------
  // A view over the fits: enough of each to tell them apart and to see metric drift
  // between them, which is the question the sequence exists to answer.
  _trainsTable(d) {
    const runs = d[this._specs.training.collection] || [];
    const add = this._record.retired ? "" :
      '<button class="btn small primary" id="mla-add-train">+ Record a train</button>';
    if (!runs.length) {
      return '<div class="empty">No trains recorded yet.</div>' + add;
    }
    const rows = runs.map((r) =>
      "<tr><td>" + '<span class="code">' + esc(r.fit_id || r.item_id) + "</span></td>" +
      "<td>" + fieldDisplay(r.run_date) + "</td>" +
      "<td>" + fieldDisplay(r.learning_task) + "</td>" +
      "<td>" + fieldDisplay(r.snapshot_id) + "</td>" +
      "<td>" + fieldDisplay(r.primary_metric) + "</td>" +
      "<td>" + fieldDisplay(r.metric_test) + "</td></tr>").join("");
    return "<table><thead><tr><th>Train</th><th>Run date</th><th>Task</th>" +
      "<th>Snapshot</th><th>Metric</th><th>On test</th></tr></thead><tbody>" +
      rows + "</tbody></table>" + add;
  },

  _bindAddTrain() {
    const btn = document.getElementById("mla-add-train");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const id = window.prompt("Identifier for this train (a fit id, commit or run name):");
      if (!id) return;
      App.amend("Record train " + id + " on " + self._record.ml_application_id + ".",
        "POST", "/api/ml-applications/" +
        encodeURIComponent(self._record.ml_application_id) + "/collections/" +
        self._specs.training.collection, { fields: { fit_id: id } },
        () => self.refresh());
    };
  },
});
