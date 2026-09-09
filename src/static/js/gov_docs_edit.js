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

// One filed document: the actions on its row, the editor that amends what it says, and
// the upload that adds another.
//
// Split from gov_docs.js, which is the tab around them — the three panels, the
// model-type filter, and the Bibliography table the rows sit in.
//
// The editor takes the model types and the free-text description together, in one pass,
// because they answer different questions and a document needs both: the types are what
// it is filtered BY, and no tag list says what a paper is actually about. Offering them
// separately invites filing one and not the other.
//
// Assigns onto GovDocs; loads after gov_docs.js.

Object.assign(GovDocs, {

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
      el.onclick = function () { self._editMeta(el.getAttribute("data-edt")); };
    });
  },

  // A row's description cell: the text, or a dash when there is none.
  _descStatic(description) {
    return description ? esc(description) : '<span class="muted">—</span>';
  },

  // One editor over both metadata fields, opened by the single "edit" control and
  // saved in one amendment — two separate editors would mean two audit entries for
  // what a user did as one correction.
  _editMeta(itemId) {
    const self = this;
    const doc = this._docs.find((d) => d.item_id === itemId);
    const desc = document.querySelector('.ds-cell[data-ds="' + itemId + '"]');
    desc.innerHTML = '<input id="mt-desc" style="width:100%" placeholder="Description" ' +
      'value="' + esc(doc.description || "") + '">';
    const cell = document.querySelector('.mt-cell[data-mt="' + itemId + '"]');
    cell.innerHTML = '<div data-editor="1">' + this._chipsPicker(doc.model_types || [], "ed") +
      '<div style="margin-top:var(--space-2)"><button class="btn small primary" id="mt-save">Save…</button>' +
      ' <button class="btn small" id="mt-cancel">Cancel</button></div></div>';
    this._bindPicker("ed");
    document.getElementById("mt-cancel").onclick = function () { self._renderRows(); };
    document.getElementById("mt-save").onclick = function () {
      App.amend("Set description and model types for " + itemId + ".", "POST",
        "/api/documents/" + itemId + "/metadata",
        { model_types: self._picked("ed"), description: val("mt-desc") },
        () => self.render());
    };
  },

  _upload() {
    const fileInput = document.getElementById("gd-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    form.append("description", val("gd-desc"));
    this._picked("up").forEach((t) => form.append("model_types", t));
    fetch("/api/documents", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json(); throw new Error(e.error || "upload failed"); }
      App.toast("Document uploaded", "ok");
      this.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
});
