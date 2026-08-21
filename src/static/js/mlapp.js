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
// ML Applications: the list view (master) beside its detail (see mlapp/detail_core.js).
//
// An ML Application is a use case for an off-the-shelf estimator, so the list answers
// the questions you ask across an ML estate rather than the ones you ask of a model:
// what is it built on, is it rated, and is anyone still watching it.
const MLApps = {
  _specs: null,
  _ref: {},
  _committees: [],

  async specs() {
    // Re-fetched so estimators added in Admin appear in the register dropdown.
    this._specs = await App.get("/api/ml-applications/fields");
    DocLinks.configure(this._specs);
    return this._specs;
  },

  fieldSpec(key) {
    let found = null;
    this._specs.groups.forEach((g) => g.fields.forEach((f) => { if (f.key === key) found = f; }));
    return found;
  },

  async render() {
    await this.specs();
    document.getElementById("tab-mlapps").innerHTML =
      '<div id="mlapp-listview"><div id="mlapp-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">ML Applications</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="mlapp-register">+ Register ML Application</button>' +
      '</div><div id="mlapp-list" style="margin-top:12px"></div></div></div>' +
      '<div id="mlapp-detail"></div>';
    document.getElementById("mlapp-register").onclick = () => this.openRegister();
    await this.loadList();
  },

  openRegister() {
    const idField = '<div class="field"><label for="mreg-ml_application_id">' +
      'ML Application ID *</label><input id="mreg-ml_application_id" placeholder="MLA-0001"></div>';
    const body = this._specs.register.map((k) => {
      const f = this.fieldSpec(k);
      return '<div class="field"><label for="mreg-' + k + '">' + esc(f.label) + " *</label>" +
        inputControl("mreg-" + k, f) + "</div>";
    }).join("");
    document.getElementById("mlapp-reg-body").innerHTML = idField + body;
    document.getElementById("mlapp-register-overlay").classList.remove("hidden");
    document.getElementById("mreg-ml_application_id").focus();
  },

  closeRegister() {
    document.getElementById("mlapp-register-overlay").classList.add("hidden");
  },

  submitRegister() {
    const id = val("mreg-ml_application_id");
    const fields = {};
    this._specs.register.forEach((k) => { const v = val("mreg-" + k); if (v !== "") fields[k] = v; });
    const missing = [id ? null : "ML Application ID"]
      .concat(this._specs.register.filter((k) => !fields[k]).map((k) => this.fieldSpec(k).label))
      .filter(Boolean);
    if (missing.length) { App.toast(missing.join(", ") + " required", "error"); return; }
    this.closeRegister();
    App.amend('Register ML Application "' + id + '" (' + fields.estimator + ").",
      "POST", "/api/ml-applications",
      { ml_application_id: id, fields: fields }, () => this.render());
  },

  // Summary tiles, one per lifecycle stage the INSTITUTION has defined (Admin >
  // Vocabulary), not a set of stage names chosen here. An adopter that renames or
  // replaces its stages gets tiles that match, because the options come from the
  // field spec the API publishes. Colour is neutral for the same reason: nothing
  // here knows which of somebody else's stages is the good one.
  _summary(records) {
    const spec = this.fieldSpec("lifecycle_stage") || {};
    const stages = spec.options || [];
    const shown = spec.option_labels || {};
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      esc(lbl) + '</div><div class="val">' + v + "</div></div>";
    const live = records.filter((r) => !r.retired);
    return '<div class="summary">' +
      card("Total", records.length, "#1976d2") +
      stages.map((stage) =>
        card(shown[stage] || stage,
             live.filter((r) => (r.data || {}).lifecycle_stage === stage).length,
             "#607d8b")).join("") +
      // "Hibernated", not "Retired": retirement is a flag on the record, not a stage,
      // and an institution whose vocabulary happens to contain a stage called Retired
      // would otherwise get two tiles with the same word counting different things.
      // The Models list draws the same distinction with the same word.
      card("Hibernated", records.filter((r) => r.retired).length, "#9e9e9e") +
      "</div>";
  },

  async loadList() {
    const nav = await MrcNav.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    const all = await App.get("/api/ml-applications");
    const records = all.filter((r) => MrcNav.inScope(this._committees, this._ref, r.data));
    document.getElementById("mlapp-summary").innerHTML = this._summary(records);
    const box = document.getElementById("mlapp-list");
    if (!records.length) {
      box.innerHTML = '<div class="empty">' +
        (MrcNav.state.div
          ? "No ML Applications in this scope yet. Register one above."
          : "No ML Applications yet. Register one above.") + "</div>";
      return;
    }
    let rows = "";
    records.forEach(function (r) {
      const d = r.data || {};
      // Estimator and version together: "which engine, at which release" is the first
      // question asked of an ML estate, and neither half answers it alone.
      const engine = fieldDisplay(d.estimator) +
        (d.estimator_version ? ' <span class="muted">' + esc(d.estimator_version) + "</span>" : "");
      rows +=
        '<tr class="clickable" data-id="' + esc(r.ml_application_id) + '">' +
        '<td class="modelid">' + esc(r.ml_application_id) + "</td>" +
        "<td>" + fieldDisplay(d.name) + "</td>" +
        '<td><span class="code">' + engine + "</span></td>" +
        "<td>" + fieldDisplay(d.owner) + "</td>" +
        "<td>" + tierBadge(d.tier, d.division) + "</td>" +
        "<td>" + ragBadge(d.rag_rating, d.division) + "</td>" +
        "<td>" + (r.retired ? '<span class="pill">retired</span>'
          : optionLabel(MLApps.fieldSpec("lifecycle_stage"), d.lifecycle_stage)) +
        "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Name</th><th>Estimator</th><th>Owner</th>" +
      "<th>Tier</th><th>RAG</th><th>Lifecycle</th></tr></thead><tbody>" + rows + "</tbody></table>";
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.onclick = function () { MLAppDetail.show(tr.getAttribute("data-id")); };
    });
  },
};
