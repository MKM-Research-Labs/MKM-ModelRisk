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

// The Models tab: the register of every model, and the form that adds one to it.
//
// This file is the tab's own business — fetching the field specs, drawing the list,
// and registering a model. The list itself is inventory/list.js and its filters and
// group headings are the files beside that; a single open model is the Detail package
// under inventory/.
//
// Registering is the only write here, and it asks for the least it can: an id, a name,
// a type and an owner. Division and Line of Business are not offered, because they are
// fixed by the region selected in the navigator above — a model registered from a
// screen scoped to a division belongs to that division, and asking again invites the
// two to disagree. Everything else is set on the record afterwards, where the audit
// can see it move.
//
// inputControl used to live here, which made a console-wide helper look like a models
// concern; it is input_control.js now.

const Inventory = {
  _specs: null,
  _ref: {},                       // reference data (mrc / division / line_of_business)
  _committees: [],

  async specs() {
    // Always re-fetch so admin changes to the reference menus show up promptly.
    this._specs = await App.get("/api/models/fields");
    DocLinks.configure(this._specs);
    return this._specs;
  },

  specByKey(key) {
    let found = null;
    this._specs.groups.forEach((g) => g.fields.forEach((f) => { if (f.key === key) found = f; }));
    return found;
  },

  async render() {
    await this.specs();
    const el = document.getElementById("tab-inventory");
    el.innerHTML =
      '<div id="m-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center"><h3 style="margin:0">Models</h3>' +
      '<span style="flex:1"></span>' +
      '<button class="btn small primary" id="m-register">+ Register model</button>' +
      '<a class="btn small" href="/api/models/risk-report.pdf" target="_blank" ' +
      'style="margin-left:var(--space-4)">&darr; Model Risk Report</a>' +
      '</div><div id="m-list" style="margin-top:var(--space-6)"></div></div>' +
      '<div id="m-detail"></div>';
    document.getElementById("m-register").onclick = () => this.openRegister();
    await this.loadList();
  },

  // Register with id + name + the org assignment (Company mandatory). The
  // header org-scope selector pre-fills Company when it is set.
  async openRegister() {
    document.getElementById("reg-model_id").value = "";
    document.getElementById("reg-name").value = "";
    this._populateTypePicker();
    await this._populateOrgScope();
    document.getElementById("register-overlay").classList.remove("hidden");
    document.getElementById("reg-model_id").focus();
  },

  _populateTypePicker() {
    const spec = this.specByKey("type");
    if (!spec) return;
    const options = ["", ...(spec.options || [])]
      .map((o) => "<option>" + esc(o) + "</option>").join("");
    document.getElementById("reg-type").innerHTML = options;
  },

  // Division/Line of Business are fixed by the region selected in the nav — shown
  // read-only. The owner picker lists people eligible for that org scope
  // (people anchored to the same division); if none match we fall back to the
  // whole directory so registration is never blocked.
  async _populateOrgScope() {
    const { committees, ref } = await MrcNav.load();
    const scope = MrcNav.currentScope(committees, ref);
    this._regScope = scope;
    document.getElementById("reg-division-val").textContent = scope.division || "—";
    document.getElementById("reg-line_of_business-val").textContent = scope.line_of_business || "—";
    const people = ref.people || [];
    const eligible = people.filter((p) => !scope.division || p.division === scope.division);
    const list = eligible.length ? eligible : people;
    document.getElementById("reg-owner").innerHTML =
      '<option value=""></option>' +
      list.map((p) => "<option>" + esc(p.name) + "</option>").join("");
  },

  closeRegister() {
    document.getElementById("register-overlay").classList.add("hidden");
  },

  submitRegister() {
    const id = val("reg-model_id"), name = val("reg-name");
    if (!id || !name) { App.toast("Model ID and name are required", "error"); return; }
    const owner = val("reg-owner");
    if (!owner) { App.toast("A model owner is required", "error"); return; }
    const fields = { owner: owner };
    const type = val("reg-type");
    if (type) fields.type = type;
    // Division/Line of Business come from the region selected in the nav, not a form
    // field, so a model always lands in the right place in the org tree.
    const scope = this._regScope || {};
    if (scope.division) fields.division = scope.division;
    if (scope.line_of_business) fields.line_of_business = scope.line_of_business;
    this.closeRegister();
    App.amend('Register model "' + id + '" (' + name + ").", "POST", "/api/models",
      { model_id: id, name: name, fields: fields }, () => this.render());
  },

  async loadList() {
    const nav = await MrcNav.load();
    await Groups.load();
    await Stages.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    // The live estate by default. Hibernated models are fetched only when somebody
    // asks for them (the Hibernated lifecycle filter), so they are absent from the
    // list, the tiles and every figure drawn from them until then.
    const wantsHibernated = InventoryList.wantsHibernated();
    const inScope = (m) => MrcNav.inScope(this._committees, this._ref, m.data);
    const all = await App.get("/api/models" + (wantsHibernated ? "?include_retired=1" : ""));
    const models = all.filter(inScope);
    if (!models.length && !(await this._estateIsEmpty(all, wantsHibernated, inScope))) {
      // Nothing live in scope, but the estate does hold something — so mount the
      // list rather than the bare empty state. The empty state carries no filter
      // bar, and the lifecycle filter is the only route back to a hibernated
      // model: a register whose models had all been hibernated would otherwise
      // strand them behind a screen with no control on it. mount() keeps the
      // filters and the table renders its own "nothing matches" line.
      InventoryList.mount(models, function (id) { Detail.show(id); });
      return;
    }
    if (!models.length) {
      document.getElementById("m-summary").innerHTML = "";
      document.getElementById("m-list").innerHTML = '<div class="empty">' +
        (MrcNav.state.div ? "No models in this scope yet. Register one above." : "No models yet. Register one above.") +
        "</div>";
      return;
    }
    // Delegate tiles, filters and the sortable table to the list view.
    InventoryList.mount(models, function (id) { Detail.show(id); });
  },

  // Is there genuinely nothing registered in scope, or merely nothing *live*?
  // A first run should keep the plain "register one above" state rather than a
  // filter bar over an empty table, so the two are told apart before choosing.
  // Only asked when the live list came back empty, and skipped entirely when the
  // fetch already included hibernated models — it is the same question answered.
  async _estateIsEmpty(all, wantsHibernated, inScope) {
    if (wantsHibernated) return !all.filter(inScope).length;
    const everything = await App.get("/api/models?include_retired=1");
    return !everything.filter(inScope).length;
  },
};
