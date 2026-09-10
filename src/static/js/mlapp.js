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

  // Returning to this tab lands on the list, not on whichever record was
  // last opened. The panel is cached between visits, so without this the
  // detail stays on screen with the list hidden underneath it.
  onShow() { MLAppDetail.resetToList(); },

  async render() {
    await this.specs();
    document.getElementById("tab-mlapps").innerHTML =
      '<div id="mlapp-listview"><div id="mlapp-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">ML Applications</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="mlapp-register">+ Register ML Application</button>' +
      '</div><div id="mlapp-list" style="margin-top:var(--space-6)"></div></div></div>' +
      '<div id="mlapp-detail"></div>';
    document.getElementById("mlapp-register").onclick = () => this.openRegister();
    await this.loadList();
  },

  openRegister() {
    const idField = '<div class="field"><label for="mreg-ml_application_id">' +
      'ML Application ID *</label><input id="mreg-ml_application_id" placeholder="MLA-0001"></div>';
    // Required fields carry the star; the optional ones (Line of Business) do not, so
    // the form never implies an obligation the domain does not enforce.
    const field = (k, required) => {
      const f = this.fieldSpec(k);
      return '<div class="field"><label for="mreg-' + k + '">' + esc(f.label) +
        (required ? " *" : "") + "</label>" + inputControl("mreg-" + k, f) + "</div>";
    };
    const body = this._specs.register.map((k) => field(k, true)).join("") +
      (this._specs.register_optional || []).map((k) => field(k, false)).join("");
    document.getElementById("mlapp-reg-body").innerHTML = idField + body;
    // Naming a line of business is what lets a Line of Business-level committee pick
    // this record up; without one it can only ever route to its division's.
    bindLineOfBusinessPicker("mreg", this._ref);
    document.getElementById("mlapp-register-overlay").classList.remove("hidden");
    document.getElementById("mreg-ml_application_id").focus();
  },

  closeRegister() {
    document.getElementById("mlapp-register-overlay").classList.add("hidden");
  },

  submitRegister() {
    const id = val("mreg-ml_application_id");
    const fields = {};
    // The optional fields are collected the same way and simply not checked below:
    // blank is a real answer for a record governed at division level.
    this._specs.register.concat(this._specs.register_optional || [])
      .forEach((k) => { const v = val("mreg-" + k); if (v !== "") fields[k] = v; });
    const missing = [id ? null : "ML Application ID"]
      .concat(this._specs.register.filter((k) => !fields[k]).map((k) => this.fieldSpec(k).label))
      .filter(Boolean);
    if (missing.length) { App.toast(missing.join(", ") + " required", "error"); return; }
    this.closeRegister();
    App.amend('Register ML Application "' + id + '" (' + fields.estimator + ").",
      "POST", "/api/ml-applications",
      { ml_application_id: id, fields: fields }, () => this.render());
  },

  // The same list the Models register draws -- tiles, filters, sortable table --
  // through createRecordList, so the two look and behave the same. Only the columns
  // and the id key differ, and the Estimator column takes the place of the model's
  // Criticality/Name pairing because it is the first thing asked of an ML estate.
  _list: null,

  list() {
    if (!this._list) {
      const self = this;
      this._list = createRecordList({
        idKey: "ml_application_id", summaryId: "mlapp-summary", listId: "mlapp-list",
        filtersId: "mla-filters", tableId: "mla-table", p: "af-",
        noun: "ML Applications",
        groupBy: "functional_group",
        // What the division's ratified ML review policy asks of the estate. Only
        // meaningful where there IS such a policy, so the tile stays off a register
        // that has never set one rather than reporting a confident "0 short".
        extraTiles: (live, tile) => {
          const scored = live.filter((m) => (m.r.review_status || {}).required > 0);
          if (!scored.length) return [];
          const short = scored.filter((m) => !m.r.review_status.complete).length;
          return [tile("Mandatory complete", (scored.length - short) + " / " +
            scored.length, Theme.value(short ? "red" : "green"), "")];
        },
        spec: (key) => self.fieldSpec(key),
        reload: () => self.loadList(),
      }, [
        { key: "id", label: "ID", sortVal: (m) => m.id.toLowerCase(),
          cell: (m) => '<span class="modelid">' + esc(m.id) + "</span>" },
        { key: "name", label: "Name", sortVal: (m) => (m.d.name || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.name) },
        { key: "estimator", label: "Estimator",
          sortVal: (m) => (m.d.estimator || "").toLowerCase(),
          cell: (m) => '<span class="code">' + fieldDisplay(m.d.estimator) +
            (m.d.estimator_version
              ? ' <span class="muted">' + esc(m.d.estimator_version) + "</span>" : "") +
            "</span>" },
        { key: "tier", label: "Criticality", sortVal: (m) => m.d.tier || 99,
          cell: (m) => tierBadge(m.d.tier, m.d.division) },
        { key: "rag", label: "Risk Rating",
          sortVal: (m) => ragOrder(m.d.rag_rating, m.d.division),
          cell: (m) => ragBadge(m.d.rag_rating, m.d.division) },
        { key: "owner", label: "Owner", sortVal: (m) => (m.d.owner || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.owner) },
        { key: "next", label: "Next Review",
          sortVal: (m) => m.d.next_review_date || "9999",
          cell: (m) => fieldDisplay(m.d.next_review_date) },
        { key: "mrc", label: "MRC Status", sortVal: (m) => mrcState(m.d),
          cell: (m) => mrcStatusBadge(m.d) },
        { key: "lifecycle", label: "Lifecycle",
          sortVal: (m) => m.retired ? "zz" : (m.d.lifecycle_stage || "").toLowerCase(),
          cell: (m) => m.retired ? '<span class="pill">retired</span>'
            : fieldDisplay(Stages.labelFor(m.d.lifecycle_stage, m.d.division)) },
      ]);
    }
    return this._list;
  },

  async loadList() {
    const nav = await MrcNav.load();
    await Groups.load();
    await Stages.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    // Retired records are out of the estate and out of every figure, exactly as a
    // hibernated model is: they appear only when the Lifecycle filter asks for them,
    // and they are not even fetched until it does. Asking is the only route back to a
    // hibernated record, which is where its reactivation is raised with the MRC.
    const wantsHibernated = this.list().wantsHibernated();
    const all = await App.get(
      "/api/ml-applications" + (wantsHibernated ? "?include_retired=1" : ""));
    const wanted = wantsHibernated ? all : all.filter((r) => !r.retired);
    const records = wanted.filter((r) => MrcNav.inScope(this._committees, this._ref, r.data));
    this.list().mount(records, (id) => MLAppDetail.show(id));
  },
};
