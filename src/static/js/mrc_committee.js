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

// The MRC committees list on the Admin > MRC tab. Unlike the other reference
// lists (a plain inline-edit table), each committee is an entity: the list rows
// are clickable and open a Model-style detail with inline field edits and the
// committee's own Terms of Reference upload/download.
const Committees = {
  _spec: null,
  _items: [],
  _openId: null,        // survives a re-render so the open detail re-opens

  _visible() {
    return this._spec.fields.filter((f) => !f.hidden);
  },

  render(container, spec, items) {
    this._spec = spec;
    this._items = items;
    const cols = this._visible();
    const head = cols.map((f) => "<th>" + esc(f.label) + "</th>").join("");
    const body = items.length
      ? items.map((it) =>
          '<tr class="clickable" data-cid="' + esc(it.item_id) + '">' +
          cols.map((f) => "<td>" + fieldDisplay(it[f.key]) + "</td>").join("") + "</tr>").join("")
      : '<tr><td colspan="' + cols.length + '" class="empty">No committees yet.</td></tr>';
    const addInputs = cols.map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("cadd-" + f.key, f) + "</div>").join("");
    container.innerHTML =
      '<div class="section-header">MRC committees</div>' +
      '<p class="muted">Each committee is anchored to an org tier and carries its chair, cadence ' +
      "and Terms of Reference. Click a row to open its detail.</p>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" +
      '<div class="row" style="margin-top:8px">' + addInputs +
      '<button class="btn small" id="cadd">Add committee&hellip;</button></div>' +
      '<div id="committee-detail"></div>';
    container.querySelectorAll("tr.clickable").forEach((tr) => {
      tr.onclick = () => this._showDetail(tr.getAttribute("data-cid"));
    });
    document.getElementById("cadd").onclick = () => this._add();
    if (this._openId && items.some((i) => i.item_id === this._openId)) {
      this._showDetail(this._openId);
    } else {
      this._openId = null;
    }
  },

  _add() {
    const fields = {};
    this._visible().forEach((f) => {
      const v = val("cadd-" + f.key);
      if (v !== "") fields[f.key] = v;
    });
    App.amend("Add an MRC committee.", "POST", "/api/reference/collections/mrc",
      { fields: fields }, () => Reference.render());
  },

  _showDetail(itemId) {
    this._openId = itemId;
    const item = this._items.find((i) => i.item_id === itemId);
    if (!item) return;
    const rows = this._visible().map((f) =>
      '<div class="inforow" id="crow-' + f.key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + fieldDisplay(item[f.key]) +
      '</div><span class="edit-btn" data-ced="' + f.key + '">edit</span></div>').join("");
    const tor = item.tor_filename
      ? '<div class="row" style="align-items:center;margin-top:8px">' +
        '<a href="/api/reference/collections/mrc/' + esc(itemId) + '/tor" target="_blank">&darr; ' +
        esc(item.tor_original_name || "Terms of Reference") + "</a>" +
        '<button class="btn small" id="ctor-replace" style="margin-left:auto">Replace&hellip;</button></div>'
      : '<div class="muted" style="margin-top:8px">No Terms of Reference uploaded.</div>';
    document.getElementById("committee-detail").innerHTML =
      '<div class="card" style="margin-top:14px"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">' + esc(item.name || item.value) + "</h3>" +
      '<span class="muted" style="margin-left:8px">' + esc(item.value) + "</span>" +
      '<span style="flex:1"></span>' +
      '<button class="btn small" id="crm">Remove committee</button></div>' + rows +
      '<div class="section-header" style="margin-top:16px">Terms of Reference</div>' + tor +
      '<div class="row" style="margin-top:6px"><input type="file" id="ctor-file">' +
      '<button class="btn small primary" id="ctor-upload">Upload ToR</button></div></div>';
    this._bindDetail(item);
  },

  _bindDetail(item) {
    const self = this;
    const byKey = {};
    this._spec.fields.forEach((f) => { byKey[f.key] = f; });
    document.querySelectorAll("[data-ced]").forEach((btn) => {
      btn.onclick = () => self._editField(item, byKey[btn.getAttribute("data-ced")]);
    });
    document.getElementById("crm").onclick = () => {
      App.amend("Remove committee " + item.value + ".", "POST",
        "/api/reference/collections/mrc/" + item.item_id + "/delete", {}, () => {
          self._openId = null;
          Reference.render();
        });
    };
    document.getElementById("ctor-upload").onclick = () => self._uploadTor(item.item_id);
    const replace = document.getElementById("ctor-replace");
    if (replace) replace.onclick = () => document.getElementById("ctor-file").click();
  },

  _editField(item, f) {
    const row = document.getElementById("crow-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      inputControl("ced-input", f) + '<button class="btn small primary" id="ced-save">Save&hellip;</button>' +
      '<button class="btn small" id="ced-cancel">Cancel</button></div>';
    const input = document.getElementById("ced-input");
    if (item[f.key] !== null && item[f.key] !== undefined) input.value = item[f.key];
    document.getElementById("ced-cancel").onclick = () => this._showDetail(item.item_id);
    document.getElementById("ced-save").onclick = () => {
      const fields = {};
      fields[f.key] = input.value.trim();
      App.amend("Set " + f.label + ' on ' + item.value + ".", "POST",
        "/api/reference/collections/mrc/" + item.item_id, { fields: fields },
        () => Reference.render());
    };
  },

  _uploadTor(itemId) {
    const fileInput = document.getElementById("ctor-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    fetch("/api/reference/collections/mrc/" + itemId + "/tor", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Terms of Reference uploaded", "ok");
      Reference.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
