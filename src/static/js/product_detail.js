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
const PRODUCT_OVERVIEW_MONITORING = ["monitoring_approach", "monitoring_results"];
const PRODUCT_OVERVIEW_GOV = ["status", "owner", "mrc_signoff_date", "next_review_date",
  "last_review_date", "notes"];

const ProductDetail = {
  _id: null, _product: null, _specs: null, _audit: [], _tab: "overview",

  async show(productId, tab) {
    this._id = productId;
    this._specs = Product._specs || await Product.specs();
    this._product = await App.get("/api/products/" + productId);
    this._audit = (await App.get("/api/audit")).filter((e) => e.aggregate_id === productId);
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
      ["overview", "Overview", null], ["limitations", "Limitations", n("limitations")],
      ["assumptions", "Assumptions", n("assumptions")],
      ["remediation_steps", "Remediation", n("remediation_steps")],
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
    if (this._tab === "overview") { box.innerHTML = this._overview(d); this._bindEdits(); return; }
    if (this._tab === "danger") { box.innerHTML = this._dangerContent(); this._bindDanger(); return; }
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
      this._section("Monitoring", PRODUCT_OVERVIEW_MONITORING, d);
    const right = this._section("Risk rating", ["rag_rating"], d) +
      this._section("Governance &amp; review", PRODUCT_OVERVIEW_GOV, d);
    // Retire lives on the Danger tab; the Overview only flags a retired Product.
    const status = this._product.retired
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
    return '<div class="grid2"><div>' + left + "</div><div>" + right + "</div></div>" + status;
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
    else if (key === "rag_rating") value = ragBadge(d[key]);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + value + "</div>" + this._editLink(key) + "</div>";
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
