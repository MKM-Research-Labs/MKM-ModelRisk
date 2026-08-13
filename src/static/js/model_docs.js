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

// Model Docs tab: per-category (Core Documentation / Sensitivity / Analysis /
// Monitoring / History) uploadable document lists with download and delete.
//
// A sub-tab is normally just a category name. It can instead be a panel object
// {key, label, count, render(hostId)}, which the caller renders itself — the
// model's Testing panel arrives this way, because test evidence spans four
// categories and so cannot be one plain upload list.
const ModelDocs = {
  _id: null, _docs: [], _categories: [], _retired: false, _cat: null,
  _base: "/api/models/", _refresh: null, _host: "dt-content",

  _key(c) { return typeof c === "string" ? c : c.key; },
  _entry(key) {
    const self = this;
    return this._categories.find((c) => self._key(c) === key);
  },

  // Pre-select a sub-tab (by key) before the next render — used where a link
  // targets one panel of the Docs tab rather than the tab as a whole.
  select(key) { this._cat = key; },

  // base / refresh / host let the same renderer serve any aggregate (models, Products).
  render(modelId, docs, categories, retired, base, refresh, host) {
    this._id = modelId;
    this._docs = docs;
    this._categories = categories;
    this._retired = retired;
    this._base = base || "/api/models/";
    this._refresh = refresh || (() => Detail.show(this._id, "docs"));
    this._host = host || "dt-content";
    if (!this._cat || !this._entry(this._cat)) this._cat = this._key(categories[0]);
    document.getElementById(this._host).innerHTML =
      this._subtabs() + '<div id="docs-cat"></div>';
    const self = this;
    document.querySelectorAll("[data-doctab]").forEach(function (b) {
      b.onclick = function () {
        self._cat = b.getAttribute("data-doctab");
        self.render(self._id, self._docs, self._categories, self._retired,
          self._base, self._refresh, self._host);
      };
    });
    this._renderCategory();
  },

  _subtabs() {
    return '<div class="dtabs">' + this._categories.map((c) => {
      const key = this._key(c);
      const n = typeof c === "string" ? DocLinks.visible(this._docs, c).length : c.count;
      const label = typeof c === "string" ? c : c.label;
      return '<button class="dtab' + (key === this._cat ? " active" : "") + '" data-doctab="' +
        esc(key) + '">' + esc(label) + " (" + n + ")</button>";
    }).join("") + "</div>";
  },

  _renderCategory() {
    // A caller-rendered panel owns its own host, uploads and bindings.
    const entry = this._entry(this._cat);
    if (entry && typeof entry !== "string") { entry.render("docs-cat"); return; }
    const items = DocLinks.visible(this._docs, this._cat);
    const rows = items.length ? items.map((d) =>
      "<tr><td>" + esc(d.original_name) + "</td><td>" + fieldDisplay(d.description) + "</td><td>" +
      esc(fmtTimestamp(d.uploaded_at)) + "</td><td>" + fmtSize(d.size) +
      '</td><td class="rowact">' + DocLinks.actions(this._base, this._id, d) +
      (this._retired ? "" : ' <button class="btn small danger" data-rmdoc="' + esc(d.item_id) + '">Delete</button>') +
      "</td></tr>").join("") : '<tr><td colspan="5" class="empty">No documents.</td></tr>';
    const upload = this._retired ? "" :
      '<div class="row" style="align-items:center;margin-bottom:10px"><input type="file" id="doc-file">' +
      '<input id="doc-desc" placeholder="Description (optional)" style="flex:1">' +
      '<button class="btn small primary" id="doc-upload">Upload</button></div>';
    document.getElementById("docs-cat").innerHTML = upload +
      "<table><thead><tr><th>Name</th><th>Description</th><th>Uploaded</th><th>Size</th><th>Actions</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
    this._bind();
  },

  _bind() {
    const self = this;
    const upload = document.getElementById("doc-upload");
    if (upload) upload.onclick = function () { self._upload(); };
    document.querySelectorAll("[data-rmdoc]").forEach(function (el) {
      const iid = el.getAttribute("data-rmdoc");
      el.onclick = function () {
        App.amend("Delete document " + iid + "?", "POST",
          self._base + self._id + "/documents/" + iid + "/delete", {}, self._refresh);
      };
    });
  },

  _upload() {
    const fileInput = document.getElementById("doc-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    form.append("category", this._cat);
    form.append("description", document.getElementById("doc-desc").value);
    fetch(this._base + this._id + "/documents", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json(); throw new Error(e.error || "upload failed"); }
      App.toast("Document uploaded", "ok");
      this._refresh();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
