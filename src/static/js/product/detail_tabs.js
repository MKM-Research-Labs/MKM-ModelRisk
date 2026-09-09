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

// What each of a Product's tabs draws.
//
// Split from detail_core.js, which says which tabs the record carries, fetches it and
// frames it. This is the dispatch behind them, kept in one place because the tab strip
// is the order the questions get asked in and that order is only checkable if you can
// read it whole.
//
// Overview leads with what the product IS rather than how it is governed: a product is
// its three component bindings, and the identifier is derived from them rather than
// typed, so the Overview says the derivation out loud. The rag_rating is the only piece
// of the risk assessment shown here — the assessment that produces it belongs on the
// Risk tab beside the grid it drives.
//
// Assigns onto ProductDetail; loads after detail_core.js.

Object.assign(ProductDetail, {

  _renderContent() {
    const d = this._product.data || {};
    const box = document.getElementById("pt-content");
    if (this._tab === "overview") {
      box.innerHTML = this._overview(d); this._bindEdits(); this._bindSignoffRequest();
      this._bindLinkageLink(); return;
    }
    if (this._tab === "model_map") {
      box.innerHTML =
        '<p class="muted" style="font-size:var(--size-sm);margin-bottom:var(--space-5)">The models this product is built ' +
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
        '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">The owner sets these; they place ' +
        "the product on the heatmap below, which becomes its rating once the MRC signs it off.</p>" +
        policyNotice(d.division) +
        this._riskTable(d) +
        DetailTabs.risk(this._risk, true, d.division);
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
        '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:var(--space-5)">' +
        '<span class="muted" style="font-size:var(--size-sm)">The full write-up for this product, ' +
        "generated from the current record — on its own, or zipped with the full pack of every " +
        "model it binds, to send on.</span>" +
        '<span><a class="btn small" href="/api/products/' + esc(this._id) +
        '/pack.zip">Product pack (ZIP)</a> ' +
        '<a class="btn small primary" target="_blank" rel="noopener" id="prd-issue" href="/api/products/' +
        esc(this._id) + '/document.pdf">Product Document (PDF)</a></span></div>' +
        '<div id="pdocs-host"></div>';
      ModelDocs.render(this._id, d.documents || [], this._specs.doc_tab_categories || [],
        this._product.retired, "/api/products/", () => this.show(this._id, "docs"), "pdocs-host");
      // Issuing files a copy under History. Fetch the PDF ourselves so we know
      // when the server has finished generating and filing it, then refresh so the
      // new copy appears in History at once — a fixed timer used to race a slow
      // LaTeX compile and leave History lagging. The tab is opened up front, inside
      // the click, so the browser does not treat it as a blocked pop-up.
      const issue = document.getElementById("prd-issue");
      if (issue) {
        issue.addEventListener("click", async (e) => {
          e.preventDefault();
          const win = window.open("", "_blank");
          try {
            const res = await fetch(issue.getAttribute("href"), { headers: App.headers() });
            if (!res.ok) throw new Error("The document could not be generated.");
            if (win) win.location = URL.createObjectURL(await res.blob());
            await this.show(this._id, "docs", { scroll: false });
          } catch (err) {
            if (win) win.close();
            App.toast(err.message || "Document generation failed.", "error");
          }
        });
      }
      return;
    }
    const spec = this.collSpec(this._tab);
    // autosave=true: the product register tabs edit in place, saving on change.
    let html = Collections.render(d, { collections: [spec] }, this._product.retired, false, true);
    const docCat = COLLECTION_DOC_CATEGORY[this._tab];
    // Refresh in place (no scroll) so an auto-saved edit does not jump the page.
    const refresh = () => this.show(this._id, this._tab, { scroll: false });
    const docOpts = { category: docCat, docs: d.documents || [], base: "/api/products/", id: this._id,
      retired: this._product.retired, refresh: refresh };
    if (docCat) html += '<div class="section-header" style="margin-top:var(--space-7)">Supporting documents</div>' +
      DocPanel.html(docOpts);
    box.innerHTML = html;
    Collections.bind("/api/products/" + this._id + "/collections/", { collections: [spec] },
      this._product.retired, refresh, d);
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
      ? '<div style="margin-top:var(--space-7)"><span class="pill">retired — read only</span></div>' : "";
    return '<div class="grid2"><div>' + left + "</div><div>" + right + "</div></div>" + status;
  },
});
