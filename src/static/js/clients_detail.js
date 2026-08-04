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

// Per-client detail: company fields, the contact org tree (Divisions ->
// Departments -> Contacts) and Product/Model links. Augments the Clients object
// defined in clients.js. The pack-generation controls and history live in a
// further augmentation (clients_pack.js), loaded after.
Object.assign(Clients, {
  _collSpec(key) {
    return (this._specs.collections || []).find((c) => c.key === key);
  },

  // A prefilled control for one field spec (select keeps its current value).
  _control(id, field, current, options) {
    const opts = options || field.options || [];
    if (field.type === "choice" || options) {
      const choices = [""].concat(opts).map((o) =>
        "<option" + (String(o) === String(current || "") ? " selected" : "") + ">" +
        esc(o) + "</option>").join("");
      return '<select id="' + id + '">' + choices + "</select>";
    }
    if (field.type === "date") {
      return '<input id="' + id + '" type="date" value="' + esc(current || "") + '">';
    }
    return '<input id="' + id + '" value="' + esc(current || "") + '">';
  },

  _companyEditor(client) {
    const data = client.data || {};
    const editable = (this._specs.groups || []).flatMap((g) => g.fields)
      .filter((f) => f.key !== "name" || true)   // name is editable too
      .filter((f) => ["name", "legal_entity", "sector", "relationship_owner", "notes", "status"]
        .indexOf(f.key) >= 0);
    const controls = editable.map((f) =>
      '<div class="field"><label>' + esc(f.label) + "</label>" +
      this._control("cf-" + f.key, f, data[f.key]) + "</div>").join("");
    return '<div class="section-header">Company</div>' +
      '<div class="row" style="flex-wrap:wrap">' + controls + "</div>";
  },

  // Options a nested reference draws from this client's own collections: a
  // department picks one of the client's divisions; a contact picks a department.
  _nestedOptions(client, collKey, fieldKey) {
    const data = client.data || {};
    if (collKey === "departments" && fieldKey === "division") {
      return (data.divisions || []).map((d) => d.value);
    }
    if (collKey === "contacts" && fieldKey === "department") {
      return (data.departments || []).map((d) => d.value);
    }
    return null;
  },

  _section(client, collKey, blurb) {
    const spec = this._collSpec(collKey);
    const cols = spec.fields.filter((f) => !f.hidden);
    const items = (client.data || {})[collKey] || [];
    const head = cols.map((f) => "<th>" + esc(f.label) + "</th>").join("") + "<th></th>";
    const body = items.length
      ? items.map((it) => "<tr>" +
          cols.map((f) => "<td>" + fieldDisplay(it[f.key]) + "</td>").join("") +
          '<td><button class="btn small ghost" data-del="' + esc(collKey) + "|" +
          esc(it.item_id) + '">Remove</button></td></tr>').join("")
      : '<tr><td colspan="' + (cols.length + 1) + '" class="empty">None yet.</td></tr>';
    const addInputs = cols.map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      this._control("cadd-" + collKey + "-" + f.key, f, "",
        this._nestedOptions(client, collKey, f.key)) + "</div>").join("");
    return '<div class="section-header">' + esc(spec.label) + "</div>" +
      (blurb ? '<p class="muted">' + esc(blurb) + "</p>" : "") +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" +
      '<div class="row" style="margin-top:8px;flex-wrap:wrap">' + addInputs +
      '<button class="btn small" data-add="' + esc(collKey) + '">Add</button></div>';
  },

  _linksSection(client, opts) {
    const items = (client.data || {}).links || [];
    const label = (link) => {
      const pool = link.link_type === "Product" ? opts.products : opts.models;
      const hit = (pool || []).find((o) => o.id === link.subject_id);
      return hit ? hit.label + " (" + link.subject_id + ")" : link.subject_id;
    };
    const body = items.length
      ? items.map((it) => "<tr><td>" + esc(it.link_type) + "</td><td>" + esc(label(it)) +
          "</td><td>" + fieldDisplay(it.note) + "</td>" +
          '<td><button class="btn small ghost" data-del="links|' + esc(it.item_id) +
          '">Remove</button></td></tr>').join("")
      : '<tr><td colspan="4" class="empty">No products or models linked yet.</td></tr>';
    const subjectOptions = (pool) => pool.map((o) =>
      '<option value="' + esc(o.id) + '">' + esc(o.label) + "</option>").join("");
    return '<div class="section-header">Links</div>' +
      '<p class="muted">Link the Products and Models this client\'s pack should cover.</p>' +
      "<table><thead><tr><th>Type</th><th>Subject</th><th>Note</th><th></th></tr></thead><tbody>" +
      body + "</tbody></table>" +
      '<div class="row" style="margin-top:8px;align-items:flex-end">' +
      '<div class="field"><label>Type</label><select id="clink-type">' +
      "<option>Product</option><option>Model</option></select></div>" +
      '<div class="field"><label>Product</label><select id="clink-product">' +
      subjectOptions(opts.products || []) + "</select></div>" +
      '<div class="field" style="display:none"><label>Model</label><select id="clink-model">' +
      subjectOptions(opts.models || []) + "</select></div>" +
      '<div class="field"><label>Note</label><input id="clink-note"></div>' +
      '<button class="btn small" id="clink-add">Add link</button></div>';
  },

  async _showDetail(clientId) {
    this._openId = clientId;
    const [client, opts] = await Promise.all([
      App.get("/api/clients/" + clientId),
      App.get("/api/clients/" + clientId + "/link-options"),
    ]);
    const box = document.getElementById("client-detail");
    box.innerHTML =
      '<div class="card"><div class="row" style="align-items:center">' +
      "<h3 style=\"margin:0\">" + esc((client.data || {}).name || clientId) + "</h3>" +
      '<span class="muted" style="margin-left:10px">' + esc(clientId) + "</span></div>" +
      this._companyEditor(client) +
      this._section(client, "divisions", "The client's internal divisions (e.g. Risk).") +
      this._section(client, "departments", "Departments within a division (e.g. Model Validation).") +
      this._section(client, "contacts", "Key contacts within a department.") +
      this._linksSection(client, opts) +
      (this._packSection ? this._packSection(client) : "") +
      "</div>";
    this._wireDetail(clientId, client, opts);
  },

  // Refresh after an edit without the page jumping: rebuild, then restore the
  // scroll position. ``_refreshDetail`` rebuilds only the open client (used by the
  // register collections); ``_refreshAll`` rebuilds the whole tab so an edited
  // company field also updates its list row. Either way the viewport stays put.
  async _refreshDetail(clientId) {
    const y = window.scrollY;
    await this._showDetail(clientId);
    window.scrollTo(0, y);
  },

  async _refreshAll() {
    const y = window.scrollY;
    await this.render();
    window.scrollTo(0, y);
  },

  _wireDetail(clientId, client, opts) {
    const base = "/api/clients/" + clientId;
    ["name", "legal_entity", "sector", "relationship_owner", "notes", "status"].forEach((key) => {
      const el = document.getElementById("cf-" + key);
      if (el) el.onchange = () => App.amend("Edit " + key + ".", "POST", base + "/field",
        { field: key, value: el.value.trim() }, () => this._refreshAll());
    });
    document.querySelectorAll("#client-detail [data-add]").forEach((btn) => {
      btn.onclick = () => this._addItem(clientId, btn.getAttribute("data-add"));
    });
    document.querySelectorAll("#client-detail [data-del]").forEach((btn) => {
      const [coll, itemId] = btn.getAttribute("data-del").split("|");
      btn.onclick = () => App.amend("Remove item.", "POST",
        base + "/collections/" + coll + "/" + itemId + "/delete", {},
        () => this._refreshDetail(clientId));
    });
    this._wireLinks(clientId);
    if (this._wirePack) this._wirePack(clientId, client);
  },

  _addItem(clientId, collKey) {
    const spec = this._collSpec(collKey);
    const fields = {};
    spec.fields.filter((f) => !f.hidden).forEach((f) => {
      const v = val("cadd-" + collKey + "-" + f.key);
      if (v !== "") fields[f.key] = v;
    });
    App.amend("Add to " + collKey + ".", "POST",
      "/api/clients/" + clientId + "/collections/" + collKey, { fields: fields },
      () => this._refreshDetail(clientId));
  },

  _wireLinks(clientId) {
    const typeSel = document.getElementById("clink-type");
    const prodField = document.getElementById("clink-product").parentElement;
    const modelField = document.getElementById("clink-model").parentElement;
    const sync = () => {
      const isProduct = typeSel.value === "Product";
      prodField.style.display = isProduct ? "" : "none";
      modelField.style.display = isProduct ? "none" : "";
    };
    typeSel.onchange = sync;
    sync();
    document.getElementById("clink-add").onclick = () => {
      const isProduct = typeSel.value === "Product";
      const subject = document.getElementById(isProduct ? "clink-product" : "clink-model").value;
      if (!subject) { App.toast("Nothing to link.", "error"); return; }
      App.amend("Link a " + typeSel.value + ".", "POST",
        "/api/clients/" + clientId + "/collections/links",
        { fields: { link_type: typeSel.value, subject_id: subject, note: val("clink-note") } },
        () => this._refreshDetail(clientId));
    };
  },
});
