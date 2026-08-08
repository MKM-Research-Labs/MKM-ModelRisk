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

// Governance-wide Documents tab: external reference material, tagged with the
// Admin-defined model types (see MRC settings > "Document model types") and
// filterable by them. Model types replace the old free-text Description column.
function parseModelTypes(str) {
  return (str || "").split(",").map((s) => s.trim()).filter(Boolean);
}

// Two panels, because the tab holds two different kinds of thing. Bibliography is the
// external reference material this governance framework is built on — papers, standards,
// regulatory texts — which is everything filed here to date. Artefacts is for what the
// institution itself produces; what belongs there is still being decided, so it is an
// empty panel rather than a guess at a schema.
const GOV_DOC_PANELS = [
  { key: "bibliography", label: "Bibliography" },
  { key: "artefacts", label: "Artefacts" },
];

const GovDocs = {
  _docs: [],
  _types: [],
  _filter: "",
  _panel: "bibliography",

  async render() {
    const [docs, settings] = await Promise.all([
      App.get("/api/documents"),
      App.get("/api/mrc/settings"),
    ]);
    this._docs = docs;
    this._types = parseModelTypes(settings.fields.document_model_types);
    this._filter = "";
    document.getElementById("tab-documents").innerHTML = this._shell();
    if (this._panel === "bibliography") {
      this._renderRows();
      this._bindShell();
    }
    this._bindPanels();
  },

  _chip(label, on, attrs) {
    const style = on
      ? "background:#1565C0;color:#fff;border:1px solid #1565C0"
      : "background:#fff;color:#1565C0;border:1px solid #1565C0";
    return '<span class="mtype-chip" ' + (attrs || "") +
      ' style="display:inline-block;padding:1px 8px;margin:1px 3px 1px 0;border-radius:10px;' +
      "font-size:12px;" + style + '">' + esc(label) + "</span>";
  },

  // Static chips shown in a row's Model Type cell.
  _chipsStatic(types) {
    if (!types || !types.length) return '<span class="muted">—</span>';
    return types.map((t) => this._chip(t, true)).join("");
  },

  // Toggleable chips for the upload row / an inline editor.
  _chipsPicker(selected, prefix) {
    if (!this._types.length) {
      return '<span class="muted">No model types defined — add them in Admin &rsaquo; MRC settings.</span>';
    }
    const sel = new Set(selected || []);
    return this._types.map((t) =>
      this._chip(t, sel.has(t),
        'data-pick="' + prefix + '" data-type="' + esc(t) + '" data-on="' + (sel.has(t) ? "1" : "0") + '"')
    ).join("");
  },

  _panelTabs() {
    return '<div class="dtabs">' + GOV_DOC_PANELS.map((p) =>
      '<button class="dtab' + (this._panel === p.key ? " active" : "") +
      '" data-gdpanel="' + p.key + '">' + esc(p.label) +
      (p.key === "bibliography" ? " (" + this._docs.length + ")" : "") +
      "</button>").join("") + "</div>";
  },

  _bindPanels() {
    document.querySelectorAll("[data-gdpanel]").forEach((btn) => {
      btn.onclick = () => { this._panel = btn.getAttribute("data-gdpanel"); this.render(); };
    });
  },

  _shell() {
    if (this._panel === "artefacts") {
      return '<div class="card"><h3>Documents</h3>' + this._panelTabs() +
        '<div class="empty" style="margin-top:12px">Artefacts are not defined yet. ' +
        "Nothing is filed here — the reference material is under Bibliography.</div></div>";
    }
    const opts = ['<option value="">All model types</option>']
      .concat(this._types.map((t) => '<option value="' + esc(t) + '">' + esc(t) + "</option>"))
      .join("");
    return '<div class="card"><h3>Documents</h3>' + this._panelTabs() +
      '<p class="muted" style="margin-top:10px">The external reference material this ' +
      "framework is built on, tagged by model type. Manage the type list in " +
      "Admin &rsaquo; MRC settings.</p>" +
      // Upload row
      '<div class="row" style="align-items:center;margin-bottom:6px"><input type="file" id="gd-file">' +
      '<button class="btn small primary" id="gd-upload">Upload</button></div>' +
      '<div id="gd-uptypes" style="margin-bottom:12px">' +
      '<span class="muted" style="margin-right:6px">Model types:</span>' +
      this._chipsPicker([], "up") + "</div>" +
      // Filter
      '<div class="row" style="align-items:center;margin-bottom:8px">' +
      '<label class="muted" style="margin-right:6px">Filter:</label>' +
      '<select id="gd-filter">' + opts + "</select></div>" +
      "<table><thead><tr><th>Name</th><th>Model Type</th><th>Date Added</th><th>Size</th>" +
      "<th>Actions</th></tr></thead><tbody id=\"gd-rows\"></tbody></table></div>";
  },

  _visibleDocs() {
    if (!this._filter) return this._docs;
    return this._docs.filter((d) => (d.model_types || []).indexOf(this._filter) !== -1);
  },

  _renderRows() {
    const docs = this._visibleDocs();
    const rows = docs.length ? docs.map((d) =>
      "<tr><td>" + esc(d.original_name) + '</td><td class="mt-cell" data-mt="' + esc(d.item_id) + '">' +
      this._chipsStatic(d.model_types) +
      ' <span class="edit-btn" data-edt="' + esc(d.item_id) + '">edit</span></td><td>' +
      esc((d.uploaded_at || "").slice(0, 10)) + "</td><td>" + fmtSize(d.size) +
      '</td><td class="rowact"><a href="/api/documents/' + esc(d.item_id) + '/download">Download</a>' +
      ' <button class="btn small danger" data-rmgd="' + esc(d.item_id) + '">Delete</button></td></tr>').join("") :
      '<tr><td colspan="5" class="empty">No documents' +
      (this._filter ? " for this model type." : " uploaded yet.") + "</td></tr>";
    document.getElementById("gd-rows").innerHTML = rows;
    this._bindRows();
  },

  _bindShell() {
    const self = this;
    document.getElementById("gd-upload").onclick = function () { self._upload(); };
    document.getElementById("gd-filter").onchange = function () {
      self._filter = this.value;
      self._renderRows();
    };
    this._bindPicker("up");
  },

  // Toggle behaviour for a picker group (upload row or an inline editor).
  _bindPicker(prefix) {
    document.querySelectorAll('[data-pick="' + prefix + '"]').forEach(function (el) {
      el.style.cursor = "pointer";
      el.onclick = function () {
        const on = el.getAttribute("data-on") === "1";
        el.setAttribute("data-on", on ? "0" : "1");
        el.style.background = on ? "#fff" : "#1565C0";
        el.style.color = on ? "#1565C0" : "#fff";
      };
    });
  },

  _picked(prefix) {
    return Array.from(document.querySelectorAll('[data-pick="' + prefix + '"]'))
      .filter((el) => el.getAttribute("data-on") === "1")
      .map((el) => el.getAttribute("data-type"));
  },

  _bindRows() {
    const self = this;
    document.querySelectorAll("[data-rmgd]").forEach(function (el) {
      const iid = el.getAttribute("data-rmgd");
      el.onclick = function () {
        App.amend("Delete document " + iid + "?", "POST", "/api/documents/" + iid + "/delete",
          {}, () => self.render());
      };
    });
    document.querySelectorAll("[data-edt]").forEach(function (el) {
      el.onclick = function () { self._editTypes(el.getAttribute("data-edt")); };
    });
  },

  _editTypes(itemId) {
    const self = this;
    const doc = this._docs.find((d) => d.item_id === itemId);
    const cell = document.querySelector('.mt-cell[data-mt="' + itemId + '"]');
    cell.innerHTML = '<div data-editor="1">' + this._chipsPicker(doc.model_types || [], "ed") +
      '<div style="margin-top:4px"><button class="btn small primary" id="mt-save">Save…</button>' +
      ' <button class="btn small" id="mt-cancel">Cancel</button></div></div>';
    this._bindPicker("ed");
    document.getElementById("mt-cancel").onclick = function () { self._renderRows(); };
    document.getElementById("mt-save").onclick = function () {
      const chosen = self._picked("ed");
      App.amend("Set model types for " + itemId + ".", "POST",
        "/api/documents/" + itemId + "/model-types", { model_types: chosen },
        () => self.render());
    };
  },

  _upload() {
    const fileInput = document.getElementById("gd-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    this._picked("up").forEach((t) => form.append("model_types", t));
    fetch("/api/documents", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json(); throw new Error(e.error || "upload failed"); }
      App.toast("Document uploaded", "ok");
      this.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
