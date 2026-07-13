// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial
// research and educational use only. Any commercial use, including
// but not limited to use in or for products or services offered for sale,
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// Build the input control for one field spec (used by the register form).
function inputControl(id, spec) {
  if (spec.type === "choice") {
    const opts = ["", ...spec.options].map((o) => "<option>" + esc(o) + "</option>").join("");
    return '<select id="' + id + '">' + opts + "</select>";
  }
  if (spec.type === "tier") {
    // Tiers 1-3 (mission critical / important / not important); mirrors TIER_MAX.
    const opts = ["", 1, 2, 3].map((o) => "<option>" + esc(o) + "</option>").join("");
    return '<select id="' + id + '">' + opts + "</select>";
  }
  if (spec.type === "date") return '<input id="' + id + '" type="date">';
  if (spec.type === "textarea") return '<textarea id="' + id + '" rows="4"></textarea>';
  return '<input id="' + id + '">';
}

const Inventory = {
  _specs: null,
  _ref: {},                       // reference data (mrc / division / department)
  _committees: [],

  async specs() {
    // Always re-fetch so admin changes to the reference menus show up promptly.
    this._specs = await App.get("/api/models/fields");
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
      'style="margin-left:8px">&darr; Model Risk Report</a>' +
      '</div><div id="m-list" style="margin-top:12px"></div></div>' +
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

  // Division/Department are fixed by the region selected in the nav — shown
  // read-only. The owner picker lists people eligible for that org scope
  // (people anchored to the same division); if none match we fall back to the
  // whole directory so registration is never blocked.
  async _populateOrgScope() {
    const { committees, ref } = await MrcNav.load();
    const scope = MrcNav.currentScope(committees, ref);
    this._regScope = scope;
    document.getElementById("reg-division-val").textContent = scope.division || "—";
    document.getElementById("reg-department-val").textContent = scope.department || "—";
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
    // Division/Department come from the region selected in the nav, not a form
    // field, so a model always lands in the right place in the org tree.
    const scope = this._regScope || {};
    if (scope.division) fields.division = scope.division;
    if (scope.department) fields.department = scope.department;
    this.closeRegister();
    App.amend('Register model "' + id + '" (' + name + ").", "POST", "/api/models",
      { model_id: id, name: name, fields: fields }, () => this.render());
  },

  _summary(models) {
    const ragCount = (k) => models.filter((m) => (m.data || {}).rag_rating === k).length;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    return '<div class="summary">' +
      card("Total", models.length, "#1976d2") +
      card("Green", ragCount("Green"), "#388e3c") +
      card("Amber", ragCount("Amber"), "#f57c00") +
      card("Red", ragCount("Red"), "#d32f2f") +
      card("Retired", models.filter((m) => m.retired).length, "#9e9e9e") +
      "</div>";
  },

  async loadList() {
    const nav = await MrcNav.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    const all = await App.get("/api/models");
    const models = all.filter((m) => MrcNav.inScope(this._committees, this._ref, m.data));
    document.getElementById("m-summary").innerHTML = this._summary(models);
    const box = document.getElementById("m-list");
    if (!models.length) {
      box.innerHTML = '<div class="empty">' +
        (MrcNav.state.div ? "No models in this scope yet. Register one above." : "No models yet. Register one above.") +
        "</div>";
      return;
    }
    let rows = "";
    models.forEach(function (m) {
      const d = m.data || {};
      const lifecycle = m.retired
        ? '<span class="pill">retired</span>'
        : fieldDisplay(d.lifecycle_stage || d.status);
      rows +=
        '<tr class="clickable" data-id="' + esc(m.model_id) + '">' +
        '<td class="modelid">' + esc(m.model_id) + "</td>" +
        "<td>" + fieldDisplay(d.name) + "</td>" +
        "<td>" + tierBadge(d.tier) + "</td>" +
        "<td>" + ragBadge(d.rag_rating) + "</td>" +
        "<td>" + fieldDisplay(d.owner) + "</td>" +
        "<td>" + mrcStatusBadge(d) + "</td>" +
        "<td>" + lifecycle + "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Name</th><th>Tier</th><th>RAG</th>" +
      "<th>Owner</th><th>MRC Status</th><th>Lifecycle</th></tr></thead><tbody>" + rows + "</tbody></table>";
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.onclick = function () { Detail.show(tr.getAttribute("data-id")); };
    });
  },
};
