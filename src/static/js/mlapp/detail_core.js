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
// ML Application detail: the master-detail counterpart to the list in mlapp.js.
//
// The same nine tabs a model carries, less Connections -- an ML Application has no
// dependency chain, so there is no graph to draw. Everything drawn here comes from
// shared components (DetailShell, DetailTabs, Collections); what this file holds is
// which tabs exist and what each one is for.
const MLAppDetail = {
  _record: null,
  _tab: "overview",
  _specs: null,
  _audit: [],
  _risk: null,

  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  async show(id) {
    this._specs = MLApps._specs || await MLApps.specs();
    const [record, audit, risk] = await Promise.all([
      App.get("/api/ml-applications/" + encodeURIComponent(id)),
      App.get("/api/audit"),
      App.get("/api/ml-applications/" + encodeURIComponent(id) + "/risk-rating"),
    ]);
    this._record = record;
    this._audit = audit.filter((e) => e.aggregate_id === id);
    this._risk = risk;
    this._tab = "overview";
    document.getElementById("mlapp-listview").classList.add("hidden");
    this._render();
  },

  close() {
    document.getElementById("mlapp-detail").innerHTML = "";
    document.getElementById("mlapp-listview").classList.remove("hidden");
    MLApps.loadList();
  },

  async refresh() { await this.show(this._record.ml_application_id); },

  _render() {
    const d = this._record.data || {};
    document.getElementById("mlapp-detail").innerHTML =
      '<div class="card">' + this._header(d) + this._tabbar(d) +
      '<div id="mla-content" style="margin-top:14px"></div></div>';
    document.getElementById("mla-close").onclick = () => this.close();
    document.querySelectorAll("[data-mlatab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-mlatab"); this._renderContent(); };
    });
    this._renderContent();
  },

  _header(d) {
    return '<div class="row" style="align-items:center">' +
      "<h3 style=\"margin:0\">" + esc(this._record.ml_application_id) + " — " +
      fieldDisplay(d.name) + "</h3>" +
      '<span style="margin-left:10px">' + tierBadge(d.tier, d.division) + " " +
      ragBadge(d.rag_rating, d.division) + " " +
      (this._record.retired ? '<span class="pill">retired</span>'
        : optionLabel(MLApps.fieldSpec("lifecycle_stage"), d.lifecycle_stage)) + "</span>" +
      '<span style="flex:1"></span><button class="btn small ghost" id="mla-close">Close</button>' +
      "</div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const asked = d.ml_review_questions || [];
    const cov = asked.filter((q) => q.status === "Addressed").length + "/" + asked.length;
    return DetailShell.tabBar([
      ["overview", "Overview", null],
      // A retrain is this record's substantial change -- the same collection a model
      // versions through, under the word that actually describes what happened.
      ["version_history", "Retrains", n("version_history")],
      ["review", "Review", cov],
      ["risk", "Risk Rating", null],
      ["linkage", "MRC linkage", n("signoff_history")],
      ["docs", "Docs", DocLinks.countIn(d.documents, this._specs.doc_tab_categories)],
      ["danger", "Danger", null],
      ["audit", "Audit", this._audit.length],
    ], this._tab, "data-mlatab");
  },

  // Which fields sit where on the Overview, following the model and product screens
  // rather than a layout of this screen's own: a full-width summary, then record
  // details on the left and Governance on the right.
  //
  // The risk assessment is NOT here. It lives on the Risk Rating tab beside the grid
  // it drives -- one row per dimension in the Admin editor's Dimension / Rating /
  // Rationale columns -- exactly as a model's and a product's do. Only the headline
  // rag_rating stays on Overview.
  _LEFT: [
    ["ML Application", ["name", "short_name", "use_case"]],
    ["Estimator", ["estimator", "estimator_version", "estimator_rationale"]],
    ["Training and performance",
     ["training_data", "training_period", "performance", "benchmark", "misinterpretation"]],
    ["Organisation", ["division", "line_of_business"]],
    ["Monitoring", ["monitoring_approach"]],
  ],
  _RIGHT: [
    ["Governance",
     ["rag_rating", "owner", "peer_reviewer", "lifecycle_stage", "validation_status",
      "version", "review_frequency", "mrc_signoff_date", "next_review_date",
      "last_review_date"]],
  ],

  _editLink(key) {
    return this._record.retired
      ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
  },

  _row(key) {
    const d = this._record.data || {};
    const spec = MLApps.fieldSpec(key);
    if (!spec) return "";
    // Through the spec, so a status vocabulary shows its label rather than the word
    // the record stores; and through the shared value cell, so a risk dimension shows
    // the band the division defined rather than the score behind it.
    const shared = DetailShell.fieldValue(key, spec, d);
    return DetailShell.row(key, riskFieldLabel(spec, d.division),
                           shared === null ? optionLabel(spec, d[key]) : shared,
                           !this._record.retired);
  },

  // Every Overview field is editable in place, through the shared editor the model and
  // product screens use. Nothing here is confirmation-gated yet: the MRC route for an
  // ML Application arrives with phase 4, and until then a rating change applies
  // directly rather than pretending to be routed somewhere.
  _bindEdits() {
    if (this._record.retired) return;
    const self = this;
    const d = this._record.data || {};
    document.querySelectorAll("#mla-content [data-edit]").forEach(function (btn) {
      const key = btn.getAttribute("data-edit");
      btn.onclick = function () {
        DetailShell.fieldEditor({
          scope: "#mla-content", prefix: "mlaed", spec: MLApps.fieldSpec(key),
          current: d[key], division: d.division, withSave: true,
          onCancel: () => self._renderContent(),
          onSave: (value, shown) => {
            App.amend("Set " + MLApps.fieldSpec(key).label + ' = "' + shown + '" on ' +
              self._record.ml_application_id + ".", "POST",
              "/api/ml-applications/" + encodeURIComponent(self._record.ml_application_id) +
              "/field", { field: key, value: value },
              () => self.refresh());
          },
        });
      };
    });
  },

  _overview() {
    const d = this._record.data || {};
    const self = this;
    const section = ([title, keys]) => DetailShell.section(title, keys, (k) => self._row(k));
    // A full-width summary of what the ML Application does, spanning both columns --
    // the same shape a model's Overview opens with.
    const summary = DetailShell.row("description", "Summary", fieldDisplay(d.description),
                                    !this._record.retired);
    return '<div style="margin-bottom:14px">' + summary + "</div>" +
      '<div class="grid2"><div>' + this._LEFT.map(section).join("") + "</div>" +
      "<div>" + this._RIGHT.map(section).join("") + "</div></div>" +
      DetailShell.retiredFlag(this._record.retired);
  },

  // The risk assessment, through the same shared table the model and product screens
  // use: one row per dimension, named and banded as the division's ratified policy
  // says, with the rationale beside each.
  _riskTable(d) {
    const rag = (this._risk.heatmap || {}).rag;
    return riskAssessmentTable({
      data: d,
      division: d.division,
      spec: (key) => MLApps.fieldSpec(key),
      editLink: (key) => this._editLink(key),
      ratingBadge: rag ? ragBadge(rag, d.division) : "",
    });
  },

  _renderContent() {
    const d = this._record.data || {};
    const box = document.getElementById("mla-content");
    if (this._tab === "overview") { box.innerHTML = this._overview(); this._bindEdits(); return; }
    if (this._tab === "risk") {
      box.innerHTML =
        '<div class="section-header">Risk assessment</div>' +
        '<p class="muted" style="font-size:12px;margin:0 0 8px">The owner sets these; they ' +
        "place the ML Application on the heatmap below, which becomes its rating once the " +
        "MRC signs it off.</p>" +
        policyNotice(d.division) +
        this._riskTable(d) +
        DetailTabs.risk(this._risk, false, d.division);  // events are product-only
      this._bindEdits();
      return;
    }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "version_history") {
      box.innerHTML = DetailTabs.versions(d, this.collSpec("version_history"),
                                          this._record.retired);
      this._bindCollections(["version_history"]);
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
        '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:10px">' +
        '<span class="muted" style="font-size:12px">The full write-up for this ML ' +
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
    if (this._tab === "danger") {
      box.innerHTML = this._record.retired
        ? '<div class="empty">This ML Application is retired.</div>'
        : '<div class="section-header">Retire</div><p class="muted">Retiring stops all ' +
          'further edits. The record and its history are kept.</p>' +
          '<button class="btn small" id="mla-retire" style="color:#d32f2f">Retire</button>';
      const btn = document.getElementById("mla-retire");
      if (btn) btn.onclick = () => this._retire();
      return;
    }
    // Everything else is an ordinary spec-driven collection.
    const key = this._tab === "review" ? "ml_review_questions" : this._tab;
    box.innerHTML = Collections.render(d, [this.collSpec(key)], this._record.retired,
                                       false, this._tab === "review");
    this._bindCollections([key]);
  },

  _bindCollections(keys) {
    const base = "/api/ml-applications/" + encodeURIComponent(this._record.ml_application_id);
    Collections.bind(base, keys.map((k) => this.collSpec(k)), this._record.retired,
                     () => this.refresh(), this._record.data);
  },

  _retire() {
    App.amend("Retire ML Application " + this._record.ml_application_id + ".", "POST",
      "/api/ml-applications/" + encodeURIComponent(this._record.ml_application_id) + "/retire",
      {}, () => this.refresh());
  },
};
