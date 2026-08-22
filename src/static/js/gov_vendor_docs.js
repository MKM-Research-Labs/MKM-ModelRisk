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

// Vendors panel of the Documents tab: what a supplier hands over about its own
// product, filed against the vendor it came from. The vendor list is the
// Admin-defined one (Admin > Vendor) — the same list a model's Vendor field picks
// from — so a document can only be filed against a declared vendor.
//
// One table across every vendor rather than a sub-tab each (the shape Artefacts
// uses for divisions): a vendor list grows long, and what is wanted here is every
// vendor document at once, narrowed to one supplier only when that is the question.
const GovVendorDocs = {
  _vendors: [],
  _docs: {},          // vendor_id -> [document]
  _filter: "",        // vendor_id, or "" for all

  async load() {
    const data = await App.get("/api/vendor-documents");
    this._vendors = data.vendors || [];
    this._docs = data.documents || {};
    if (this._filter && !this._vendors.some((v) => v.vendor_id === this._filter)) {
      this._filter = "";
    }
  },

  _rows() {
    const out = [];
    this._vendors.forEach((v) => {
      if (this._filter && v.vendor_id !== this._filter) return;
      (this._docs[v.vendor_id] || []).forEach((d) => out.push({ vendor: v, doc: d }));
    });
    return out;
  },

  _vendorOptions(all) {
    const opts = all ? ['<option value="">All vendors</option>'] : [];
    return opts.concat(this._vendors.map((v) =>
      '<option value="' + esc(v.vendor_id) + '">' + esc(v.name) + "</option>")).join("");
  },

  // Nothing to file against until Admin defines a vendor, so say where to do that
  // rather than offering an upload box that can only fail.
  _noVendors() {
    return '<p class="empty">No vendors defined yet &mdash; add them in Admin ' +
      "&rsaquo; Vendor, then file their documents here.</p>";
  },

  _uploadRow() {
    return '<div class="row" style="align-items:center;margin-top:var(--space-7)">' +
      '<select id="gv-vendor">' + this._vendorOptions(false) + "</select>" +
      '<input type="file" id="gv-file">' +
      '<input id="gv-desc" placeholder="Description (optional)" style="flex:1">' +
      '<button class="btn small primary" id="gv-upload">Upload</button></div>';
  },

  shell(panelTabs) {
    const body = this._vendors.length
      ? '<div class="row" style="align-items:center;margin-bottom:var(--space-4)">' +
        '<label class="muted" style="margin-right:var(--space-3)">Filter:</label>' +
        '<select id="gv-filter">' + this._vendorOptions(true) + "</select></div>" +
        "<table><thead><tr><th>Vendor</th><th>Name</th><th>Description</th>" +
        "<th>Date Added</th><th>Size</th><th>Actions</th></tr></thead>" +
        '<tbody id="gv-rows">' + this._rowsHtml() + "</tbody></table>" + this._uploadRow()
      : this._noVendors();
    return '<div class="card"><h3>Documents</h3>' + panelTabs +
      '<p class="muted" style="margin-top:var(--space-5)">What a third-party supplier gives ' +
      "us &mdash; contracts, assurance reports, the vendor's own model documentation. " +
      "Filed against the vendor it came from; manage the vendor list in Admin " +
      "&rsaquo; Vendor.</p>" + body + "</div>";
  },

  _rowsHtml() {
    const rows = this._rows();
    if (!rows.length) {
      return '<tr><td colspan="6" class="empty">No vendor documents' +
        (this._filter ? " for this vendor." : " uploaded yet.") + "</td></tr>";
    }
    return rows.map(({ vendor, doc }) => {
      const base = "/api/vendor-documents/" + encodeURIComponent(vendor.vendor_id) +
        "/" + esc(doc.item_id);
      return "<tr><td>" + esc(vendor.name) + "</td><td>" + esc(doc.original_name) +
        "</td><td>" + (doc.description ? esc(doc.description) : '<span class="muted">—</span>') +
        "</td><td>" + esc((doc.uploaded_at || "").slice(0, 10)) + "</td><td>" +
        fmtSize(doc.size) + '</td><td class="rowact"><a href="' + base + '/download">Download</a>' +
        ' <button class="btn small danger" data-gvrm="' + esc(doc.item_id) +
        '" data-gvvendor="' + esc(vendor.vendor_id) + '">Delete</button></td></tr>';
    }).join("");
  },

  bind() {
    const self = this;
    const filter = document.getElementById("gv-filter");
    if (filter) {
      filter.value = this._filter;
      filter.onchange = function () {
        self._filter = this.value;
        document.getElementById("gv-rows").innerHTML = self._rowsHtml();
        self._bindRows();
      };
    }
    const up = document.getElementById("gv-upload");
    if (up) up.onclick = () => this._upload();
    this._bindRows();
  },

  _bindRows() {
    const self = this;
    document.querySelectorAll("[data-gvrm]").forEach(function (el) {
      const itemId = el.getAttribute("data-gvrm");
      const vendorId = el.getAttribute("data-gvvendor");
      el.onclick = function () {
        App.amend("Delete vendor document " + itemId + "?", "POST",
          "/api/vendor-documents/" + encodeURIComponent(vendorId) + "/" + itemId + "/delete",
          {}, () => GovDocs.render());
      };
    });
  },

  _upload() {
    const file = document.getElementById("gv-file");
    if (!file.files.length) { App.toast("Choose a file first", "error"); return; }
    const vendorId = document.getElementById("gv-vendor").value;
    if (!vendorId) { App.toast("Choose a vendor first", "error"); return; }
    const form = new FormData();
    form.append("file", file.files[0]);
    form.append("description", document.getElementById("gv-desc").value);
    fetch("/api/vendor-documents/" + encodeURIComponent(vendorId), {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.error || "upload failed");
      }
      App.toast("Vendor document uploaded", "ok");
      GovDocs.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
