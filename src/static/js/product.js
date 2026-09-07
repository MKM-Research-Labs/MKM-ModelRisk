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

// A coloured status pill (shared with the Product detail view).
function productStatusBadge(status, retired) {
  if (retired) return '<span class="pill">retired</span>';
  const c = Theme.colour("product_status", status);
  // ``nowrap`` because the Status column narrowed when the list gained Criticality and
  // Risk Rating: "Proposed" broke across two lines inside the pill and read as damage.
  return '<span style="display:inline-block;white-space:nowrap;padding:var(--space-1) 9px;' +
    'border-radius:var(--radius-xl);color:var(--inverse);' +
    'font-size:var(--size-sm);background:' + c + '">' + esc(status || "—") + "</span>";
}

// Products (Product Valuation Models): one Analytics Model can underpin many Products.
// A Product's components at a glance: how many models it binds and of what kind.
// The list used to show the single Analytics Model, which cannot describe a
// structured product built from several.
function componentSummary(d) {
  const items = d.components || [];
  if (!items.length) { return '<span class="muted">none</span>'; }
  const kinds = {};
  items.forEach(function (c) {
    const k = c.component_type || "Unclassified";
    kinds[k] = (kinds[k] || 0) + 1;
  });
  return esc(Object.keys(kinds).sort().map(function (k) {
    return kinds[k] > 1 ? kinds[k] + " x " + k : k;
  }).join(", "));
}

const Product = {
  _specs: null,
  _ref: {},                       // reference data (mrc / division / line_of_business)
  _committees: [],

  async specs() {
    // Re-fetch so new inventory models / reference values populate the dropdowns.
    this._specs = await App.get("/api/products/fields");
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
  onShow() { ProductDetail.close(); },

  async render() {
    await this.specs();
    // List and detail are siblings; opening a Product hides the list view (master-detail).
    document.getElementById("tab-product").innerHTML =
      '<div id="product-listview"><div id="product-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">Product Valuation Models</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="product-register">+ Register Product</button></div>' +
      '<div id="product-list" style="margin-top:var(--space-6)"></div></div></div>' +
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
    if (!id || !product) {
      App.toast("Product ID and Product are required", "error"); return;
    }
    const fields = {};
    this._specs.bindings.forEach((k) => { const v = val("preg-" + k); if (v !== "") fields[k] = v; });
    this.closeRegister();
    App.amend('Register Product "' + id + '" for ' + product + ".", "POST", "/api/products",
      { product_id: id, product: product, fields: fields }, () => this.render());
  },

  // The same list every other register draws -- tiles, filters, a sortable table and
  // the functional-group headings -- through createRecordList. Products hand-rolled its
  // own <tr> strings until now, which is why it was the one register with no filters, no
  // sorting and no clickable tiles; the columns are still its own, because Identifier
  // and Components are facts no model has.
  _list: null,

  list() {
    if (!this._list) {
      const self = this;
      this._list = createRecordList({
        idKey: "product_id", summaryId: "product-summary", listId: "product-list",
        filtersId: "prd-filters", tableId: "prd-table", p: "pf-", noun: "Products",
        // A Product is Active or Suspended; it has no lifecycle stage. The filter and
        // the vocabulary behind it follow this rather than a model's field.
        statusField: "status",
        statusFilterLabel: "All statuses",
        groupBy: "functional_group",
        // The status counts this screen has always carried. They are a Product's own
        // vocabulary, so they stay as the register's extra tiles rather than being
        // pushed into the shared set, where they would mean nothing on a model.
        extraTiles: (live, tile) => {
          const n = (v) => live.filter((m) => m.d.status === v).length;
          return [tile("Active", n("Active"), Theme.value("green"), ""),
                  tile("Proposed", n("Proposed"), Theme.value("info"), ""),
                  tile("Suspended", n("Suspended"), Theme.value("amber"), "")];
        },
        spec: (key) => self.fieldSpec(key),
        reload: () => self.loadList(),
      }, [
        { key: "id", label: "ID", sortVal: (m) => m.id.toLowerCase(),
          cell: (m) => '<span class="modelid">' + esc(m.id) + "</span>" },
        { key: "identifier", label: "Identifier",
          sortVal: (m) => (m.d.identifier || "").toLowerCase(),
          cell: (m) => '<span class="code">' + fieldDisplay(m.d.identifier) + "</span>" },
        { key: "product", label: "Product",
          sortVal: (m) => (m.d.product || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.product) },
        { key: "components", label: "Components",
          sortVal: (m) => (m.d.components || []).length,
          cell: (m) => componentSummary(m.d) },
        { key: "tier", label: "Criticality", sortVal: (m) => m.d.tier || 99,
          cell: (m) => tierBadge(m.d.tier, m.d.division) },
        { key: "rag", label: "Risk Rating",
          sortVal: (m) => ragOrder(m.d.rag_rating, m.d.division),
          cell: (m) => ragBadge(m.d.rag_rating, m.d.division) },
        { key: "mrc", label: "MRC Status", sortVal: (m) => mrcState(m.d),
          cell: (m) => mrcStatusBadge(m.d) },
        { key: "status", label: "Status",
          sortVal: (m) => m.retired ? "zz" : (m.d.status || "").toLowerCase(),
          cell: (m) => productStatusBadge(m.d.status, m.retired) },
      ]);
    }
    return this._list;
  },

  async loadList() {
    const nav = await MrcNav.load();
    await Groups.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    const all = await App.get("/api/products");
    const products = all.filter((p) => MrcNav.inScope(this._committees, this._ref, p.data));
    if (!products.length) {
      document.getElementById("product-summary").innerHTML = "";
      document.getElementById("product-list").innerHTML = '<div class="empty">' +
        (MrcNav.state.div ? "No products in this scope yet. Register one above."
                          : "No Products yet. Register one above.") + "</div>";
      return;
    }
    this.list().mount(products, (id) => ProductDetail.show(id));
  },
};
