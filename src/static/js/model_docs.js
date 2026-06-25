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

// Model Docs tab: per-category (Core Documentation / Test Results / Analysis /
// Monitoring) uploadable document lists with download and delete.
const ModelDocs = {
  _id: null, _docs: [], _categories: [], _retired: false, _cat: null,
  _base: "/api/models/", _refresh: null, _host: "dt-content",

  // base / refresh / host let the same renderer serve any aggregate (models, PVMs).
  render(modelId, docs, categories, retired, base, refresh, host) {
    this._id = modelId;
    this._docs = docs;
    this._categories = categories;
    this._retired = retired;
    this._base = base || "/api/models/";
    this._refresh = refresh || (() => Detail.show(this._id, "docs"));
    this._host = host || "dt-content";
    if (!this._cat || categories.indexOf(this._cat) < 0) this._cat = categories[0];
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
      const n = this._docs.filter((d) => d.category === c).length;
      return '<button class="dtab' + (c === this._cat ? " active" : "") + '" data-doctab="' +
        esc(c) + '">' + esc(c) + " (" + n + ")</button>";
    }).join("") + "</div>";
  },

  _renderCategory() {
    const items = this._docs.filter((d) => d.category === this._cat);
    const rows = items.length ? items.map((d) =>
      "<tr><td>" + esc(d.original_name) + "</td><td>" + fieldDisplay(d.description) + "</td><td>" +
      esc((d.uploaded_at || "").slice(0, 10)) + "</td><td>" + fmtSize(d.size) +
      '</td><td class="rowact"><a href="' + this._base + this._id + "/documents/" + esc(d.item_id) +
      '/download">Download</a>' +
      (this._retired ? "" : '<span class="edit-btn" data-rmdoc="' + esc(d.item_id) + '">Delete</span>') +
      "</td></tr>").join("") : '<tr><td colspan="5" class="empty">No documents.</td></tr>';
    const upload = this._retired ? "" :
      '<div class="row" style="align-items:center;margin-bottom:10px"><input type="file" id="doc-file">' +
      '<input id="doc-desc" placeholder="Description (optional)" style="flex:1">' +
      '<button class="btn small primary" id="doc-upload">Upload</button></div>';
    document.getElementById("docs-cat").innerHTML = upload +
      "<table><thead><tr><th>Name</th><th>Description</th><th>Date</th><th>Size</th><th>Actions</th></tr></thead><tbody>" +
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
