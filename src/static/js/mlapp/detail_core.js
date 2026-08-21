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
  _mrc: null,
  _reqIndex: null,

  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  async show(id) {
    this._specs = MLApps._specs || await MLApps.specs();
    const [record, audit, risk, mrc] = await Promise.all([
      App.get("/api/ml-applications/" + encodeURIComponent(id)),
      App.get("/api/audit"),
      App.get("/api/ml-applications/" + encodeURIComponent(id) + "/risk-rating"),
      App.get("/api/ml-applications/" + encodeURIComponent(id) + "/mrc"),
    ]);
    this._record = record;
    this._mrc = mrc;
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
    // _render, not _renderContent: the tab bar carries the active marker, so drawing
    // only the body leaves the underline on whichever tab was open before.
    document.querySelectorAll("[data-mlatab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-mlatab"); this._render(); };
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
      ["training", "Training", (d.training_completeness || {}).total
        ? (d.training_completeness.filled + "/" + d.training_completeness.total) : null],
      ["training_runs", "Trains", n("training_runs")],
      ["review", "Review", cov],
      ["risk", "Risk Rating", null],
      ["linkage", "MRC linkage", n("signoff_history")],
      ["docs", "Docs", DocLinks.countIn(d.documents, this._specs.doc_tab_categories)],
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
  _LEFT: ["division", "line_of_business", "repo_location", "codebase", "estimator",
          "estimator_version", "vendor", "short_name", "category", "methodology",
          "estimator_rationale", "source_module"],

  // Testing evidence is asked of the review, not of the fit: whether the code is
  // tested is a different question from how the model was trained, and mixing them
  // dilutes both. Monitoring is how the fit is watched afterwards, so it sits with
  // the trains.
  _REVIEW_FIELDS: ["unit_tests", "integration_tests", "benchmark_tests"],
  _TRAINS_FIELDS: ["monitoring_approach"],

  // Governance, in the model's order. Deliberately NOT here, exactly as on a model:
  // validation status, version, review frequency, last review, recertification and the
  // peer reviewer. The MRC sets sign-off and next review at sign-off, and the reviewer
  // belongs on the tab where the review is actually run.
  _RIGHT: ["rag_rating", "owner", "model_owner_role", "lifecycle_stage", "review_status"],


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
    const summary = '<div style="margin-bottom:14px">' +
      DetailShell.row("description", "Summary", fieldDisplay(d.description),
                      !this._record.retired) + "</div>";
    return summary +
      '<div class="grid2"><div><div class="section-header">ML Application Details</div>' +
      rows(this._LEFT) + "</div>" +
      '<div><div class="section-header">Governance</div>' +
      this._mrcRow() + rows(this._RIGHT) + this._mrcStatusRow(d) +
      this._row("next_review_date") + "</div></div>" +
      DetailShell.retiredFlag(this._record.retired);
  },

  // The committee responsible for this ML Application, derived from its Division and
  // Line of Business exactly as a model's is. Flags red when none covers it: a record
  // no committee sees is invisible to the governance meant to hold it.
  _mrcRow() {
    const m = this._mrc || {};
    if (m.mrc) {
      const c = m.mrc;
      return '<div class="inforow"><div class="k">MRC</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:11px">' + esc(m.level || "") +
        "-level</span></div></div>";
    }
    const d = this._record.data || {};
    const org = [d.division, d.line_of_business].filter(Boolean).join(" / ") ||
      "no division / line of business set";
    return '<div class="inforow"><div class="k">MRC</div>' +
      '<div class="v" style="color:var(--red)">&#9888; No committee covers this ML ' +
      "Application (" + esc(org) + "). Set one up under Admin &rarr; MRC.</div></div>";
  },

  // The committee's latest word on this record. Empty until phase 4 puts an ML
  // Application on the sign-off route; the row exists now so the Overview reads the
  // same as a model's rather than gaining a section later.
  _mrcStatusRow(d) {
    const hist = d.signoff_history || [];
    const latest = hist.length ? hist[hist.length - 1] : null;
    let value = '<span class="muted">Not yet before a committee</span>';
    if (latest) {
      const outcome = latest.outcome || "Approved";
      const colour = outcome === "Rejected" ? "var(--red)" : "#388e3c";
      value = '<span style="color:' + colour + ';font-weight:600">' + esc(outcome) +
        "</span> at " + '<span class="code">' + esc(latest.meeting_id) + "</span>" +
        (latest.date ? " (" + esc(latest.date) + ")" : "");
    }
    return '<div class="inforow"><div class="k">MRC status</div><div class="v">' +
      value + "</div></div>";
  },

  // --- Training -------------------------------------------------------------
  // The most recent train, in the six sections the schema declares, in the order a
  // fit is actually performed. The order is governance: split (C) comes before the
  // preprocessing it constrains, so a scaler fitted on the full dataset is visible
  // above the metric it inflates rather than buried below it.
  _latestTrain(d) {
    const runs = d[this._specs.training.collection] || [];
    return runs.length ? runs[runs.length - 1] : null;
  },

  _trainSpec(key) {
    const coll = this.collSpec(this._specs.training.collection) || { fields: [] };
    return coll.fields.find((f) => f.key === key);
  },

  // Whether a conditional field applies to this train, from the learning task it
  // declares. Matched on the STORED value, so renaming a task in Admin does not
  // change which fields it demands.
  // Which fields carry a conditional rule. Nothing is mandatory, so this is the only
  // thing that decides whether a field is asked for at all.
  _conditional(key) {
    if (!this._reqIndex) {
      this._reqIndex = {};
      (this._specs.training.applies || []).forEach((r) => { this._reqIndex[r.key] = r; });
    }
    return this._reqIndex[key] || {};
  },

  _applies(key, train) {
    const meta = this._conditional(key);
    if (!meta.when) return true;
    const task = (train || {}).learning_task || "";
    if (meta.when === "classification") return /classification/i.test(task);
    if (meta.when === "neural task") return task === "Sequence" || task === "Image";
    return true;  // the rest depend on the data, not the task: always offered
  },

  _trainingSections(d) {
    const train = this._latestTrain(d);
    if (!train) {
      return '<div class="empty">No train recorded yet. A train is one fit — its ' +
        "snapshot, split, hyperparameters, seed and metrics. Record one on the Trains " +
        "tab.</div>";
    }
    const self = this;
    return '<p class="muted" style="font-size:12px;margin:0 0 10px">Train ' +
      '<span class="code">' + esc(train.fit_id || train.item_id) + "</span>" +
      " — the most recent fit. Earlier trains are on the Trains tab.</p>" +
      this._completenessPanel(d) +
      this._specs.training.sections.map((section) => {
        const keys = (section.fields || []).filter((k) => self._applies(k, train));
        if (!keys.length) return "";
        return '<div class="section-header">' + esc(section.key + ". " + section.title) +
          "</div>" + keys.map((k) => self._trainRow(k, train) + self._artefact(k)).join("");
      }).join("");
  },

  // What the evidence adds up to. Deliberately NOT the RAG rating: that is the risk
  // the committee signed off, and a thin Training tab is a different fact from a
  // risky model. Both appear on the record and a reader must be able to tell them
  // apart, so this one is named for what it is.
  _completenessPanel(d) {
    const c = d.training_completeness || {};
    const findings = c.qualifications || [];
    const detail = findings.length
      ? '<span class="badge" style="background:#f57c00">' + findings.length +
        " to tell a reviewer</span>" +
        '<ul style="margin:6px 0 0 18px;padding:0;font-size:12px">' +
        findings.map((q) => "<li>" + esc(q) + "</li>").join("") + "</ul>"
      : '<span class="muted">Nothing recorded here that a reviewer must be told about.</span>';
    return '<div class="inforow" style="align-items:flex-start"><div class="k">Evidence' +
      '</div><div class="v"><span class="muted">' + (c.filled || 0) + " of " +
      (c.total || 0) + ' fields recorded</span><div style="margin-top:4px">' +
      detail + "</div></div></div>";
  },

  // A field of the train. An empty one is an ordinary dash: nothing here is
  // mandatory, so an unfilled field is work not yet done rather than a failure, and
  // a tab that says otherwise on every record is one people stop reading.
  _trainRow(key, train) {
    const spec = this._trainSpec(key);
    if (!spec) return "";
    const value = train[key];
    const shown = (value === null || value === undefined || value === "")
      ? '<span class="muted">—</span>' : optionLabel(spec, value);
    // A field the run reported for itself is READ-ONLY. A value somebody can hand-edit
    // is a value a validator has to verify separately, and the point of capturing it
    // was that nobody had to be trusted to retype it.
    const captured = (train.captured_fields || "").split(",").indexOf(key) >= 0;
    const edit = (this._record.retired || captured)
      ? "" : ' <span class="edit-btn" data-edit="tr-' + key + '">edit</span>';
    const mark = captured
      ? ' <span class="pill" title="Reported by the run that produced it">captured</span>'
      : "";
    return '<div class="inforow" id="row-tr-' + key + '"><div class="k">' +
      esc(spec.label) + '</div><div class="v">' + shown + mark + edit +
      this._why(key) + "</div></div>";
  },

  // The short reason inline, the whole one behind the (i). Space to the right of the
  // value is where a reader's eye already is when they are wondering why they are
  // being asked for something, and a field nobody understands is a field filled in
  // plausibly rather than honestly.
  _why(key) {
    const note = (this._specs.training.notes || {})[key] || "";
    if (!note) return "";
    const cut = note.indexOf(". ");
    const short = cut > 0 ? note.slice(0, cut + 1) : note;
    const more = note.length > short.length
      ? ' <span class="edit-btn" data-why="' + key + '" title="Why this is asked">&#9432;</span>'
      : "";
    return '<span class="muted" style="margin-left:14px;font-size:11px">' +
      esc(short) + more + "</span>" +
      '<div class="muted" id="why-' + key + '" style="display:none;font-size:11px;' +
      'margin-top:4px;max-width:52em">' + esc(note) + "</div>";
  },

  _bindWhy() {
    document.querySelectorAll("#mla-content [data-why]").forEach(function (el) {
      el.onclick = function () {
        const box = document.getElementById("why-" + el.getAttribute("data-why"));
        if (box) box.style.display = box.style.display === "none" ? "block" : "none";
      };
    });
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

  // The plot or table behind a field  // The plot or table behind a field, filed beside it. A reliability curve IS the
  // calibration evidence: a sentence saying the model is well calibrated is an
  // assertion, and the curve is the thing a reviewer can disagree with. So the panel
  // sits under the reading of it, never on a documents tab away from it.
  _artefactOpts(key) {
    const category = (this._specs.training.artefacts || {})[key];
    if (!category) return null;
    return { category: category, docs: (this._record.data || {}).documents || [],
             base: "/api/ml-applications/", id: this._record.ml_application_id,
             retired: this._record.retired, refresh: () => this.refresh() };
  },

  _artefact(key) {
    const opts = this._artefactOpts(key);
    return opts ? DocPanel.html(opts) : "";
  },

  _bindArtefacts() {
    const self = this;
    Object.keys(this._specs.training.artefacts || {}).forEach(function (key) {
      const opts = self._artefactOpts(key);
      if (opts) DocPanel.bind(opts);
    });
  },

  _bindTrainEdits(d) {
    if (this._record.retired) return;
    const train = this._latestTrain(d);
    if (!train) return;
    const self = this;
    const base = "/api/ml-applications/" + encodeURIComponent(this._record.ml_application_id) +
      "/collections/" + this._specs.training.collection + "/" + train.item_id;
    document.querySelectorAll("#mla-content [data-edit]").forEach(function (btn) {
      const key = btn.getAttribute("data-edit").replace(/^tr-/, "");
      const spec = self._trainSpec(key);
      if (!spec) return;
      btn.onclick = function () {
        DetailShell.fieldEditor({
          scope: "#mla-content", prefix: "mltr", spec: spec, current: train[key],
          division: (self._record.data || {}).division, withSave: true,
          onCancel: () => self._renderContent(),
          onSave: (value, shown) => {
            const fields = {}; fields[key] = value;
            App.amend("Set " + spec.label + ' = "' + shown + '" on train ' +
              (train.fit_id || train.item_id) + ".", "POST", base, { fields: fields },
              () => self.refresh());
          },
        });
      };
    });
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
    if (this._tab === "training") {
      box.innerHTML = this._trainingSections(d);
      this._bindTrainEdits(d);
      this._bindArtefacts();
      this._bindWhy();
      return;
    }
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
    if (this._tab === "training_runs") {
      box.innerHTML =
        '<div class="section-header">Monitoring</div>' +
        this._TRAINS_FIELDS.map((k) => this._row(k)).join("") +
        '<div class="section-header" style="margin-top:16px">Trains</div>' +
        '<p class="muted" style="font-size:12px;margin:0 0 8px">Every fit, each with ' +
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
    if (this._tab === "review") {
      box.innerHTML =
        '<div class="section-header">Testing evidence</div>' +
        this._REVIEW_FIELDS.map((k) => this._row(k)).join("") +
        '<div class="section-header" style="margin-top:16px">Review questions</div>' +
        '<div id="mla-questions"></div>';
      this._bindEdits();
      document.getElementById("mla-questions").innerHTML = Collections.render(
        d, [this.collSpec("ml_review_questions")], this._record.retired, false, true);
      this._bindCollections(["ml_review_questions"]);
      return;
    }
    // Everything else is an ordinary spec-driven collection.
    const key = this._tab;
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
