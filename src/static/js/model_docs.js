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

// Model Docs tab: per-category (Core Documentation / Test Results / Analysis /
// Monitoring) uploadable document lists with download and delete.
const ModelDocs = {
  _id: null, _docs: [], _categories: [], _retired: false, _cat: null,
  _base: "/api/models/", _refresh: null, _host: "dt-content",

  // base / refresh / host let the same renderer serve any aggregate (models, Products).
  render(modelId, docs, categories, retired, base, refresh, host, groups) {
    this._id = modelId;
    this._groups = groups || this._groups || {};
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
          self._base, self._refresh, self._host, self._groups);
      };
    });
    this._renderCategory();
  },

  // The real categories behind a tab: itself, unless it is a group (Testing is a
  // panel over several categories; Benchmark and Review over one each). Nothing is
  // ever filed under a group's label.
  _members(cat) {
    return (this._groups && this._groups[cat]) || [cat];
  },

  // A grouped panel: one section per member category, each with its own upload
  // panel, so a document is filed under the test it evidences rather than into one
  // undifferentiated heap.
  _renderGroup(members) {
    const opts = (cat) => ({ category: cat, docs: this._docs, base: this._base,
      id: this._id, retired: this._retired, refresh: this._refresh });
    document.getElementById("docs-cat").innerHTML = members.map((cat) =>
      '<div class="section-header" style="margin-top:var(--space-6)">' + esc(cat) + "</div>" +
      DocPanel.html(opts(cat))).join("");
    members.forEach((cat) => DocPanel.bind(opts(cat)));
  },

  _subtabs() {
    return '<div class="dtabs">' + this._categories.map((c) => {
      const n = this._members(c)
        .reduce((sum, m) => sum + DocLinks.visible(this._docs, m).length, 0);
      return '<button class="dtab' + (c === this._cat ? " active" : "") + '" data-doctab="' +
        esc(c) + '">' + esc(c) + " (" + n + ")</button>";
    }).join("") + "</div>";
  },

  _renderCategory() {
    const members = this._members(this._cat);
    if (members.length > 1) { this._renderGroup(members); return; }
    // A one-member group lists, and files into, its member — never its label.
    const items = DocLinks.visible(this._docs, members[0]);
    const rows = items.length ? items.map((d) =>
      "<tr><td>" + esc(DocLinks.name(d)) + "</td><td>" + fieldDisplay(d.description) + "</td><td>" +
      esc(fmtTimestamp(d.uploaded_at)) + "</td><td>" + (DocLinks.isLink(d) ? "Link" : fmtSize(d.size)) +
      '</td><td class="rowact">' + DocLinks.actions(this._base, this._id, d) +
      (this._retired ? "" : ' <button class="btn small danger" data-rmdoc="' + esc(d.item_id) + '">Delete</button>') +
      "</td></tr>").join("") : '<tr><td colspan="5" class="empty">No documents.</td></tr>';
    const upload = this._retired ? "" :
      '<div class="row" style="align-items:center;margin-bottom:var(--space-5)">' +
      DocUpload.html("doc", false) + "</div>";
    document.getElementById("docs-cat").innerHTML = upload +
      "<table><thead><tr><th>Name</th><th>Description</th><th>Uploaded</th><th>Size</th><th>Actions</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
    this._bind();
  },

  _bind() {
    const self = this;
    DocUpload.bind("doc", function () {
      DocUpload.submit("doc", self._base + self._id + "/documents",
        self._members(self._cat)[0], self._refresh);
    });
    document.querySelectorAll("[data-rmdoc]").forEach(function (el) {
      const iid = el.getAttribute("data-rmdoc");
      el.onclick = function () {
        App.amend("Delete document " + iid + "?", "POST",
          self._base + self._id + "/documents/" + iid + "/delete", {}, self._refresh);
      };
    });
  },
};
