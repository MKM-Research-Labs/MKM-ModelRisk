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

// A compact, embeddable document panel: an upload row plus a small list of the
// documents in ONE category, reusing the aggregate's existing /documents
// endpoints (so uploads also surface in the Docs tab, are audited, etc.). Used
// in-context on the Docs tab's Testing panel, the Events tab and the Remediation
// register on Risk Rating, so evidence can be attached where it belongs. Several
// panels can coexist on a page — every element id is namespaced by the category slug.
const DocPanel = {
  _slug(category) { return "dp-" + category.toLowerCase().replace(/[^a-z0-9]+/g, "-"); },

  // opts: {category, docs, base, id, retired, refresh, compact}
  // `base` e.g. "/api/models/" or "/api/products/"; `docs` is the full documents
  // array (filtered to `category` here); `refresh` re-renders the host tab.
  html(opts) {
    const p = this._slug(opts.category);
    const items = DocLinks.visible(opts.docs, opts.category);
    const rows = items.length
      ? items.map((d) =>
          '<div class="dp-doc">' + esc(d.original_name) + " " +
          DocLinks.actions(opts.base, opts.id, d) +
          (d.description ? ' <span class="muted">— ' + esc(d.description) + "</span>" : "") +
          (opts.retired ? "" : ' <button class="btn small danger" data-' + p + '-rm="' +
            esc(d.item_id) + '">&times;</button>') + "</div>").join("")
      : '<div class="muted" style="font-size:var(--size-sm)">No documents.</div>';
    const upload = opts.retired ? "" :
      '<div class="row" style="align-items:center;margin-top:var(--space-3);gap:var(--space-3)">' +
      '<input type="file" id="' + p + '-file" style="font-size:var(--size-sm)">' +
      '<input id="' + p + '-desc" placeholder="Description (optional)" style="flex:1;font-size:var(--size-sm)">' +
      '<button class="btn small primary" id="' + p + '-upload">Upload</button></div>';
    return '<div class="dp-panel" style="margin:var(--space-2) 0 var(--space-6)">' + rows + upload + "</div>";
  },

  bind(opts) {
    const p = this._slug(opts.category);
    const self = this;
    const upload = document.getElementById(p + "-upload");
    if (upload) upload.onclick = function () { self._upload(opts, p); };
    document.querySelectorAll("[data-" + p + "-rm]").forEach(function (el) {
      const iid = el.getAttribute("data-" + p + "-rm");
      el.onclick = function () {
        App.amend("Delete document " + iid + "?", "POST",
          opts.base + opts.id + "/documents/" + iid + "/delete", {}, opts.refresh);
      };
    });
  },

  _upload(opts, p) {
    const fileInput = document.getElementById(p + "-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    form.append("category", opts.category);
    form.append("description", document.getElementById(p + "-desc").value);
    fetch(opts.base + opts.id + "/documents", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Document uploaded", "ok");
      opts.refresh();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
