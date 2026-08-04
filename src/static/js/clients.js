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

// The Clients top-level tab. A Client is an external company we hand a governance
// evidence pack to: it carries its own contact org tree (Divisions -> Departments
// -> Contacts) and the Products / Models it is linked to. This core module owns
// the client list + add form; the per-client detail (org tree, links, pack) lives
// in clients_detail.js, loaded after and augmenting this object.
const Clients = {
  _specs: null,
  _items: [],
  _openId: null,   // survives a re-render so the open detail re-opens

  async specs() {
    // Re-fetch each render so admin edits to the People list (relationship owner)
    // surface promptly, exactly like the model/product field endpoints.
    this._specs = await App.get("/api/clients/fields");
    return this._specs;
  },

  fieldByKey(key) {
    let found = null;
    (this._specs.groups || []).forEach((g) =>
      g.fields.forEach((f) => { if (f.key === key) found = f; }));
    return found;
  },

  async render() {
    await this.specs();
    this._items = await App.get("/api/clients");
    const rows = this._items.length
      ? this._items.map((c) =>
          '<tr class="clickable" data-cid="' + esc(c.client_id) + '">' +
          "<td>" + esc(c.client_id) + "</td>" +
          "<td>" + fieldDisplay((c.data || {}).name) + "</td>" +
          "<td>" + fieldDisplay((c.data || {}).sector) + "</td>" +
          "<td>" + fieldDisplay((c.data || {}).status) + "</td></tr>").join("")
      : '<tr><td colspan="4" class="empty">No clients yet.</td></tr>';
    const el = document.getElementById("tab-clients");
    el.innerHTML =
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">Clients</h3>' +
      '<span class="muted" style="margin-left:12px">External companies a client pack is prepared for. ' +
      "Click a row to open a client, set up its contact org tree and links, and generate its pack.</span>" +
      "</div>" +
      "<table><thead><tr><th>ID</th><th>Client</th><th>Sector</th><th>Status</th></tr></thead><tbody>" +
      rows + "</tbody></table>" +
      '<div class="row" style="margin-top:10px;align-items:flex-end">' +
      '<div class="field"><label>New client name *</label><input id="client-add-name"></div>' +
      '<button class="btn" id="client-add">Add client&hellip;</button></div>' +
      "</div>" +
      '<div id="client-detail"></div>';
    el.querySelectorAll("tr.clickable").forEach((tr) => {
      tr.onclick = () => this._showDetail(tr.getAttribute("data-cid"));
    });
    document.getElementById("client-add").onclick = () => this._add();
    if (this._openId && this._items.some((c) => c.client_id === this._openId)) {
      await this._showDetail(this._openId);
    } else {
      this._openId = null;
    }
  },

  _add() {
    const name = val("client-add-name");
    if (!name) { App.toast("A client name is required.", "error"); return; }
    App.amend("Register the client " + name + ".", "POST", "/api/clients",
      { name: name }, () => this.render());
  },
};
