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
// Detail — the header card: what the model is called, what it is critical for, who
// owns it, and the one edit that changes any of that.
//
// The name and the identifier read as one thing to whoever is looking at the screen,
// so they are edited from one button — but only the name can actually move.
// ``model_id`` is the aggregate id: it is hashed into every event on the stream
// (src/database/_hash.py), and it is the reference that products, meetings, dependency
// edges and the document store each hold. Changing it would not be an edit, it would
// be a re-keying of the record and a break in its audit chain. So the editor shows it
// alongside the name and says why it stays, rather than leaving a reader to conclude
// the screen forgot about it.
Object.assign(Detail, {
  _header(d) {
    const dates = HEADER_DATES.map((k) => {
      // MRC sign-off shows the granting meeting id (not the date) once approved.
      const value = (k === "mrc_signoff_date" && d.mrc_signoff_meeting)
        ? esc(d.mrc_signoff_meeting) : fieldDisplay(d[k]);
      return '<span class="datechip"><span class="muted">' + esc(this.specByKey(k).label) +
        ":</span> <b>" + value + "</b></span>";
    }).join("");
    return '<div class="detail-header"><div>' + this._identity(d) +
      // The RAG rating is the governed
      // one, and a second, differently-derived verdict in the header invited the
      // question "where does that come from?" without answering it.
      '<div style="margin-top:var(--space-4)">' + tierBadge(d.tier, d.division) + ' <span class="muted">' +
      esc(tierFullLabel(d.tier, d.division)) + "</span></div>" +
      '<div class="dh-dates">' + dates + "</div></div>" +
      '<div class="right"><div class="olabel">OWNER</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div>" +
      '<div style="margin-top:var(--space-3)">' + ragBadge(d.rag_rating, d.division) + "</div></div></div>";
  },

  // Name over identifier, with the edit affordance on the name. Its own element so the
  // editor below can open in place of the pair.
  _identity(d) {
    const edit = this._model.retired
      ? "" : ' <span class="edit-btn" data-edit-name="1">edit</span>';
    return '<div id="dh-identity"><div class="name">' + esc(d.name || this._id) + edit +
      '</div><div class="sub">' + this._sub(d) + "</div></div>";
  },

  _sub(d) {
    return esc(this._id) + (d.version ? " · v" + esc(d.version) : "") +
      (d.category ? " · " + esc(d.category) : "");
  },

  _bindHeader() {
    const btn = document.querySelector("#dh-identity [data-edit-name]");
    if (btn) btn.onclick = () => this._editName(this._model.data || {});
  },

  // Opens in place of the name / identifier pair: a field for the name, and the
  // identifier shown read-only beneath it with the reason it is read-only. Deliberately
  // not DetailShell.fieldEditor — that draws an inforow inside the tab content, and this
  // is a title.
  _editName(d) {
    const host = document.getElementById("dh-identity");
    if (!host) return;
    const current = d.name || "";
    host.innerHTML = '<div class="editor">' +
      '<input id="dh-name-input" type="text" aria-label="Name">' +
      '<button class="btn small primary" id="dh-name-save">Save&hellip;</button>' +
      '<button class="btn small" id="dh-name-cancel">Cancel</button></div>' +
      '<div class="sub dh-idnote"><span class="code">' + esc(this._id) + "</span> &mdash; the " +
      "permanent identifier. Every event in the audit trail is signed with it, and the " +
      "products, meetings, feeds and documents that point at this model point at this " +
      "string, so it cannot be changed.</div>";
    const input = document.getElementById("dh-name-input");
    input.value = current;
    input.focus();
    input.select();
    document.getElementById("dh-name-cancel").onclick = () => this._render();
    document.getElementById("dh-name-save").onclick = () => {
      const value = input.value.trim();
      // A blank name is accepted by the field command but leaves the register showing
      // the id in the name column, which reads as a broken record rather than an
      // unnamed one. Refuse it here instead.
      if (!value) { App.toast("A model needs a name.", "error"); return; }
      if (value === current) { this._render(); return; }
      App.amend('Rename ' + this._id + ' to "' + value + '".', "POST",
        "/api/models/" + this._id + "/field", { field: "name", value: value },
        () => { this.show(this._id, this._tab, { scroll: false }); Inventory.loadList(); });
    };
  },
});
