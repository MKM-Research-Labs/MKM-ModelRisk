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
// ML Application detail: the Training tab -- one fit, in six sections.
//
// The most recent train, in the order a fit is actually performed. The order is
// governance: split (C) comes before the preprocessing it constrains, so a scaler
// fitted on the full dataset is visible above the metric it inflates rather than
// buried below it.
//
// Six sub-tabs rather than one long page: fifty-three fields in a single scroll is a
// page nobody reaches the bottom of. What a single row of that page does -- display,
// explain, file an artefact beside, edit -- is detail_train_row.js.
//
// Loads after detail_core.js, which defines MLAppDetail.

Object.assign(MLAppDetail, {



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
});
