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

// A coloured status pill (shared with the Product detail view).
function productStatusBadge(status, retired) {
  if (retired) return '<span class="pill">retired</span>';
  const colors = { Active: "#388e3c", Proposed: "#0288d1", Suspended: "#f57c00", Retired: "#9e9e9e" };
  const c = colors[status] || "#9e9e9e";
  return '<span style="display:inline-block;padding:2px 9px;border-radius:10px;color:#fff;' +
    'font-size:12px;background:' + c + '">' + esc(status || "—") + "</span>";
}

// Products (Product Valuation Models): one Analytics Model can underpin many Products.
const Product = {
  _specs: null,
  _ref: {},                       // reference data (mrc / division / department)
  _committees: [],

  async specs() {
    // Re-fetch so new inventory models / reference values populate the dropdowns.
    this._specs = await App.get("/api/products/fields");
    return this._specs;
  },

  fieldSpec(key) {
    let found = null;
    this._specs.groups.forEach((g) => g.fields.forEach((f) => { if (f.key === key) found = f; }));
    return found;
  },

  async render() {
    await this.specs();
    // List and detail are siblings; opening a Product hides the list view (master-detail).
    document.getElementById("tab-product").innerHTML =
      '<div id="product-listview"><div id="product-mrcnav">' + MrcNav.cachedHtml() +
      '</div><div id="product-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">Product Valuation Models</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="product-register">+ Register Product</button></div>' +
      '<div id="product-list" style="margin-top:12px"></div></div></div>' +
      '<div id="product-detail"></div>';
    document.getElementById("product-register").onclick = () => this.openRegister();
    await this.loadList();
  },

  // Register with the Product ID, product and three component bindings.
  openRegister() {
    const idField = '<div class="field"><label for="preg-product_id">Product ID *</label>' +
      '<input id="preg-product_id" placeholder="Product-0001"></div>';
    const body = this._specs.register.map((k) => {
      const f = this.fieldSpec(k);
      return '<div class="field"><label for="preg-' + k + '">' + esc(f.label) + " *</label>" +
        inputControl("preg-" + k, f) + "</div>";
    }).join("");
    document.getElementById("product-reg-body").innerHTML = idField + body;
    document.getElementById("product-register-overlay").classList.remove("hidden");
    document.getElementById("preg-product_id").focus();
  },

  closeRegister() {
    document.getElementById("product-register-overlay").classList.add("hidden");
  },

  submitRegister() {
    const id = val("preg-product_id"), product = val("preg-product");
    if (!id || !product || !val("preg-analytics_model")) {
      App.toast("Product ID, Product and Analytics Model are required", "error"); return;
    }
    const fields = {};
    this._specs.bindings.forEach((k) => { const v = val("preg-" + k); if (v !== "") fields[k] = v; });
    this.closeRegister();
    App.amend('Register Product "' + id + '" for ' + product + ".", "POST", "/api/products",
      { product_id: id, product: product, fields: fields }, () => this.render());
  },

  _summary(products) {
    const n = (s) => products.filter((p) => (p.data || {}).status === s && !p.retired).length;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    return '<div class="summary">' +
      card("Total", products.length, "#1976d2") +
      card("Active", n("Active"), "#388e3c") +
      card("Proposed", n("Proposed"), "#0288d1") +
      card("Suspended", n("Suspended"), "#f57c00") +
      card("Retired", products.filter((p) => p.retired).length, "#9e9e9e") +
      "</div>";
  },

  // Render the shared MRC-region navigator and wire it to re-filter the list.
  _renderNav() {
    const nav = document.getElementById("product-mrcnav");
    MrcNav.normalize(this._committees, this._ref);
    nav.innerHTML = MrcNav.html(this._committees, this._ref);
    MrcNav.bind(nav, this._committees, this._ref, () => this.loadList());
  },

  async loadList() {
    const nav = await MrcNav.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    this._renderNav();
    const all = await App.get("/api/products");
    const products = all.filter((p) => MrcNav.inScope(this._committees, this._ref, p.data));
    document.getElementById("product-summary").innerHTML = this._summary(products);
    const box = document.getElementById("product-list");
    if (!products.length) {
      box.innerHTML = '<div class="empty">' +
        (MrcNav.state.div ? "No products in this MRC scope." : "No Products yet. Register one above.") +
        "</div>";
      return;
    }
    let rows = "";
    products.forEach(function (p) {
      const d = p.data || {};
      rows +=
        '<tr class="clickable" data-id="' + esc(p.product_id) + '">' +
        '<td class="modelid">' + esc(p.product_id) + "</td>" +
        '<td><span class="code">' + fieldDisplay(d.identifier) + "</span></td>" +
        "<td>" + fieldDisplay(d.product) + "</td>" +
        "<td>" + fieldDisplay(d.analytics_model) + "</td>" +
        "<td>" + mrcStatusBadge(d) + "</td>" +
        "<td>" + productStatusBadge(d.status, p.retired) + "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Identifier</th><th>Product</th>" +
      "<th>Analytics Model</th><th>MRC Status</th><th>Status</th></tr></thead><tbody>" + rows + "</tbody></table>";
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.onclick = function () { ProductDetail.show(tr.getAttribute("data-id")); };
    });
  },
};
