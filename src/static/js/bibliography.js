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

// Bibliography tab: references with a category filter, add/edit/delete and a
// BibTeX export.
const Bibliography = {
  _refs: [], _spec: null, _cat: "All", _editingId: null,

  async render() {
    const data = await App.get("/api/bibliography");
    this._refs = data.references;
    this._spec = data.spec;
    const cats = ["All"].concat(
      this._refs.map((r) => r.category).filter((c, i, a) => c && a.indexOf(c) === i));
    if (cats.indexOf(this._cat) < 0) this._cat = "All";
    document.getElementById("tab-bibliography").innerHTML =
      '<div class="card"><h3>Bibliography</h3>' +
      '<div class="row" style="margin-bottom:10px;align-items:center"><div class="field"><label>Category</label>' +
      '<select id="bib-cat">' + cats.map((c) =>
        "<option" + (c === this._cat ? " selected" : "") + ">" + esc(c) + "</option>").join("") +
      "</select></div><span style=\"flex:1\"></span>" +
      '<a class="btn small" href="/api/bibliography/export.bib">Export BibTeX</a></div>' +
      '<div id="bib-add"></div>' +
      "<table><thead><tr><th>Author(s)</th><th>Year</th><th>Title</th><th>Journal / Publisher</th>" +
      "<th>Category</th><th>Notes</th><th></th></tr></thead><tbody id=\"bib-rows\"></tbody></table></div>";
    document.getElementById("bib-cat").onchange = (e) => { this._cat = e.target.value; this._renderRows(); };
    this._renderForm();
    this._renderRows();
  },

  _renderForm() {
    const editing = this._editingId
      ? (this._refs.find((r) => r.item_id === this._editingId) || {}) : {};
    const inputs = this._spec.fields.map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("bib-" + f.key, f) + "</div>").join("");
    const label = this._editingId ? "Save changes" : "+ Add Reference";
    document.getElementById("bib-add").innerHTML =
      '<div class="row" style="margin-bottom:10px">' + inputs +
      '<button class="btn small primary" id="bib-save">' + label + "</button>" +
      (this._editingId ? '<button class="btn small" id="bib-cancel">Cancel</button>' : "") + "</div>";
    this._spec.fields.forEach((f) => {
      const el = document.getElementById("bib-" + f.key);
      if (editing[f.key] != null) el.value = editing[f.key];
    });
    document.getElementById("bib-save").onclick = () => this._save();
    const cancel = document.getElementById("bib-cancel");
    if (cancel) cancel.onclick = () => { this._editingId = null; this.render(); };
  },

  _save() {
    const fields = {};
    this._spec.fields.forEach((f) => { const v = val("bib-" + f.key); if (v !== "") fields[f.key] = v; });
    const path = this._editingId ? "/api/bibliography/references/" + this._editingId
      : "/api/bibliography/references";
    const id = this._editingId;
    this._editingId = null;
    App.amend(id ? "Update reference " + id + "." : "Add reference.", "POST", path,
      { fields: fields }, () => this.render());
  },

  _renderRows() {
    const items = this._cat === "All" ? this._refs : this._refs.filter((r) => r.category === this._cat);
    const rows = items.length ? items.map((r) =>
      "<tr><td>" + fieldDisplay(r.authors) + "</td><td>" + fieldDisplay(r.year) + "</td><td>" +
      (r.url ? '<a href="' + esc(r.url) + '" target="_blank">' + fieldDisplay(r.title) + "</a>"
        : fieldDisplay(r.title)) + "</td><td>" + fieldDisplay(r.journal) + "</td><td>" +
      (r.category ? '<span class="badge" style="background:#1976d2">' + esc(r.category) + "</span>" : "—") +
      '</td><td class="muted" style="font-size:12px">' + fieldDisplay(r.notes) + "</td>" +
      '<td class="rowact"><button class="btn small" data-bibed="' + esc(r.item_id) + '">Edit</button>' +
      ' <button class="btn small danger" data-bibrm="' + esc(r.item_id) + '">Remove</button></td></tr>').join("") :
      '<tr><td colspan="7" class="empty">No references.</td></tr>';
    document.getElementById("bib-rows").innerHTML = rows;
    const self = this;
    document.querySelectorAll("[data-bibrm]").forEach(function (el) {
      const iid = el.getAttribute("data-bibrm");
      el.onclick = function () {
        App.amend("Delete reference " + iid + "?", "POST",
          "/api/bibliography/references/" + iid + "/delete", {}, () => self.render());
      };
    });
    document.querySelectorAll("[data-bibed]").forEach(function (el) {
      el.onclick = function () { self._editingId = el.getAttribute("data-bibed"); self._renderForm(); };
    });
  },
};
