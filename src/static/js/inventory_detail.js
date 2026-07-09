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
// Description is promoted to a full-width summary band above the two columns.
// Tier + its rating rationale sit at the foot of Model Details, below Complexity.
const OVERVIEW_LEFT = ["division", "department", "methodology", "source_module",
  "materiality", "complexity", "tier", "rating_rationale"];
const OVERVIEW_RIGHT = ["rag_rating", "owner", "lifecycle_stage", "validation_status",
  "last_review_date", "mrc_signoff_date", "next_review_date", "recertification_date", "review_frequency", "peer_reviewer"];
const TESTING_FIELDS = ["unit_tests", "integration_tests", "benchmark_tests"];
const HEADER_DATES = ["last_review_date", "mrc_signoff_date", "next_review_date", "recertification_date"];

const Detail = {
  _id: null, _model: null, _specs: null, _risk: null, _audit: [], _mrc: null,
  _decisions: [], _actions: [], _tab: "overview",

  async show(modelId, tab) {
    this._id = modelId;
    this._specs = await Inventory.specs();
    // Fetch the independent reads in parallel so a re-render settles quickly.
    const [model, risk, mrc, audit, decisions, actions] = await Promise.all([
      App.get("/api/models/" + modelId),
      App.get("/api/models/" + modelId + "/risk-rating"),
      App.get("/api/models/" + modelId + "/mrc"),
      App.get("/api/audit"),
      App.get("/api/models/" + modelId + "/decisions"),
      App.get("/api/models/" + modelId + "/actions"),
    ]);
    this._model = model;
    this._risk = risk;
    this._mrc = mrc;
    this._audit = audit.filter((e) => e.aggregate_id === modelId);
    this._decisions = decisions;
    this._actions = actions;
    if (tab) this._tab = tab;
    this._render();
    document.getElementById("m-detail").scrollIntoView({ block: "start" });
  },

  specByKey(key) { return Inventory.specByKey(key); },
  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const d = this._model.data || {};
    document.getElementById("m-detail").innerHTML =
      '<div class="card">' + this._header(d) + this._tabbar(d) + '<div id="dt-content"></div></div>';
    document.querySelectorAll("[data-dtab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-dtab"); this._render(); };
    });
    this._renderContent();
    if (this._tab === "danger") this._bindRetire();
  },

  _header(d) {
    const warn = this._risk.rating === "Unacceptable" ? "&#9888; " : "";
    const sub = esc(this._id) + (d.version ? " · v" + esc(d.version) : "") + (d.category ? " · " + esc(d.category) : "");
    const dates = HEADER_DATES.map((k) => {
      // MRC sign-off shows the granting meeting id (not the date) once approved.
      const value = (k === "mrc_signoff_date" && d.mrc_signoff_meeting)
        ? esc(d.mrc_signoff_meeting) : fieldDisplay(d[k]);
      return '<span class="datechip"><span class="muted">' + esc(this.specByKey(k).label) +
        ":</span> <b>" + value + "</b></span>";
    }).join("");
    return '<div class="detail-header"><div>' +
      '<div class="name">' + warn + esc(d.name || this._id) + "</div>" +
      '<div class="sub">' + sub + "</div>" +
      '<div style="margin-top:8px">' + tierBadge(d.tier) + ' <span class="muted">' +
      esc(tierFullLabel(d.tier)) + "</span> &nbsp; " + riskBadge(this._risk.rating) + "</div>" +
      '<div class="dh-dates">' + dates + "</div></div>" +
      '<div class="right"><div class="olabel">OWNER</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div>" +
      '<div style="margin-top:6px">' + ragBadge(d.rag_rating) + "</div></div></div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const vq = d.validation_questions || [];
    const cov = vq.filter((q) => q.status === "Addressed").length + "/" + vq.length;
    const tabs = [
      ["overview", "Overview", null], ["remediation_steps", "Remediation", n("remediation_steps")],
      ["version_history", "Versions", n("version_history")], ["limitations", "Limitations", n("limitations")],
      ["validation_questions", "Validation & Assumptions", cov],
      ["operational_failure_events", "Events", n("operational_failure_events")],
      ["risk", "Risk Rating", null],
      ["decisions", "Decisions", this._decisions.length],
      ["actions", "Actions", this._actions.length],
      ["docs", "Docs", n("documents")], ["audit", "Audit", this._audit.length],
      ["danger", "Danger", null],
    ];
    return '<div class="dtabs">' + tabs.map((t) => {
      const danger = t[0] === "danger" ? " dtab-danger" : "";
      return '<button class="dtab' + (t[0] === this._tab ? " active" : "") + danger +
        '" data-dtab="' + t[0] + '">' +
        esc(t[1]) + (t[2] !== null ? " (" + t[2] + ")" : "") + "</button>";
    }).join("") + "</div>";
  },

  _renderContent() {
    const d = this._model.data || {};
    const box = document.getElementById("dt-content");
    if (this._tab === "overview") { box.innerHTML = this._overview(d); this._bindEdits(); return; }
    if (this._tab === "risk") {
      box.innerHTML = DetailTabs.risk(this._risk);
      this._bindSignoffRequest(); return;
    }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "danger") { box.innerHTML = this._dangerContent(); return; }
    if (this._tab === "decisions") { box.innerHTML = DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]); return; }
    if (this._tab === "actions") { box.innerHTML = DetailTabs.linkedItems("Actions", this._actions, ["description", "owner", "target_date", "status"]); return; }
    if (this._tab === "docs") {
      ModelDocs.render(this._id, d.documents || [], this._specs.doc_categories || [], this._model.retired);
      return;
    }
    // Validation & Assumptions overlap — one tab: the SR 26-2 questions plus
    // the assumptions register.
    if (this._tab === "validation_questions") {
      box.innerHTML = DetailTabs.validation(d, this._model.retired) +
        this._collSection("assumptions", d);
      this._bindValidationSaves();
      this._bindCollections(["assumptions"]); return;
    }
    // Versions & Changes overlap — one tab: the version timeline plus the
    // change-history register.
    if (this._tab === "version_history") {
      box.innerHTML = DetailTabs.versions(d, this.collSpec("version_history"), this._model.retired) +
        this._collSection("change_history", d);
      this._bindCollections(["version_history", "change_history"]); return;
    }
    // Limitations tab: Testing (scalar fields) + Model weaknesses + Limitations.
    if (this._tab === "limitations") {
      const testing = '<div class="section-header">Testing</div>' +
        TESTING_FIELDS.map((k) =>
          '<div class="inforow" id="row-' + k + '"><div class="k">' + esc(this.specByKey(k).label) +
          '</div><div class="v">' + yesNo(d[k]) + "</div>" + this._editLink(k) + "</div>").join("");
      box.innerHTML = testing + this._collSection("model_weaknesses", d) +
        this._collSection("limitations", d);
      this._bindEdits();
      this._bindCollections(["model_weaknesses", "limitations"]); return;
    }
    const spec = this.collSpec(this._tab);
    box.innerHTML = Collections.render(d, { collections: [spec] }, this._model.retired);
    this._bindCollection(this._tab);
    if (this._tab === "operational_failure_events") this._defaultAccountable(d);
  },

  _collSection(key, d) {
    return Collections.render(d, { collections: [this.collSpec(key)] }, this._model.retired);
  },

  _bindCollections(keys) {
    Collections.bind("/api/models/" + this._id + "/collections/",
      { collections: keys.map((k) => this.collSpec(k)) },
      this._model.retired, () => this.show(this._id, this._tab), this._model.data);
  },

  // Pre-fill an Event's Accountable field with the model's owner so the chair
  // can capture an incident without re-typing who owns the model.
  _defaultAccountable(d) {
    const accountable = document.getElementById("add-operational_failure_events-accountable");
    if (accountable && d.owner && [...accountable.options].some((o) => o.value === d.owner)) {
      accountable.value = d.owner;
    }
  },

  _bindCollection(key) { this._bindCollections([key]); },

  _bindValidationSaves() {
    if (this._model.retired) return;
    const self = this;
    document.querySelectorAll("[data-vq-save]").forEach(function (btn) {
      const itemId = btn.getAttribute("data-vq-save");
      btn.onclick = function () {
        const status = val("vq-" + itemId + "-status");
        const rationale = val("vq-" + itemId + "-rationale");
        App.amend(
          "Update " + itemId + ' — status="' + status + '", rationale.', "POST",
          "/api/models/" + self._id + "/collections/validation_questions/" + itemId,
          { fields: { status: status, rationale: rationale } },
          () => self.show(self._id, "validation_questions"),
        );
      };
    });
  },

  _overview(d) {
    const left = OVERVIEW_LEFT.map((k) => this._row(k, d)).join("");
    const right = OVERVIEW_RIGHT.map((k) => this._row(k, d)).join("");
    const status = this._model.retired
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
    // Full-width summary of what the model does, spanning both columns.
    const summary = '<div class="inforow" id="row-description" style="margin-bottom:14px">' +
      '<div class="k">Summary</div><div class="v">' + fieldDisplay(d.description) + "</div>" +
      this._editLink("description") + "</div>";
    return summary +
      '<div class="grid2"><div><div class="section-header">Model Details</div>' + left + "</div>" +
      '<div><div class="section-header">Governance Status</div>' + right + this._mrcRow() +
      "</div></div>" + status;
  },

  // The MRC responsible for this model, derived from its division/department.
  // A missing committee is flagged in red — sign-off can't be routed without one.
  _mrcRow() {
    const m = this._mrc || {};
    if (m.mrc) {
      const c = m.mrc;
      return '<div class="inforow"><div class="k">MRC</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:11px">' + esc(m.level || "") + "-level</span></div></div>";
    }
    const d = this._model.data || {};
    const org = [d.division, d.department].filter(Boolean).join(" / ") || "no division/department set";
    return '<div class="inforow"><div class="k">MRC</div>' +
      '<div class="v" style="color:var(--red)">&#9888; No committee covers this model (' +
      esc(org) + "). Set one up under Admin &rarr; MRC.</div></div>";
  },

  // Contents of the "Danger" dtab — replaces the earlier below-card danger zone.
  // Sits inside #dt-content so the tab bar handles activation, and reuses the
  // existing .danger-zone card styling for the red border + header.
  _dangerContent() {
    if (this._model.retired) {
      return '<div class="empty">This model is retired and read-only. Nothing further can be changed.</div>';
    }
    return '<div class="danger-zone">' +
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
    if (key === "rag_rating") {
      // Show the owner's RAG alongside what the tier heatmap ("the table") says,
      // so any divergence needing MRC sign-off is visible at a glance.
      const tableRag = (this._risk.heatmap || {}).rag;
      value = '<span class="muted" style="font-size:11px">Owner</span> ' + ragBadge(d[key]) +
        '<span class="muted" style="font-size:11px;margin-left:12px">Table</span> ' +
        (tableRag ? ragBadge(tableRag) : '<span class="muted">&mdash;</span>');
    } else if (key === "tier" && (d[key] || d[key] === 0)) {
      value = tierBadge(d[key]) + ' <span class="muted">' + esc(tierFullLabel(d[key])) + "</span>";
    } else if (key === "source_module" && d[key]) {
      value = '<span class="code">' + esc(d[key]) + "</span>";
    } else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      // MRC sign-off shows the granting meeting (not the raw date) once approved.
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // The sign-off date/meeting are stamped by MRC approval, not edited by hand.
    const editLink = key === "mrc_signoff_date" ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + value + "</div>" + editLink + "</div>";
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

  // W4c — open the sign-off picker, then hand the chosen meeting off to the
  // standard confirm-to-amend flow.
  _bindSignoffRequest() {
    const btn = document.getElementById("req-signoff");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const proposed = btn.getAttribute("data-proposed");
      // Routing is automatic — the request goes to the model's responsible MRC.
      const mrc = (self._mrc || {}).mrc;
      if (!mrc) {
        App.toast("No MRC covers this model — set one up under Admin → MRC first.", "error");
        return;
      }
      App.amend(
        "Request MRC sign-off for " + self._id + " → " + proposed +
          " (routed to " + (mrc.name || mrc.value) + ").",
        "POST", "/api/models/" + self._id + "/request-signoff",
        { proposed_rag: proposed },
        () => self.show(self._id, "risk"));
    };
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
    document.getElementById("ed-cancel").onclick = () => this.show(this._id, this._tab);
    document.getElementById("ed-save").onclick = () => {
      let value = input.value.trim();
      if (f.type === "tier") value = parseInt(value, 10);
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/models/" + this._id + "/field", { field: f.key, value: value },
        () => { this.show(this._id, this._tab); Inventory.loadList(); });
    };
  },
};
