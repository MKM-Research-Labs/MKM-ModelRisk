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

// Model detail: a PhysicalRisk-style header card + tabbed detail (Overview,
// Remediation, Versions, Limitations, Assumptions, Changes, Validation, Risk
// Rating, Audit).
const OVERVIEW_LEFT = ["description", "methodology", "tier_rationale", "source_module", "materiality", "complexity"];
const OVERVIEW_RIGHT = ["rag_rating", "owner", "model_owner_role", "lifecycle_stage", "validation_status",
  "last_review_date", "mrc_signoff_date", "next_review_date", "recertification_date", "review_frequency", "peer_reviewer"];
const TESTING_FIELDS = ["unit_tests", "integration_tests", "benchmark_tests"];
const HEADER_DATES = ["last_review_date", "mrc_signoff_date", "next_review_date", "recertification_date"];

const Detail = {
  _id: null, _model: null, _specs: null, _risk: null, _audit: [],
  _decisions: [], _actions: [], _tab: "overview",

  async show(modelId, tab) {
    this._id = modelId;
    this._specs = await Inventory.specs();
    this._model = await App.get("/api/models/" + modelId);
    this._risk = await App.get("/api/models/" + modelId + "/risk-rating");
    this._audit = (await App.get("/api/audit")).filter((e) => e.aggregate_id === modelId);
    this._decisions = await App.get("/api/models/" + modelId + "/decisions");
    this._actions = await App.get("/api/models/" + modelId + "/actions");
    if (tab) this._tab = tab;
    this._render();
    document.getElementById("m-detail").scrollIntoView({ block: "start" });
  },

  specByKey(key) { return Inventory.specByKey(key); },
  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const d = this._model.data || {};
    document.getElementById("m-detail").innerHTML =
      '<div class="card">' + this._header(d) + this._tabbar(d) + '<div id="dt-content"></div></div>' +
      this._dangerZone();
    document.querySelectorAll("[data-dtab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-dtab"); this._render(); };
    });
    this._renderContent();
    this._bindRetire();
  },

  _header(d) {
    const warn = this._risk.rating === "Unacceptable" ? "&#9888; " : "";
    const sub = esc(this._id) + (d.version ? " · v" + esc(d.version) : "") + (d.category ? " · " + esc(d.category) : "");
    const dates = HEADER_DATES.map((k) =>
      '<span class="datechip"><span class="muted">' + esc(this.specByKey(k).label) + ":</span> <b>" +
      fieldDisplay(d[k]) + "</b></span>").join("");
    return '<div class="detail-header"><div>' +
      '<div class="name">' + warn + esc(d.name || this._id) + "</div>" +
      '<div class="sub">' + sub + "</div>" +
      '<div style="margin-top:8px">' + tierBadge(d.tier) + ' <span class="muted">' +
      esc(tierFullLabel(d.tier)) + "</span> &nbsp; " + riskBadge(this._risk.rating) + "</div>" +
      '<div class="dh-dates">' + dates + "</div></div>" +
      '<div class="right"><div class="olabel">OWNER</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div>" +
      '<div class="pill">' + fieldDisplay(d.model_owner_role) + "</div>" +
      '<div style="margin-top:6px">' + ragBadge(d.rag_rating) + "</div></div></div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const vq = d.validation_questions || [];
    const cov = vq.filter((q) => q.status === "Addressed").length + "/" + vq.length;
    const tabs = [
      ["overview", "Overview", null], ["remediation_steps", "Remediation", n("remediation_steps")],
      ["version_history", "Versions", n("version_history")], ["limitations", "Limitations", n("limitations")],
      ["assumptions", "Assumptions", n("assumptions")], ["change_history", "Changes", null],
      ["validation_questions", "Validation", cov], ["risk", "Risk Rating", null],
      ["decisions", "Decisions", this._decisions.length],
      ["actions", "Actions", this._actions.length],
      ["docs", "Docs", n("documents")], ["audit", "Audit", this._audit.length],
    ];
    return '<div class="dtabs">' + tabs.map((t) =>
      '<button class="dtab' + (t[0] === this._tab ? " active" : "") + '" data-dtab="' + t[0] + '">' +
      esc(t[1]) + (t[2] !== null ? " (" + t[2] + ")" : "") + "</button>").join("") + "</div>";
  },

  _renderContent() {
    const d = this._model.data || {};
    const box = document.getElementById("dt-content");
    if (this._tab === "overview") { box.innerHTML = this._overview(d); this._bindEdits(); return; }
    if (this._tab === "risk") { box.innerHTML = DetailTabs.risk(this._risk); return; }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "decisions") { box.innerHTML = DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]); return; }
    if (this._tab === "actions") { box.innerHTML = DetailTabs.linkedItems("Actions", this._actions, ["description", "owner", "target_date", "status"]); return; }
    if (this._tab === "docs") {
      ModelDocs.render(this._id, d.documents || [], this._specs.doc_categories || [], this._model.retired);
      return;
    }
    if (this._tab === "validation_questions") {
      box.innerHTML = DetailTabs.validation(d, this._model.retired);
      this._bindCollection("validation_questions"); return;
    }
    if (this._tab === "version_history") {
      box.innerHTML = DetailTabs.versions(d, this.collSpec("version_history"), this._model.retired);
      this._bindCollection("version_history"); return;
    }
    const spec = this.collSpec(this._tab);
    box.innerHTML = Collections.render(d, { collections: [spec] }, this._model.retired);
    this._bindCollection(this._tab);
  },

  _bindCollection(key) {
    Collections.bind("/api/models/" + this._id + "/collections/", { collections: [this.collSpec(key)] },
      this._model.retired, () => this.show(this._id, this._tab), this._model.data);
  },

  _overview(d) {
    const left = OVERVIEW_LEFT.map((k) => this._row(k, d)).join("");
    const right = OVERVIEW_RIGHT.map((k) => this._row(k, d)).join("");
    const testing = TESTING_FIELDS.map((k) =>
      '<div class="inforow" id="row-' + k + '"><div class="k">' + esc(this.specByKey(k).label) +
      '</div><div class="v">' + yesNo(d[k]) + "</div>" + this._editLink(k) + "</div>").join("");
    const status = this._model.retired
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
    return '<div class="grid2"><div><div class="section-header">Model Details</div>' + left + "</div>" +
      '<div><div class="section-header">Governance Status</div>' + right +
      '<div class="section-header">Testing</div>' + testing + "</div></div>" + status;
  },

  _dangerZone() {
    if (this._model.retired) return "";
    return '<div class="card danger-zone">' +
      '<div class="dz-header">Danger Zone</div>' +
      '<div class="dz-row">' +
      '<div class="dz-text"><b>Retire this model</b>' +
      '<p class="muted">Retired models become read-only — no further amendments are accepted. ' +
      "Existing data and audit trail are preserved.</p></div>" +
      '<div class="dz-action"><button class="btn danger small" id="d-retire">Retire model&hellip;</button></div>' +
      "</div></div>";
  },

  _editLink(key) {
    return this._model.retired ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
  },

  _row(key, d) {
    const f = this.specByKey(key);
    if (!f) return "";
    let value = fieldDisplay(d[key]);
    if (key === "rag_rating") value = ragBadge(d[key]);
    else if (key === "source_module" && d[key]) value = '<span class="code">' + esc(d[key]) + "</span>";
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + value + "</div>" + this._editLink(key) + "</div>";
  },

  _bindEdits() {
    const self = this;
    if (!this._model.retired) {
      document.querySelectorAll("[data-edit]").forEach(function (btn) {
        const key = btn.getAttribute("data-edit");
        btn.onclick = function () { self._edit(self.specByKey(key), self._model.data[key]); };
      });
    }
  },

  _bindRetire() {
    if (this._model.retired) return;
    const self = this;
    const retire = document.getElementById("d-retire");
    if (retire) retire.onclick = function () {
      App.amend("Retire model " + self._id + " (it can no longer be edited).", "POST",
        "/api/models/" + self._id + "/retire", {}, function () { Inventory.render(); });
    };
  },

  _edit(f, current) {
    const row = document.getElementById("row-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      inputControl("ed-input", f) + '<button class="btn small primary" id="ed-save">Save…</button>' +
      '<button class="btn small" id="ed-cancel">Cancel</button></div>';
    const input = document.getElementById("ed-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("ed-cancel").onclick = () => this.show(this._id, "overview");
    document.getElementById("ed-save").onclick = () => {
      let value = input.value.trim();
      if (f.type === "tier") value = parseInt(value, 10);
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/models/" + this._id + "/field", { field: f.key, value: value },
        () => { this.show(this._id, "overview"); Inventory.loadList(); });
    };
  },
};
