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

// Product detail (the ProductDetail package). This core module owns the header,
// tab bar and routing, the Overview render and the MRC linkage view. The per-
// field rows, inline editors, sign-off panel and Danger tab augment ProductDetail
// from detail_edit.js, loaded after. The identifier is derived from the bindings.
const PRODUCT_OVERVIEW_PRODUCT = ["product", "product_id", "description"];
const PRODUCT_OVERVIEW_ORG = ["division", "line_of_business"];
// The risk assessment (what places the product on the heatmap) lives on the Risk tab,
// next to the grid it drives; only the headline rag_rating stays on Overview.
const PRODUCT_RISK_ASSESSMENT = ["tier", "materiality", "complexity"];
// The standing description of how the product is monitored. The results
// themselves are no longer a scalar field — they are timestamped uploads under
// the "Monitoring" category, on the Docs tab's Monitoring sub-tab.
const PRODUCT_OVERVIEW_MONITORING = ["monitoring_approach"];
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
      '<div style="margin-top:8px">' + productStatusBadge(d.status, this._product.retired) + "</div></div>" +
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
    if (this._tab === "model_map") {
      box.innerHTML =
        '<p class="muted" style="font-size:12px;margin-bottom:10px">The models this product is built ' +
        "from (its components) and the feed-chain they sit in. Data sources sit on top and supply the models " +
        "beneath them (amber arrows); grey arrows run producer &rarr; consumer. Click any model to open it.</p>" +
        '<div id="pmap-host"></div>';
      ProductMap.render(this._id, "pmap-host");
      return;
    }
    if (this._tab === "danger") { box.innerHTML = this._dangerContent(); this._bindDanger(); return; }
    if (this._tab === "risk") {
      box.innerHTML =
        '<div class="section-header">Risk assessment</div>' +
        '<p class="muted" style="font-size:12px;margin:0 0 8px">The owner sets these; they place ' +
        "the product on the heatmap below, which becomes its rating once the MRC signs it off.</p>" +
        PRODUCT_RISK_ASSESSMENT.map((k) => this._row(k, d)).join("") +
        DetailTabs.risk(this._risk);
      this._bindEdits();
      this._bindSignoffRequest();
      return;
    }
    if (this._tab === "linkage") { box.innerHTML = this._mrcLinkage(d); return; }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "docs") {
      // Docs is the product's own documentation and supporting analysis; testing
      // and evidence categories are captured in-context on their own tabs. The
      // Product Document and the product pack are generated from the current
      // record on request, so they are offered as actions rather than filed as
      // rows that could go stale — and the pack pulls in the full pack of every
      // model the product binds.
      box.innerHTML =
        '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:10px">' +
        '<span class="muted" style="font-size:12px">The full write-up for this product, ' +
        "generated from the current record — on its own, or zipped with the full pack of every " +
        "model it binds, to send on.</span>" +
        '<span><a class="btn small" href="/api/products/' + esc(this._id) +
        '/pack.zip">Product pack (ZIP)</a> ' +
        '<a class="btn small primary" target="_blank" rel="noopener" id="prd-issue" href="/api/products/' +
        esc(this._id) + '/document.pdf">Product Document (PDF)</a></span></div>' +
        '<div id="pdocs-host"></div>';
      ModelDocs.render(this._id, d.documents || [], this._specs.doc_tab_categories || [],
        this._product.retired, "/api/products/", () => this.show(this._id, "docs"), "pdocs-host");
      // Issuing a document files a copy under History. The PDF opens in a new
      // tab, so reload the docs tab or History lags behind what was just issued.
      const issue = document.getElementById("prd-issue");
      if (issue) {
        issue.addEventListener("click", () => {
          setTimeout(() => this.show(this._id, "docs"), 1500);
        });
      }
      return;
    }
    const spec = this.collSpec(this._tab);
    let html = Collections.render(d, { collections: [spec] }, this._product.retired);
    const docCat = COLLECTION_DOC_CATEGORY[this._tab];
    const docOpts = { category: docCat, docs: d.documents || [], base: "/api/products/", id: this._id,
      retired: this._product.retired, refresh: () => this.show(this._id, this._tab) };
    if (docCat) html += '<div class="section-header" style="margin-top:14px">Supporting documents</div>' +
      DocPanel.html(docOpts);
    box.innerHTML = html;
    Collections.bind("/api/products/" + this._id + "/collections/", { collections: [spec] },
      this._product.retired, () => this.show(this._id, this._tab), d);
    if (docCat) DocPanel.bind(docOpts);
  },

  _section(title, keys, d) {
    return '<div class="section-header">' + title + "</div>" +
      keys.map((k) => this._row(k, d)).join("");
  },

  _overview(d) {
    const bindings = this._specs.bindings.map((k) => this._bindingRow(k, d)).join("");
    const left = '<div class="section-header">Components</div>' +
      this._componentRows(d) + bindings +
      this._section("Product", PRODUCT_OVERVIEW_PRODUCT, d) +
      this._section("Organisation", PRODUCT_OVERVIEW_ORG, d) +
      this._section("Monitoring", PRODUCT_OVERVIEW_MONITORING, d);
    const right = this._section("Risk rating", ["rag_rating"], d) + this._signoffPanel(d) +
      this._section("Governance &amp; review", PRODUCT_OVERVIEW_GOV, d) +
      this._mrcRow(d) + this._mrcStatusRow(d);
    // Retire lives on the Danger tab; the Overview only flags a retired Product.
    const status = this._product.retired
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
    return '<div class="grid2"><div>' + left + "</div><div>" + right + "</div></div>" + status;
  },

  // The MRC responsible for this product, derived from its Division/Line of Business
  // (Line of Business-level → Division-level → Company). Flags red when none covers it.
  _mrcRow(d) {
    const m = this._mrc || {};
    const head = '<div class="section-header">MRC</div>';
    if (m.mrc) {
      const c = m.mrc;
      return head + '<div class="inforow"><div class="k">Committee</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:11px">' + esc(m.level || "") + "-level</div></div>";
    }
    const org = [d.division, d.line_of_business].filter(Boolean).join(" / ") || "no division / line of business set";
    return head + '<div class="inforow"><div class="v" style="color:var(--red)">&#9888; ' +
      "No committee covers this product (" + esc(org) + "). Set its Division/Line of Business, " +
      "or configure an MRC under Admin &rarr; MRC.</div></div>";
  },

  // MRC status: a one-line summary of the product's MRC linkage — its latest
  // sign-off decision (or a pending request), linking through to the full record.
  _mrcStatusRow(d) {
    const hist = d.signoff_history || [];
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

  // The MRC linkage tab: granted sign-offs plus decisions linked from meetings
  // (read-only). Actions are now first-class on the product (the Actions tab).
  _mrcLinkage(d) {
    const signoffs = d.signoff_history || [];
    const soSection = signoffs.length
      ? DetailTabs.signoffHistory(signoffs)
      : '<div class="section-header">Sign-off history</div>' +
        '<div class="empty">No MRC sign-offs granted yet.</div>';
    return '<p class="muted">The product&rsquo;s MRC record — granted rating sign-offs, plus ' +
      "decisions linked from meetings (read-only, sourced from the meeting log).</p>" +
      soSection +
      '<div class="section-header">Decisions</div>' +
      DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]);
  },

  // Wire the MRC-status "view" link (rendered inside the overview) to the
  // linkage tab — the overview content is injected after the tabbar handlers
  // bind, so this link needs its own binding.
  _bindLinkageLink() {
    const link = document.querySelector('[data-open-linkage]');
    if (link) link.onclick = () => { this._tab = "linkage"; this._render(); };
  },
};
