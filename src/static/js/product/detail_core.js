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

// Product detail (the ProductDetail package). This core module owns the fetch, the
// header, the tab bar and the routing between tabs. What each tab draws is
// detail_tabs.js; the per-field rows, inline editors, sign-off panel and Danger tab
// augment ProductDetail from detail_edit.js. Both load after this file. The identifier
// is derived from the bindings.
const PRODUCT_OVERVIEW_PRODUCT = ["product", "product_id", "description"];
const PRODUCT_OVERVIEW_ORG = ["division", "line_of_business", "functional_group"];
// The risk assessment (what places the product on the heatmap) lives on the Risk tab,
// next to the grid it drives; only the headline rag_rating stays on Overview.
// The fields themselves are the risk-assessment table's business (risk_assessment.js):
// one row per dimension, in the Admin editor's Dimension / Rating / Rationale columns.
// The standing description of how the product is monitored. The results
// themselves are no longer a scalar field — they are timestamped uploads under
// the "Monitoring" category, on the Docs tab's Monitoring sub-tab.
const PRODUCT_OVERVIEW_MONITORING = ["monitoring_approach"];
const PRODUCT_OVERVIEW_GOV = ["status", "owner", "mrc_signoff_date", "next_review_date",
  "last_review_date", "notes"];

const ProductDetail = {
  _id: null, _product: null, _specs: null, _audit: [], _mrc: null, _risk: null,
  _decisions: [], _actions: [], _tab: "overview",

  // ``opts.scroll === false`` refreshes in place without jumping to the top — used
  // by the register tabs so an auto-save does not scroll the page on every edit.
  async show(productId, tab, opts) {
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
    if (!opts || opts.scroll !== false) {
      document.getElementById("product-detail").scrollIntoView({ block: "start" });
    }
  },

  fieldSpec(key) { return Product.fieldSpec(key); },
  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const d = this._product.data || {};
    const listview = document.getElementById("product-listview");
    if (listview) listview.style.display = "none";
    document.getElementById("product-detail").innerHTML =
      '<div style="margin-bottom:var(--space-6)"><button class="btn small" id="product-back">&lsaquo; All Products</button></div>' +
      '<div class="card">' + this._header(d) + this._tabbar(d) + '<div id="pt-content"></div></div>';
    document.getElementById("product-back").onclick = () => ProductDetail.close();
    document.querySelectorAll("[data-ptab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-ptab"); this._render(); };
    });
    this._renderContent();
  },

  // Return to the list without a full refetch (the list is kept current on edits).
  //
  // Both lookups are guarded, not just the listview: this also runs when the Products
  // tab is opened, including the very first time, when the panel has not been rendered
  // and neither element exists yet. Throwing there aborted the render that was about
  // to create them and the tab came up blank.
  close() {
    this._tab = "overview";
    const detail = document.getElementById("product-detail");
    if (detail) detail.innerHTML = "";
    const listview = document.getElementById("product-listview");
    if (listview) listview.style.display = "";
  },

  _header(d) {
    return '<div class="detail-header"><div>' +
      '<div class="name">' + fieldDisplay(d.product) + "</div>" +
      '<div class="sub"><span class="code">' + fieldDisplay(d.identifier) + "</span> · " + esc(this._id) +
      (d.product_id ? " · " + esc(d.product_id) : "") + "</div>" +
      '<div style="margin-top:var(--space-4)">' + productStatusBadge(d.status, this._product.retired) + "</div></div>" +
      '<div class="right"><div class="olabel">OWNER</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div></div></div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const tabs = [
      ["overview", "Overview", null],
      // Components is the Product definition — its typed component models. The
      // collection + backend existed and were shown read-only on the overview, but
      // there was no editor tab, so a Product could not be defined from the UI.
      ["components", "Components", n("components")],
      ["model_map", "Model Map", null],
      ["limitations", "Limitations", n("limitations")],
      ["assumptions", "Assumptions", n("assumptions")],
      ["remediation_steps", "Remediation", openRemediationCount(d.remediation_steps)],
      // SR 26-2 validation questions are a model-level concept; a Product validates
      // through its component models, not a separate product questionnaire.
      ["operational_failure_events", "Events", n("operational_failure_events")],
      ["raci_roles", "RACI", n("raci_roles")],
      ["risk", "Risk Rating", null], ["linkage", "MRC", null],
      ["docs", "Docs", DocLinks.countIn(d.documents, this._specs.doc_tab_categories)],
      // Audit is the final tab — the complete, read-only record of every change,
      // entry and upload, so it always sits last after Danger.
      ["danger", "Danger", null], ["audit", "Audit", this._audit.length],
    ];
    return DetailShell.tabBar(tabs, this._tab, "data-ptab");
  },
};
