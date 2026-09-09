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

// Artefacts panel of the Documents tab: what the institution ISSUES, filed per
// division, plus a company-wide shelf and the FINOS shelf.
//
// Extracted from gov_docs.js when the FINOS shelf arrived. That file was already past
// the 300-line mark rule R2 held web files to — reported then, gated since
// 2026-09-05 — and the panel is a
// self-contained screen with its own state — the same split gov_vendor_docs.js
// already makes, and the same load()/shell()/bind() interface.
//
// The FINOS shelf is the one that is not like the others. Its documents are the
// institution's description of how it implements the FINOS mitigations, and the
// completeness audit reads them: a document tagged AIR-PREV-017 is what turns that
// row of the coverage table from Not evidenced into a citation. So this shelf, and
// only this shelf, offers the reference picker.
const GovArtefacts = {
  _artefacts: {},        // shelf -> [artefact]
  _shelves: [],          // Company-wide, then one per division, then FINOS
  _kinds: [],
  _finosShelf: "",
  _finosRefs: [],        // [{ref, title}] — the mitigation catalogue
  _shelf: null,          // the open shelf
  _picked: [],           // references ticked for the pending upload

  async load() {
    const art = await App.get("/api/artefacts");
    this._artefacts = art.artefacts || {};
    this._shelves = art.shelves || [];
    this._kinds = art.kinds || [];
    this._finosShelf = art.finos_shelf || "";
    this._finosRefs = art.finos_refs || [];
    if (!this._shelf || this._shelves.indexOf(this._shelf) < 0) this._shelf = this._shelves[0];
  },

  _isFinos() {
    return this._shelf === this._finosShelf && !!this._finosShelf;
  },

  shell(panelTabs) {
    const shelfTabs = '<div class="dtabs" style="margin-top:var(--space-5)">' + this._shelves.map((sh) =>
      '<button class="dtab' + (sh === this._shelf ? " active" : "") + '" data-gdshelf="' +
      esc(sh) + '">' + esc(sh) + " (" + ((this._artefacts[sh] || []).length) + ")</button>")
      .join("") + "</div>";
    const kindOpts = this._kinds.map((k) => "<option>" + esc(k) + "</option>").join("");
    return '<div class="card"><h3>Documents</h3>' + panelTabs +
      '<p class="muted" style="margin-top:var(--space-5)">' + this._blurb() + "</p>" + shelfTabs +
      '<div class="tiles" id="gd-tiles">' + this._tiles() + "</div>" +
      this._refPicker() +
      '<div class="row" style="align-items:center;margin-top:var(--space-7)">' +
      '<input type="file" id="ga-file">' +
      '<select id="ga-kind">' + kindOpts + "</select>" +
      '<input id="ga-desc" placeholder="Description (optional)" style="flex:1">' +
      '<button class="btn small primary" id="ga-upload">Upload</button></div></div>';
  },

  _blurb() {
    if (this._isFinos()) {
      return "How this institution implements the FINOS AI Governance Framework's " +
             "mitigations. Tag a document with every mitigation it describes &mdash; one " +
             "paper may cover many &mdash; and the completeness audit cites it against " +
             "each of them. Untagged documents are filed but evidence nothing.";
    }
    return "What this institution issues &mdash; terms of reference, committee " +
           "presentations, policies and guides. Filed per division; Company-wide holds " +
           "what belongs to the institution as a whole.";
  },

  // Ticked before choosing the file, so the reference list is read as part of
  // describing the document rather than as an afterthought to uploading it.
  _refPicker() {
    if (!this._isFinos()) return "";
    const boxes = this._finosRefs.map((r) => {
      const on = this._picked.indexOf(r.ref) !== -1;
      return '<label class="chip' + (on ? " on" : "") + '" title="' + esc(r.title) + '">' +
        '<input type="checkbox" data-ga-ref="' + esc(r.ref) + '"' + (on ? " checked" : "") +
        "> " + esc(r.ref) + "</label>";
    }).join(" ");
    return '<div style="margin-top:var(--space-7)"><div class="muted">Mitigations this ' +
      "document describes</div>" +
      '<div class="row" style="flex-wrap:wrap;gap:var(--space-2);margin-top:var(--space-3)">' +
      boxes + "</div></div>";
  },

  bind(rerender) {
    this._rerender = rerender;
    document.querySelectorAll("[data-gdshelf]").forEach((btn) => {
      btn.onclick = () => {
        this._shelf = btn.getAttribute("data-gdshelf");
        this._picked = [];      // references belong to the shelf they were ticked on
        rerender();
      };
    });
    document.querySelectorAll("[data-ga-ref]").forEach((box) => {
      box.onchange = () => {
        const ref = box.getAttribute("data-ga-ref");
        const at = this._picked.indexOf(ref);
        if (box.checked && at === -1) this._picked.push(ref);
        if (!box.checked && at !== -1) this._picked.splice(at, 1);
        rerender();
      };
    });
    const up = document.getElementById("ga-upload");
    if (up) up.onclick = () => this._upload();
    const pol = document.getElementById("gp-upload");
    if (pol) pol.onclick = () => this._uploadPolicy();
    document.querySelectorAll("[data-ga-rm]").forEach((btn) => {
      const id = btn.getAttribute("data-ga-rm");
      btn.onclick = () => App.amend("Remove artefact " + id + " from " + this._shelf + ".",
        "POST", "/api/artefacts/" + encodeURIComponent(this._shelf) + "/" + id + "/delete",
        {}, () => rerender());
    });
  },

  _upload() {
    const file = document.getElementById("ga-file");
    if (!file.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", file.files[0]);
    form.append("kind", document.getElementById("ga-kind").value);
    form.append("description", document.getElementById("ga-desc").value);
    this._picked.forEach((ref) => form.append("finos_refs", ref));
    fetch("/api/artefacts/" + encodeURIComponent(this._shelf), {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Artefact filed", "ok");
      this._picked = [];
      this._rerender();
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
      this._rerender();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
