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
// Migrated onto RecordDetail when the AI System screen arrived: the fetch/render/
// close sequence below was the third copy of it, and the copies had drifted -- this
// one hid the list view by adding a `hidden` class that no stylesheet rule matches,
// so the register stayed on screen underneath every open ML Application. That is
// fixed by using the shared sequence rather than by patching this file.
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
  _LEFT: ["use_case", "division", "line_of_business", "repo_location", "codebase",
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
  _RIGHT: ["rag_rating", "owner", "model_owner_role", "lifecycle_stage", "review_status"],



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

  // The policy the division's MRC ratified: which items it asks for, and which a
  // review cannot be completed without. Resolved server-side and sent with the
  // record, so the screen never has to know that half the catalogue is code and half
  // is a reference list.
  _scope() { return (this._record || {}).review_scope || {}; },

  _inUse(key) {
    const list = this._scope().training_in_use;
    return !list || list.indexOf(key) >= 0;
  },

  _mandatory(key) {
    return (this._scope().training_mandatory || []).indexOf(key) >= 0;
  },

  // Questions join to the policy on their TOPIC, not on an id: a record's copy is
  // seeded with an id of its own, and a record migrated from a model carries that
  // model's questions. Anything the policy does not mention stays asked, so a
  // migration never drops questions off its own review.
  _questionKey(q) { return (q || {}).short_label || ""; },

  _questionInUse(q) {
    const list = this._scope().question_in_use;
    return !list || list.indexOf(this._questionKey(q)) >= 0;
  },

  _questionMandatory(q) {
    return (this._scope().question_mandatory || []).indexOf(this._questionKey(q)) >= 0;
  },

  // Outstanding mandatory questions, named above the table for the same reason the
  // Training tab names its own: "3 outstanding" sends somebody hunting.
  _questionGap() {
    const q = (this._scope().questions) || {};
    const missing = q.missing_mandatory || [];
    if (!missing.length) return "";
    return '<p style="margin:0 0 var(--space-3)"><span class="badge" ' +
      'style="background:var(--red)">' + missing.length + " mandatory outstanding" +
      '</span> <span class="muted">' + missing.map(esc).join(", ") + "</span></p>";
  },

  _applies(key, train) {
    // Switched off by the institution: not asked, so not shown and not counted. The
    // record keeps whatever it already recorded -- this hides a field, it never
    // erases one.
    if (!this._inUse(key)) return false;
    const meta = this._conditional(key);
    if (!meta.when) return true;
    const task = (train || {}).learning_task || "";
    if (meta.when === "classification") return /classification/i.test(task);
    if (meta.when === "neural task") return task === "Sequence" || task === "Image";
    return true;  // the rest depend on the data, not the task: always offered
  },

  // Which section is open. Held on the detail object so leaving the tab and coming
  // back puts the owner where they were, exactly as the model's review rail does.
  _trainSection: null,

  // Six sub-tabs rather than one long page: fifty-three fields in a single scroll is
  // a page nobody reaches the bottom of, and the sections are a sequence anyway.
  // Numbered 1-6 and not lettered — the letters were the spec's internal references,
  // and a reader meeting "C." on screen has nothing to match it against.
  _trainingSections(d) {
    const train = this._latestTrain(d);
    if (!train) {
      // Start here, not somewhere else. Sending an owner to another tab to find a
      // button before the fields will even appear is a tab nobody gets past — the
      // evidence is entered here, so the first train is started here too.
      if (this._record.retired) {
        return '<div class="empty">No train recorded. This ML Application is ' +
          "retired.</div>";
      }
      return '<div class="empty" style="text-align:left">' +
        "<p style=\"margin:0 0 8px\"><b>No train recorded yet.</b> A train is one fit " +
        "— what it was fitted on, how it was split, its hyperparameters, seed and " +
        "metrics. Name this fit and the six sections open for you to fill in.</p>" +
        '<div class="row" style="align-items:center;gap:6px">' +
        '<input id="mla-first-fit" placeholder="Identifier for this fit — a run name, ' +
        'a version or a commit" style="flex:1;min-width:320px">' +
        '<button class="btn small primary" id="mla-start-train">Start a train</button>' +
        "</div>" +
        '<p class="muted" style="font-size:12px;margin:8px 0 0">Most of it can report ' +
        "itself: a fit that calls <span class=\"code\">modelrisk.capture</span> fills " +
        "the snapshot, hyperparameters, seed, environment, commit and metrics without " +
        "anyone typing them.</p></div>";
    }
    const self = this;
    const sections = this._specs.training.sections;
    if (!this._trainSection) this._trainSection = sections[0].key;
    const open = sections.find((x) => x.key === self._trainSection) || sections[0];
    const rail = sections.map((section, i) =>
      '<button class="dtab' + (section.key === open.key ? " active" : "") +
      '" data-tsec="' + section.key + '">' + (i + 1) + ". " + esc(section.title) +
      self._sectionBadge(section, train) + "</button>").join("");
    const keys = (open.fields || []).filter((k) => self._applies(k, train));
    return '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-5)">Train ' +
      '<span class="code">' + esc(train.fit_id || train.item_id) + "</span>" +
      " — the most recent fit. Earlier trains are on the Trains tab.</p>" +
      this._completenessPanel(d) +
      '<div class="dtabs" style="margin-top:12px">' + rail + "</div>" +
      '<div style="margin-top:12px">' +
      keys.map((k) => self._trainRow(k, train) + self._artefact(k)).join("") +
      "</div>";
  },

  // How much of the section is recorded, and whether anything the division REQUIRES
  // is still blank. Still a count and not a mark -- but a rail that does not say
  // which of six sub-tabs is holding up the review makes somebody open all six.
  _sectionBadge(section, train) {
    const self = this;
    const keys = (section.fields || []).filter((k) => self._applies(k, train));
    const recorded = (k) => {
      const v = train[k];
      return v !== null && v !== undefined && v !== "" &&
        !(Array.isArray(v) && !v.length);
    };
    const filled = keys.filter(recorded).length;
    const short = keys.filter((k) => self._mandatory(k) && !recorded(k)).length;
    return " (" + filled + "/" + keys.length + ")" +
      (short ? ' <span class="badge" style="background:var(--red)">' + short + "</span>" : "");
  },

  // Start the first train from the Training tab itself.
  _bindFirstTrain() {
    const input = document.getElementById("mla-first-fit");
    const btn = document.getElementById("mla-start-train");
    if (!btn || !input) return;
    const self = this;
    const start = function () {
      const id = input.value.trim();
      if (!id) { App.toast("Give this fit an identifier.", "error"); input.focus(); return; }
      App.amend("Record train " + id + " on " + self._record.ml_application_id + ".",
        "POST", "/api/ml-applications/" +
        encodeURIComponent(self._record.ml_application_id) + "/collections/" +
        self._specs.training.collection, { fields: { fit_id: id } },
        () => self.refresh());
    };
    btn.onclick = start;
    input.onkeydown = function (e) { if (e.key === "Enter") start(); };
  },

  _bindSectionRail() {
    const self = this;
    document.querySelectorAll("#mla-content [data-tsec]").forEach(function (btn) {
      btn.onclick = function () {
        self._trainSection = btn.getAttribute("data-tsec");
        self._renderContent();
      };
    });
  },

  // What the evidence adds up to. Deliberately NOT the RAG rating: that is the risk
  // the committee signed off, and a thin Training tab is a different fact from a
  // risky model. Both appear on the record and a reader must be able to tell them
  // apart, so this one is named for what it is.
  _completenessPanel(d) {
    const c = (this._scope().training) || d.training_completeness || {};
    const findings = c.qualifications || [];
    const detail = findings.length
      ? '<span class="badge" style="background:var(--amber)">' + findings.length +
        " to tell a reviewer</span>" +
        '<ul style="margin:var(--space-3) 0 0 var(--space-9);padding:0;font-size:var(--size-sm)">' +
        findings.map((q) => "<li>" + esc(q) + "</li>").join("") + "</ul>"
      : '<span class="muted">Nothing recorded here that a reviewer must be told about.</span>';
    // Progress and permission are different questions, so the outstanding mandatory
    // items are named beside the count rather than folded into it. A bar at 40% that
    // is nonetheless completable is not a contradiction.
    const missing = (c.missing_mandatory || []);
    const required = missing.length
      ? '<div style="margin-top:var(--space-2)"><span class="badge" ' +
        'style="background:var(--red)">' + missing.length + " mandatory outstanding" +
        "</span> <span class=\"muted\">" + missing.map(esc).join(", ") + "</span></div>"
      : ((c.mandatory_total || 0)
        ? '<div style="margin-top:var(--space-2)"><span class="badge" ' +
          'style="background:var(--green)">every mandatory field recorded</span></div>'
        : "");
    return '<div class="inforow" style="align-items:flex-start"><div class="k">Evidence' +
      '</div><div class="v"><span class="muted">' + (c.filled || 0) + " of " +
      (c.total || 0) + ' fields recorded</span><div style="margin-top:var(--space-2)">' +
      detail + "</div>" + required + "</div></div>";
  },

  // A field of the train. An empty one is an ordinary dash UNLESS the division has
  // made it mandatory: what a review cannot be completed without carries the red
  // rule, and everything else is work not yet done rather than a failure. A tab that
  // scolds on every row is one people stop reading, which is the whole reason the
  // institution gets to choose which rows these are.
  _trainRow(key, train) {
    const spec = this._trainSpec(key);
    if (!spec) return "";
    const value = train[key];
    let shown = (value === null || value === undefined || value === "")
      ? '<span class="muted">—</span>' : optionLabel(spec, value);
    // Linked features carry their count inline, and the count the run reported is
    // checked against them: more features fitted than linked means the register is
    // behind what actually went into the model, which is worth seeing on the page.
    if (key === "features" && Array.isArray(value) && value.length) {
      shown += ' <span class="muted">(' + value.length + " linked)</span>";
      const counted = parseInt(train.feature_count, 10);
      if (!isNaN(counted) && counted > value.length) {
        shown += ' <span class="badge" style="background:var(--amber)">' +
          (counted - value.length) + " not in the register</span>";
      }
    }
    // A field the run reported for itself is READ-ONLY. A value somebody can hand-edit
    // is a value a validator has to verify separately, and the point of capturing it
    // was that nobody had to be trusted to retype it.
    const captured = (train.captured_fields || "").split(",").indexOf(key) >= 0;
    const edit = (this._record.retired || captured)
      ? "" : ' <span class="edit-btn" data-edit="tr-' + key + '">edit</span>';
    const mark = captured
      ? ' <span class="pill" title="Reported by the run that produced it">captured</span>'
      : "";
    const required = this._mandatory(key);
    return '<div class="inforow' + (required ? " mandatory-item" : "") +
      '" id="row-tr-' + key + '"><div class="k">' + esc(spec.label) +
      (required ? ' <span class="muted" style="font-size:var(--size-xs)">required</span>'
                : "") +
      '</div><div class="v">' + shown + mark + edit +
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
    return '<span class="muted" style="margin-left:var(--space-7);font-size:var(--size-xs)">' +
      esc(short) + more + "</span>" +
      '<div class="muted" id="why-' + key + '" style="display:none;font-size:var(--size-xs);' +
      'margin-top:var(--space-2);max-width:52em">' + esc(note) + "</div>";
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
    if (this._tab === "danger") {
      box.innerHTML = this._record.retired
        ? '<div class="empty">This ML Application is retired.</div>'
        : '<div class="section-header">Retire</div><p class="muted">Retiring stops all ' +
          'further edits. The record and its history are kept.</p>' +
          '<button class="btn small" id="mla-retire" style="color:var(--red)">Retire</button>';
      const btn = document.getElementById("mla-retire");
      if (btn) btn.onclick = () => this._retire();
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

  _bindCollections(keys) { this.bindCollections(keys); },

  _retire() {
    App.amend("Retire ML Application " + this._record.ml_application_id + ".", "POST",
      "/api/ml-applications/" + encodeURIComponent(this._record.ml_application_id) + "/retire",
      {}, () => this.refresh());
  },
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
