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

// Product detail: header + tabbed detail (Overview with component bindings/rebind,
// Limitations, Assumptions, Audit). The identifier is derived from the bindings.
const PRODUCT_OVERVIEW_PRODUCT = ["product", "product_id", "description"];
const PRODUCT_OVERVIEW_ORG = ["division", "department"];
const PRODUCT_OVERVIEW_CLASS = ["tier", "materiality", "complexity"];
const PRODUCT_OVERVIEW_MONITORING = ["monitoring_approach", "monitoring_results"];
const PRODUCT_OVERVIEW_GOV = ["status", "owner", "mrc_signoff_date", "next_review_date",
  "last_review_date", "notes"];

const ProductDetail = {
  _id: null, _product: null, _specs: null, _audit: [], _mrc: null, _risk: null,
  _decisions: [], _actions: [], _tab: "overview",

  async show(productId, tab) {
    this._id = productId;
    this._specs = Product._specs || await Product.specs();
    // Fetch the independent reads in parallel so a re-render settles quickly.
    const [product, mrc, risk, audit, decisions, actions] = await Promise.all([
      App.get("/api/products/" + productId),
      App.get("/api/products/" + productId + "/mrc"),
      App.get("/api/products/" + productId + "/risk-rating"),
      App.get("/api/audit"),
      App.get("/api/products/" + productId + "/decisions"),
      App.get("/api/products/" + productId + "/actions"),
    ]);
    this._product = product;
    this._mrc = mrc;
    this._risk = risk;
    this._audit = audit.filter((e) => e.aggregate_id === productId);
    this._decisions = decisions;
    this._actions = actions;
    if (tab) this._tab = tab;
    this._render();
    document.getElementById("product-detail").scrollIntoView({ block: "start" });
  },

  fieldSpec(key) { return Product.fieldSpec(key); },
  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const d = this._product.data || {};
    const listview = document.getElementById("product-listview");
    if (listview) listview.style.display = "none";
    document.getElementById("product-detail").innerHTML =
      '<div style="margin-bottom:12px"><button class="btn small" id="product-back">&lsaquo; All Products</button></div>' +
      '<div class="card">' + this._header(d) + this._tabbar(d) + '<div id="pt-content"></div></div>';
    document.getElementById("product-back").onclick = () => ProductDetail.close();
    document.querySelectorAll("[data-ptab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-ptab"); this._render(); };
    });
    this._renderContent();
  },

  // Return to the list without a full refetch (the list is kept current on edits).
  close() {
    this._tab = "overview";
    document.getElementById("product-detail").innerHTML = "";
    const listview = document.getElementById("product-listview");
    if (listview) listview.style.display = "";
  },

  _header(d) {
    return '<div class="detail-header"><div>' +
      '<div class="name">' + fieldDisplay(d.product) + "</div>" +
      '<div class="sub"><span class="code">' + fieldDisplay(d.identifier) + "</span> · " + esc(this._id) +
      (d.product_id ? " · " + esc(d.product_id) : "") + "</div>" +
      '<div style="margin-top:8px">' + productStatusBadge(d.status, this._product.retired) +
      (this._risk && this._risk.rating ? " &nbsp; " + riskBadge(this._risk.rating) : "") + "</div></div>" +
      '<div class="right"><div class="olabel">OWNER</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div></div></div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const tabs = [
      ["overview", "Overview", null], ["limitations", "Limitations", n("limitations")],
      ["assumptions", "Assumptions", n("assumptions")],
      ["remediation_steps", "Remediation", n("remediation_steps")],
      ["validation_questions", "Validation", n("validation_questions")],
      ["operational_failure_events", "Events", n("operational_failure_events")],
      ["risk", "Risk Rating", null], ["linkage", "MRC", null],
      ["docs", "Docs", n("documents")], ["audit", "Audit", this._audit.length],
      ["danger", "Danger", null],
    ];
    return '<div class="dtabs">' + tabs.map((t) =>
      '<button class="dtab' + (t[0] === this._tab ? " active" : "") + '" data-ptab="' + t[0] + '"' +
      (t[0] === "danger" ? ' style="color:#d32f2f"' : "") + ">" +
      esc(t[1]) + (t[2] !== null ? " (" + t[2] + ")" : "") + "</button>").join("") + "</div>";
  },

  _renderContent() {
    const d = this._product.data || {};
    const box = document.getElementById("pt-content");
    if (this._tab === "overview") {
      box.innerHTML = this._overview(d); this._bindEdits(); this._bindSignoffRequest();
      this._bindLinkageLink(); return;
    }
    if (this._tab === "danger") { box.innerHTML = this._dangerContent(); this._bindDanger(); return; }
    if (this._tab === "risk") { box.innerHTML = DetailTabs.risk(this._risk); return; }
    if (this._tab === "linkage") { box.innerHTML = this._mrcLinkage(d); return; }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "docs") {
      ModelDocs.render(this._id, d.documents || [], this._specs.doc_categories || [],
        this._product.retired, "/api/products/", () => this.show(this._id, "docs"), "pt-content");
      return;
    }
    const spec = this.collSpec(this._tab);
    box.innerHTML = Collections.render(d, { collections: [spec] }, this._product.retired);
    Collections.bind("/api/products/" + this._id + "/collections/", { collections: [spec] },
      this._product.retired, () => this.show(this._id, this._tab), d);
  },

  _section(title, keys, d) {
    return '<div class="section-header">' + title + "</div>" +
      keys.map((k) => this._row(k, d)).join("");
  },

  _overview(d) {
    const bindings = this._specs.bindings.map((k) => this._bindingRow(k, d)).join("");
    const left = '<div class="section-header">Components</div>' + bindings +
      this._section("Product", PRODUCT_OVERVIEW_PRODUCT, d) +
      this._section("Organisation", PRODUCT_OVERVIEW_ORG, d) +
      this._section("Classification", PRODUCT_OVERVIEW_CLASS, d) +
      this._section("Monitoring", PRODUCT_OVERVIEW_MONITORING, d);
    const right = this._section("Risk rating", ["rag_rating"], d) + this._signoffPanel(d) +
      this._section("Governance &amp; review", PRODUCT_OVERVIEW_GOV, d) +
      this._mrcRow(d) + this._mrcStatusRow(d);
    // Retire lives on the Danger tab; the Overview only flags a retired Product.
    const status = this._product.retired
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
    return '<div class="grid2"><div>' + left + "</div><div>" + right + "</div></div>" + status;
  },

  // The MRC responsible for this product, derived from its Division/Department
  // (Department-level → Division-level → Company). Flags red when none covers it.
  _mrcRow(d) {
    const m = this._mrc || {};
    const head = '<div class="section-header">MRC</div>';
    if (m.mrc) {
      const c = m.mrc;
      return head + '<div class="inforow"><div class="k">Committee</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:11px">' + esc(m.level || "") + "-level</div></div>";
    }
    const org = [d.division, d.department].filter(Boolean).join(" / ") || "no division/department set";
    return head + '<div class="inforow"><div class="v" style="color:var(--red)">&#9888; ' +
      "No committee covers this product (" + esc(org) + "). Set its Division/Department, " +
      "or configure an MRC under Admin &rarr; MRC.</div></div>";
  },

  // MRC status: a one-line summary of the product's MRC linkage — its latest
  // sign-off decision (or a pending request), linking through to the full record.
  _mrcStatusRow(d) {
    const hist = d.rag_signoff_history || [];
    const latest = hist.length ? hist[hist.length - 1] : null;
    const pending = (this._risk || {}).pending_signoff;
    let value;
    if (latest) {
      const outcome = latest.outcome || "Approved";
      const color = outcome === "Rejected" ? "var(--red)" : "#388e3c";
      value = '<span style="color:' + color + ';font-weight:600">' + esc(outcome) + "</span> at " +
        '<span class="code">' + esc(latest.meeting_id) + "</span>" +
        (latest.date ? " (" + esc(latest.date) + ")" : "");
    } else if (pending) {
      value = pending.status === "Attached"
        ? 'Pending — on the agenda of <span class="code">' + esc(pending.meeting_id) + "</span>"
        : "Pending — queued for " + esc(pending.target_mrc || "its MRC");
    } else {
      value = '<span class="muted">No MRC decision yet</span>';
    }
    return '<div class="inforow"><div class="k">MRC status</div><div class="v">' + value +
      '</div><span class="edit-btn" data-open-linkage="1">view</span></div>';
  },

  // The MRC linkage tab: granted sign-offs plus decisions/actions linked from
  // meetings (read-only, sourced from the meeting log). Mirrors the model view.
  _mrcLinkage(d) {
    const signoffs = d.rag_signoff_history || [];
    const soSection = signoffs.length
      ? DetailTabs.signoffHistory(signoffs)
      : '<div class="section-header">Sign-off history</div>' +
        '<div class="empty">No MRC sign-offs granted yet.</div>';
    return '<p class="muted">The product&rsquo;s MRC record — granted rating sign-offs, plus ' +
      "decisions and actions linked from meetings (read-only, sourced from the meeting log).</p>" +
      soSection +
      '<div class="section-header">Decisions</div>' +
      DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]) +
      '<div class="section-header">Actions</div>' +
      DetailTabs.linkedItems("Actions", this._actions, ["description", "owner", "target_date", "status"]);
  },

  // Wire the MRC-status "view" link (rendered inside the overview) to the
  // linkage tab — the overview content is injected after the tabbar handlers
  // bind, so this link needs its own binding.
  _bindLinkageLink() {
    const link = document.querySelector('[data-open-linkage]');
    if (link) link.onclick = () => { this._tab = "linkage"; this._render(); };
  },

  _editLink(key) {
    return this._product.retired ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
  },

  _bindingRow(key, d) {
    const f = this.fieldSpec(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v"><span class="code">' + fieldDisplay(d[key]) + "</span></div>" +
      (this._product.retired ? "" : '<span class="edit-btn" data-rebind="' + key + '">rebind</span>') + "</div>";
  },

  _row(key, d) {
    const f = this.fieldSpec(key);
    let value = fieldDisplay(d[key]);
    if (key === "status") value = productStatusBadge(d[key], this._product.retired);
    else if (key === "rag_rating") {
      // Owner's RAG alongside the heatmap ("Table") RAG — any divergence needing
      // MRC sign-off is visible at a glance, exactly as on a model.
      const tableRag = (this._risk.heatmap || {}).rag;
      value = '<span class="muted" style="font-size:11px">Owner</span> ' + ragBadge(d[key]) +
        '<span class="muted" style="font-size:11px;margin-left:12px">Table</span> ' +
        (tableRag ? ragBadge(tableRag) : '<span class="muted">&mdash;</span>');
    } else if (key === "tier" && (d[key] || d[key] === 0)) {
      value = tierBadge(d[key]) + ' <span class="muted">' + esc(tierFullLabel(d[key])) + "</span>";
    }
    // MRC sign-off shows the granting meeting (not the raw date) once approved.
    else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // The sign-off date/meeting are set by the MRC approval, not edited by hand.
    const editLink = key === "mrc_signoff_date" ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + value + "</div>" + editLink + "</div>";
  },

  // MRC sign-off state: a pending/queued request, or a button to request one.
  _signoffPanel(d) {
    const pending = (this._mrc || {}).pending_signoff;
    if (pending) {
      const detail = pending.status === "Attached"
        ? 'on the agenda of <span class="code">' + esc(pending.meeting_id) + "</span>" +
          (pending.meeting_date ? " (" + esc(pending.meeting_date) + ")" : "")
        : "queued for <b>" + esc(pending.target_mrc || "its MRC") +
          "</b> — added to that committee's next scheduled meeting";
      return '<div class="dz-row" style="border:1px solid #f57c00;background:#fff8e1;' +
        'padding:10px 14px;border-radius:6px;margin:8px 0"><div class="dz-text">' +
        '<b>Pending MRC sign-off</b><p class="muted">Proposed <b>' + esc(pending.proposed_rag) +
        "</b> " + detail + ".</p></div></div>";
    }
    if (this._product.retired) return "";
    if (!d.rag_rating) {
      return '<p class="muted" style="font-size:12px;margin:6px 0">Set a RAG rating to request MRC sign-off.</p>';
    }
    if (!(this._mrc || {}).mrc) return "";   // _mrcRow already explains the missing committee
    return '<div class="dz-row" style="border:1px solid var(--line);padding:10px 14px;' +
      'border-radius:6px;margin:8px 0"><div class="dz-text"><b>' + esc(d.rag_rating) +
      " rating not yet signed off</b><p class=\"muted\">Request MRC sign-off — routed to the " +
      "product's committee, picked up at its next meeting.</p></div>" +
      '<div class="dz-action"><button class="btn small primary" id="preq-signoff" data-proposed="' +
      esc(d.rag_rating) + '">Request MRC sign-off&hellip;</button></div></div>';
  },

  _bindSignoffRequest() {
    const btn = document.getElementById("preq-signoff");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const mrc = (self._mrc || {}).mrc;
      if (!mrc) {
        App.toast("No MRC covers this product — bind a model / set up an MRC first.", "error");
        return;
      }
      App.amend("Request MRC sign-off for " + self._id + " → " + btn.getAttribute("data-proposed") +
        " (routed to " + (mrc.name || mrc.value) + ").", "POST",
        "/api/products/" + self._id + "/request-signoff", {},
        () => self.show(self._id, "overview"));
    };
  },

  // Danger tab: retire the Product (mirrors the model's Danger zone).
  _dangerContent() {
    if (this._product.retired) {
      return '<div class="empty">This Product is retired and read-only. Nothing further can be changed.</div>';
    }
    return '<div class="danger-zone">' +
      '<div class="dz-header">Danger Zone</div>' +
      '<div class="dz-row">' +
      '<div class="dz-text"><b>Retire this Product</b>' +
      '<p class="muted">Retired Products become read-only — no further amendments are accepted. ' +
      "Existing data and audit trail are preserved.</p></div>" +
      '<div class="dz-action"><button class="btn danger small" id="product-retire">Retire Product&hellip;</button></div>' +
      "</div></div>";
  },

  _bindDanger() {
    const self = this;
    if (this._product.retired) return;
    const retire = document.getElementById("product-retire");
    if (retire) retire.onclick = function () {
      App.amend("Retire Product " + self._id + " (it can no longer be edited).", "POST",
        "/api/products/" + self._id + "/retire", {}, function () { Product.render(); });
    };
  },

  _bindEdits() {
    const self = this;
    if (this._product.retired) return;
    document.querySelectorAll("[data-edit]").forEach(function (btn) {
      const key = btn.getAttribute("data-edit");
      btn.onclick = function () { self._editor(self.fieldSpec(key), "field", "/field", "Set"); };
    });
    document.querySelectorAll("[data-rebind]").forEach(function (btn) {
      const key = btn.getAttribute("data-rebind");
      btn.onclick = function () { self._editor(self.fieldSpec(key), "component", "/rebind", "Rebind"); };
    });
  },

  // One inline editor for both scalar fields (POST /field) and bindings (POST /rebind).
  _editor(f, paramKey, endpoint, verb) {
    const row = document.getElementById("row-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      inputControl("ped-input", f) + '<button class="btn small primary" id="ped-save">' + verb +
      '…</button><button class="btn small" id="ped-cancel">Cancel</button></div>';
    const input = document.getElementById("ped-input");
    const current = this._product.data[f.key];
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("ped-cancel").onclick = () => this.show(this._id, "overview");
    document.getElementById("ped-save").onclick = () => {
      const body = paramKey === "component"
        ? { component: f.key, value: input.value.trim() }
        : { field: f.key, value: input.value.trim() };
      App.amend(verb + " " + f.label + ' to "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/products/" + this._id + endpoint, body,
        () => { this.show(this._id, "overview"); Product.loadList(); });
    };
  },
};
