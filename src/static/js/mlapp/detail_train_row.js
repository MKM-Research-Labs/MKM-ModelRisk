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
// ML Application detail: one field of a train.
//
// Display it, say why it is asked, file the plot or table that evidences it beside it,
// and edit it. Four things about a single row, kept together because they are read and
// changed together -- an artefact that drifts away from the field it evidences is the
// failure this grouping exists to prevent.
//
// A reliability curve IS the calibration evidence: a sentence saying the fit is well
// calibrated is an assertion, and the curve is the thing a reviewer can disagree with.
// So the artefact sits under the reading of it, never on a documents tab away from it.
//
// Loads after detail_core.js, which defines MLAppDetail.

Object.assign(MLAppDetail, {

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
});
