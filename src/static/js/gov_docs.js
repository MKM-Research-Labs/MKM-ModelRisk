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
  _artefacts: {},        // shelf -> [artefact]
  _shelves: [],          // Company-wide, then one per division
  _kinds: [],
  _shelf: null,          // the open shelf

  async render() {
    const [docs, settings] = await Promise.all([
      App.get("/api/documents"),
      App.get("/api/mrc/settings"),
    ]);
    this._docs = docs;
    const art = await App.get("/api/artefacts");
    this._artefacts = art.artefacts || {};
    this._shelves = art.shelves || [];
    this._kinds = art.kinds || [];
    if (!this._shelf || this._shelves.indexOf(this._shelf) < 0) this._shelf = this._shelves[0];
    this._types = parseModelTypes(settings.fields.document_model_types);
    this._filter = "";
    document.getElementById("tab-documents").innerHTML = this._shell();
    if (this._panel === "bibliography") {
      this._renderRows();
      this._bindShell();
    } else {
      this._bindArtefacts();
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
    if (this._panel === "artefacts") return this._artefactsShell();
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

  // What the institution issues, filed per division. The shelves are sub-tabs because a
  // division's terms of reference are not another's, and Company-wide holds what belongs
  // to the institution rather than to one division.
  _artefactsShell() {
    const shelfTabs = '<div class="dtabs" style="margin-top:10px">' + this._shelves.map((sh) =>
      '<button class="dtab' + (sh === this._shelf ? " active" : "") + '" data-gdshelf="' +
      esc(sh) + '">' + esc(sh) + " (" + ((this._artefacts[sh] || []).length) + ")</button>")
      .join("") + "</div>";
    const kindOpts = this._kinds.map((k) => "<option>" + esc(k) + "</option>").join("");
    return '<div class="card"><h3>Documents</h3>' + this._panelTabs() +
      '<p class="muted" style="margin-top:10px">What this institution issues &mdash; terms ' +
      "of reference, committee presentations, policies and guides. Filed per division; " +
      "Company-wide holds what belongs to the institution as a whole.</p>" + shelfTabs +
      '<div class="tiles" id="gd-tiles">' + this._tiles() + "</div>" +
      '<div class="row" style="align-items:center;margin-top:14px">' +
      '<input type="file" id="ga-file">' +
      '<select id="ga-kind">' + kindOpts + "</select>" +
      '<input id="ga-desc" placeholder="Description (optional)" style="flex:1">' +
      '<button class="btn small primary" id="ga-upload">Upload</button></div></div>';
  },

  // One tile per artefact, plus the two the platform maintains itself.
  _tiles() {
    const own = (this._artefacts[this._shelf] || []).map((a) => this._tile({
      title: a.original_name, kind: a.category || "Other", note: a.description,
      links: [["Open", "/api/artefacts/" + encodeURIComponent(this._shelf) + "/" +
               esc(a.item_id) + "/download?inline=1"],
              ["Download", "/api/artefacts/" + encodeURIComponent(this._shelf) + "/" +
               esc(a.item_id) + "/download"]],
      remove: a.item_id,
    })).join("");
    return this._platformTiles() + own ||
      '<div class="empty">Nothing filed on this shelf yet.</div>';
  },

  // Artefacts the platform produces rather than an adopter uploading them: the user
  // guide (company-wide) and each division's risk policy document, which used to be
  // reachable only from Admin.
  _platformTiles() {
    if (this._shelf === (this._shelves[0] || "")) {
      return this._tile({
        title: "User Guide", kind: "Guide",
        note: "Generated from the platform's own documentation. Published in both forms " +
              "so it can be read as issued or marked up by your own people.",
        links: [["PDF", "/api/audit-reports/user_guide.pdf"],
                ["Word", "/api/audit-reports/user_guide.docx"]],
      });
    }
    return this._tile({
      title: this._shelf + " Risk Policy",
      kind: "Policy",
      note: "The division's formal written risk policy, sent to its MRC alongside the " +
            "categorisation. Uploaded here; the categorisation itself stays in Admin.",
      links: [["Open", "/api/risk-policy/" + encodeURIComponent(this._shelf) + "/document"]],
      upload: "policy",
    });
  },

  _tile(t) {
    const links = t.links.map(([label, href]) =>
      '<a class="btn small" href="' + href + '" target="_blank" rel="noopener">' +
      esc(label) + "</a>").join(" ");
    const remove = t.remove
      ? ' <button class="btn small danger" data-ga-rm="' + esc(t.remove) + '">Remove</button>'
      : "";
    // The policy document belongs to the risk-policy record, not to this shelf, so its
    // tile replaces it in place rather than filing a second copy here.
    const upload = t.upload === "policy"
      ? '<div class="row" style="margin-top:6px;gap:6px"><input type="file" id="gp-file" ' +
        'accept=".pdf,.doc,.docx" style="max-width:150px">' +
        '<button class="btn small" id="gp-upload">Replace</button></div>'
      : "";
    return '<div class="tile"><div class="tile-kind">' + esc(t.kind) + "</div>" +
      '<div class="tile-title">' + esc(t.title) + "</div>" +
      (t.note ? '<div class="tile-note">' + esc(t.note) + "</div>" : "") +
      '<div class="tile-actions">' + links + remove + "</div>" + upload + "</div>";
  },

  _bindArtefacts() {
    document.querySelectorAll("[data-gdshelf]").forEach((btn) => {
      btn.onclick = () => { this._shelf = btn.getAttribute("data-gdshelf"); this.render(); };
    });
    const up = document.getElementById("ga-upload");
    if (up) up.onclick = () => this._uploadArtefact();
    const pol = document.getElementById("gp-upload");
    if (pol) pol.onclick = () => this._uploadPolicy();
    document.querySelectorAll("[data-ga-rm]").forEach((btn) => {
      const id = btn.getAttribute("data-ga-rm");
      btn.onclick = () => App.amend("Remove artefact " + id + " from " + this._shelf + ".",
        "POST", "/api/artefacts/" + encodeURIComponent(this._shelf) + "/" + id + "/delete",
        {}, () => this.render());
    });
  },

  _uploadArtefact() {
    const file = document.getElementById("ga-file");
    if (!file.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", file.files[0]);
    form.append("kind", document.getElementById("ga-kind").value);
    form.append("description", document.getElementById("ga-desc").value);
    fetch("/api/artefacts/" + encodeURIComponent(this._shelf), {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Artefact filed", "ok");
      this.render();
    }).catch((e) => App.toast(e.message, "error"));
  },

  // Replace the division's written risk policy. Posts to the risk-policy record that
  // owns it, so the committee still receives it alongside the categorisation.
  _uploadPolicy() {
    const file = document.getElementById("gp-file");
    if (!file.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", file.files[0]);
    fetch("/api/risk-policy/" + encodeURIComponent(this._shelf) + "/document", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Risk policy document uploaded", "ok");
      this.render();
    }).catch((e) => App.toast(e.message, "error"));
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
