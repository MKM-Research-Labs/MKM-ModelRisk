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
// dependency chain, so there is no graph to draw.
// Migrated onto RecordDetail when the AI System screen arrived: the fetch/render/
// close sequence was the third copy of it, and the copies had drifted -- this one hid
// the list view by adding a `hidden` class that no stylesheet rule matches, so the
// register stayed on screen underneath every open ML Application. That is fixed by
// using the shared sequence rather than by patching this file.
//
// This file is what the record IS: its heading, its tab bar, the Overview, and editing
// a field in place. Four companions assign onto MLAppDetail and must load after it --
// detail_tabs (what each tab draws), detail_training (the Training tab), detail_train_row
// (one field of a train) and detail_policy (what the division's MRC asks for).
const MLAppDetail = RecordDetail.attach({
  _reqIndex: null,

  _header(d) {
    return '<div class="row" style="align-items:center">' +
      "<h3 style=\"margin:0\">" + esc(this._record.ml_application_id) + " — " +
      fieldDisplay(d.name) + "</h3>" +
      '<span style="margin-left:var(--space-5)">' + tierBadge(d.tier, d.division) + " " +
      ragBadge(d.rag_rating, d.division) + " " +
      (this._record.retired ? '<span class="pill">retired</span>'
        : optionLabel(MLApps.fieldSpec("lifecycle_stage"), d.lifecycle_stage)) + "</span>" +
      '<span style="flex:1"></span><button class="btn small ghost" id="mla-content-close">Close</button>' +
      "</div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const qs = (this._scope().questions) || {};
    const asked = d.ml_review_questions || [];
    const cov = (qs.total !== undefined)
      ? qs.answered + "/" + qs.total
      : asked.filter((q) => q.status === "Addressed").length + "/" + asked.length;
    return DetailShell.tabBar([
      ["overview", "Overview", null],
      // A retrain is this record's substantial change -- the same collection a model
      // versions through, under the word that actually describes what happened.
      ["training", "Training", ((this._scope().training || d.training_completeness || {}).total)
        ? ((this._scope().training || d.training_completeness).filled + "/" +
           (this._scope().training || d.training_completeness).total) : null],
      ["training_runs", "Trains", n("training_runs")],
      ["review", "Review", cov],
      ["risk", "Risk Rating", null],
      ["fairness_assessments", "Fairness", n("fairness_assessments")],
      ["evaluations", "Evaluations", n("evaluations")],
      ["linkage", "MRC linkage", n("signoff_history")],
      ["docs", "Docs", DocLinks.countIn(d.documents, this._specs.doc_tab_categories)],
      ["changes", "Changes", null],
      ["danger", "Danger", null],
      ["audit", "Audit", this._audit.length],
    ], this._tab, "data-mlatab");
  },

  // The Overview mirrors the model's, field for field and column for column, because
  // the two records are read side by side and a reader should not have to relearn the
  // page. Compare OVERVIEW_LEFT / OVERVIEW_RIGHT_TOP in inventory/detail_core.js.
  //
  // Left is what the thing IS: where it lives, what it is built on, how. ``estimator``
  // sits where a model's ``type`` does, and ``estimator_rationale`` where its
  // ``methodology_rationale`` does -- the same question, asked of an estimator.
  // ``use_case`` leads: what the thing is FOR is the question every other answer on
  // the record is judged against, and it has no equivalent on a model — so it goes
  // above the fields borrowed from the inventory rather than being left off the page
  // because the model has nothing to put there.
  _LEFT: ["use_case", "division", "line_of_business", "functional_group",
          "repo_location", "codebase",
          "estimator", "estimator_version", "vendor", "short_name", "category",
          "methodology", "estimator_rationale", "source_module"],

  // Testing evidence is asked of the review, not of the fit: whether the code is
  // tested is a different question from how the model was trained, and mixing them
  // dilutes both. Monitoring is how the fit is watched afterwards, so it sits with
  // the trains.
  // The reviewer belongs on the tab where the review is run, as on a model — and
  // this one is not optional furniture: the completeness audit scores INDEPENDENCE by
  // comparing it against the owner, so a record with nowhere to set it is a record
  // marked down for a field nobody can reach.
  // ``peer_reviewer`` is not here: it is part of the review's brief
  // (REVIEW_BRIEF_FIELDS in config), and the review stage renders it.
  _TESTING_FIELDS: ["validation_status", "unit_tests", "integration_tests",
                    "benchmark_tests"],
  _TRAINS_FIELDS: ["monitoring_approach"],

  // Governance, in the model's order. Deliberately NOT here, exactly as on a model:
  // validation status, version, review frequency, last review, recertification and the
  // peer reviewer. The MRC sets sign-off and next review at sign-off, and the reviewer
  // belongs on the tab where the review is actually run.
  _RIGHT: ["rag_rating", "owner", "lifecycle_stage", "review_status"],



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
            // The rating is not set, it is PROPOSED. It moves when the committee
            // approves it, exactly as a model's does — an ML rating that applied
            // directly was the one class of record exempt from the committee that
            // signs off everything else.
            if (key === "rag_rating") { self._proposeRag(value, d[key]); return; }
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
    const rows = (keys) => keys.map((k) => self._row(k)).join("");
    const summary = '<div style="margin-bottom:var(--space-7)">' +
      DetailShell.row("description", "Summary", fieldDisplay(d.description),
                      !this._record.retired) + "</div>";
    return summary +
      '<div class="grid2"><div><div class="section-header">ML Application Details</div>' +
      rows(this._LEFT) + "</div>" +
      '<div><div class="section-header">Governance</div>' +
      this.mrcRow("ML Application") + rows(this._RIGHT) + this.mrcStatusRow() +
      this._row("next_review_date") + "</div></div>" +
      DetailShell.retiredFlag(this._record.retired);
  },

  // A rating change goes to the committee rather than to the record. Nothing is
  // stored until it approves, so the screen says where the proposal went rather than
  // looking unchanged and inviting the owner to try again.
  _proposeRag(value, current) {
    if (!value || value === current) { this._renderContent(); return; }
    const mrc = (this._mrc || {}).mrc;
    if (!mrc) {
      App.toast("No MRC covers this ML Application — set one up under Admin → MRC first.",
                "error");
      return;
    }
    const id = this._record.ml_application_id;
    App.amend("Propose " + value + " for " + id + " — routed to " +
      (mrc.name || mrc.value) + " for MRC sign-off. The rating changes once approved.",
      "POST", "/api/ml-applications/" + encodeURIComponent(id) + "/request-signoff",
      { proposed_rag: value }, () => { this.refresh(); MLApps.loadList(); });
  },

  _bindCollections(keys) { this.bindCollections(keys); },
}, {
  api: "/api/ml-applications",
  idKey: "ml_application_id",
  listEl: "mlapp-listview",
  detailEl: "mlapp-detail",
  contentEl: "mla-content",
  tabAttr: "data-mlatab",
  specs: () => MLApps._specs || MLApps.specs(),
  fieldSpec: (key) => MLApps.fieldSpec(key),
  onClose: () => MLApps.loadList(),
});

// The Review tab: the shared review panel (review_panel.js), the same workflow a model's
// review runs. The defaults in the contract already suit a RecordDetail screen, so the
// only thing supplied here is the list refresh after an interim approval — the list
// column shows review status, and it is stale the moment a stage is agreed.
Object.assign(MLAppDetail, ReviewPanelContract, ReviewPanel, {
  _rvAfterApprove() { if (typeof MLApps !== "undefined") MLApps.loadList(); },
});

// The two places an ML Application's review legitimately differs from a model's, both
// because of its review policy (Admin > ML Review Policy): a question the division
// switched off is hidden, and the gap note says what the policy still expects.
Object.assign(MLAppDetail, {
  _rvQuestions(d) {
    return (d[this._rvQuestionsKey()] || []).filter((q) => this._questionInUse(q));
  },
  _rvQuestionsLead() { return this._questionGap(); },
});
