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

// Admin tab: sub-tabs for each reference section. There is a single company per
// instance (no list / no "add another") — the Company tab edits the institution
// name + logo, stored on the MRC settings. The simple lists (Division,
// Line of Business, Calc Agent, People) render through _renderList with working inline
// edit/remove; MRC is a drill-in.
const Reference = {
  _tab: "company",
  _TABS: [
    ["company", "Company"], ["division", "Division"], ["line_of_business", "Line of Business"],
    ["mrc", "MRC"], ["calculating_agent", "Calc Agent"], ["data_source", "Data Source"],
    ["people", "People"],
    // model_type (and codebase) are admin-managed and already exposed by
    // /api/reference; they were just missing from the tab bar, so the type field's
    // reference list could not be maintained from the UI. Vendor sits with it —
    // both classify the model itself (its type and who supplies it).
    ["model_type", "Model Type"], ["vendor", "Vendor"],
    // The per-division risk policy: dimensions, ratings and the generated grids.
    ["risk", "Risk"],
    // The questionnaire every review works through. Its own tab rather than a row
    // among the reference lists: it is the institution's own standard, and the
    // review workflow is built around it.
    ["review_questions", "Review"],
    // The running order every meeting is seeded with. Beside the questionnaire
    // because they are the same kind of thing: a standard the institution sets,
    // copied onto each record it applies to.
    ["standing_agenda", "Agenda"],
    // The words a model's lifecycle can carry. Shown-as is the division's to
    // change; stored-as is what every record already holds and never moves.
    ["lifecycle_stage", "Lifecycle"],
    // Institution-specific wording that is not a reference list — what the
    // generated PDFs say (classification, author, legal notice).
    ["misc", "Misc"],
  ],

  async render() {
    const el = document.getElementById("tab-reference");
    const bar = this._TABS.map(([k, label]) =>
      '<button class="dtab' + (k === this._tab ? " active" : "") + '" data-atab="' + k + '">' +
      label + "</button>").join("");
    el.innerHTML = '<div class="card"><div class="dtabs">' + bar + '</div><div id="admin-body"></div></div>';
    el.querySelectorAll("[data-atab]").forEach((btn) => {
      btn.onclick = () => { this._tab = btn.getAttribute("data-atab"); this.render(); };
    });
    await this._renderBody(document.getElementById("admin-body"));
  },

  async _renderBody(container) {
    // The single company (institution name + logo) lives on the MRC settings,
    // not the reference lists — edited as one record, never added to.
    if (this._tab === "company") {
      await this._renderInstitution(container);
      return;
    }
    // The risk policy is per-division structured config, not a flat reference list.
    if (this._tab === "risk") {
      await RiskEditor.render(container);
      return;
    }
    // Misc is the singleton settings that are wording, not lists.
    if (this._tab === "misc") {
      await AdminMisc.render(container);
      return;
    }
    const res = await App.get("/api/reference");
    const spec = res.collections.find((c) => c.key === this._tab);
    // MRC committees are entities with a drill-in detail (fields + per-committee
    // Terms of Reference); the scope field reacts to the committee's level.
    if (this._tab === "mrc") {
      Committees.render(container, spec, res.data.mrc || [], res.data);
      return;
    }
    if (!spec) { container.innerHTML = '<div class="empty">This section has moved.</div>'; return; }
    if (this._tab === "lifecycle_stage") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The stages a model moves through. <b>Shown as</b> is what every screen " +
        "displays and is yours to change. <b>Stored as</b> is the word the records " +
        "themselves carry, fixed once the stage exists — renaming a stage therefore " +
        "changes what is shown without moving anything on record.");
      return;
    }
    if (this._tab === "standing_agenda") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The running order every meeting is seeded with. A meeting is copied the list " +
        "as it stands when it is scheduled and keeps its own agenda, so editing here " +
        "changes the <em>next</em> meeting — it never rewrites one already held. " +
        "<b>Role</b> is what the console draws for the item (a rollcall, the previous " +
        "minutes, the sign-off review); leave it blank for business the committee " +
        "always takes, which renders as an ordinary agenda item.");
      return;
    }
    if (this._tab === "review_questions") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The questions every review works through, asked of each model in this order. A " +
        "model is copied the list as it stands when it is registered and keeps its own " +
        "answers, so editing here changes what the <em>next</em> review asks — it never " +
        "rewrites an answer already given.");
      return;
    }
    this._renderList(container, spec, res.data[this._tab] || []);
  },

  // The one company per instance: its name + logo, stored on the MRC settings.
  // A single record — there is no option to add another company.
  async _renderInstitution(container) {
    const s = await App.get("/api/mrc/settings");
    const name = (s.fields && s.fields.org_name) || "";
    const logoImg = s.logo
      ? '<img src="/api/mrc/logo?ts=' + Date.now() + '" alt="logo" style="max-height:64px;' +
        'border:1px solid var(--line);border-radius:6px;padding:4px;background:#fff">'
      : '<span class="muted">No logo uploaded.</span>';
    container.innerHTML =
      '<div class="section-header">Company</div>' +
      '<p class="muted">There is a single company per instance &mdash; its name and logo head the ' +
      "console and the PDF reports. There is no option to add another.</p>" +
      '<div class="inforow" id="inst-name-row"><div class="k">Company name</div><div class="v">' +
      (name ? esc(name) : '<span class="muted">Not set</span>') +
      '</div><span class="edit-btn" id="inst-name-edit">edit</span></div>' +
      '<div class="section-header" style="margin-top:16px">Logo</div>' +
      '<p class="muted">Used in the Meeting Pack and Model Risk Report PDF headers.</p>' +
      '<div class="row" style="align-items:center">' + logoImg + "</div>" +
      '<div class="row" style="margin-top:8px"><input type="file" id="inst-logo-file" accept="image/png,image/jpeg">' +
      '<button class="btn small" id="inst-logo-upload">Upload logo</button></div>';
    document.getElementById("inst-name-edit").onclick = () => this._editInstitutionName(name);
    document.getElementById("inst-logo-upload").onclick = () => this._uploadInstitutionLogo();
  },

  _editInstitutionName(current) {
    const row = document.getElementById("inst-name-row");
    row.innerHTML = '<div class="k">Company name</div><div class="editor">' +
      '<input id="inst-name-input"><button class="btn small primary" id="inst-name-save">Save&hellip;</button>' +
      '<button class="btn small" id="inst-name-cancel">Cancel</button></div>';
    document.getElementById("inst-name-input").value = current || "";
    document.getElementById("inst-name-cancel").onclick = () => this.render();
    document.getElementById("inst-name-save").onclick = () => {
      const value = document.getElementById("inst-name-input").value.trim();
      App.amend("Set the company name.", "POST", "/api/mrc/settings/field",
        { field: "org_name", value: value }, () => { this.render(); OrgScope.init(); });
    };
  },

  _uploadInstitutionLogo() {
    const fileInput = document.getElementById("inst-logo-file");
    if (!fileInput.files.length) { App.toast("Choose an image first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    fetch("/api/mrc/settings/logo", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Logo uploaded", "ok");
      this.render();
      OrgScope.init();   // refresh the header logo
    }).catch((e) => App.toast(e.message, "error"));
  },

  // A plain reference list rendered as a table with a working add form and
  // inline edit / remove per row (via the confirm-to-amend flow). Selectors
  // mirror the shared Collections module so the e2e helpers can drive both.
  _renderList(container, spec, items, intro) {
    const cols = spec.fields.filter((f) => !f.hidden);
    const head = cols.map((f) => "<th>" + esc(f.label) + "</th>").join("") + "<th></th>";
    const body = items.length
      ? items.map((it, i) =>
          '<tr id="rlrow-' + esc(it.item_id) + '">' +
          cols.map((f) => "<td>" + fieldDisplay(it[f.key]) + "</td>").join("") +
          '<td class="rowact">' +
          '<button class="edit-btn" data-mv="up|' + esc(it.item_id) + '" title="Move up"' +
          (i === 0 ? " disabled" : "") + ">\u2191</button>" +
          '<button class="edit-btn" data-mv="down|' + esc(it.item_id) + '" title="Move down"' +
          (i === items.length - 1 ? " disabled" : "") + ">\u2193</button> " +
          '<button class="btn small" data-ed="' + esc(spec.key) + "|" + esc(it.item_id) +
          '">Edit</button> <button class="btn small danger" data-rm="' + esc(spec.key) + "|" + esc(it.item_id) +
          '">Remove</button></td></tr>').join("")
      : '<tr><td colspan="' + (cols.length + 1) + '" class="empty">None yet.</td></tr>';
    // A readonly field (a person's ratified roles) is recorded by the process that
    // grants it, so it is shown in the table but never offered as an input.
    const addInputs = cols.filter((f) => !f.readonly).map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("add-" + spec.key + "-" + f.key, f) + "</div>").join("");
    container.innerHTML =
      '<div class="section-header">' + esc(spec.label) + "</div>" +
      (intro ? '<p class="muted" style="font-size:12px">' + intro + "</p>" : "") +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" +
      '<div class="row" style="margin-top:8px">' + addInputs +
      '<button class="btn small" data-add="' + esc(spec.key) + '">Add&hellip;</button></div>';
    container.querySelector('[data-add="' + spec.key + '"]').onclick = () => {
      const fields = {};
      // An empty list is dropped on ADD (nothing to say yet); on edit it is kept, so a
      // role can be taken away.
      cols.filter((f) => !f.readonly).forEach((f) => {
        const v = val("add-" + spec.key + "-" + f.key);
        if (v !== "" && !(Array.isArray(v) && !v.length)) fields[f.key] = v;
      });
      App.amend("Add to " + spec.label + ".", "POST",
        "/api/reference/collections/" + spec.key, { fields: fields }, () => this.render());
    };
    container.querySelectorAll("[data-rm]").forEach((btn) => {
      const id = btn.getAttribute("data-rm").split("|")[1];
      btn.onclick = () => App.amend("Remove " + id + ".", "POST",
        "/api/reference/collections/" + spec.key + "/" + id + "/delete", {}, () => this.render());
    });
    container.querySelectorAll("[data-mv]").forEach((btn) => {
      if (btn.disabled) return;
      const [direction, id] = btn.getAttribute("data-mv").split("|");
      // Reordering is an edit to what every dropdown offers, so it is confirmed and
      // recorded like the others rather than treated as a display preference.
      btn.onclick = () => App.amend("Move " + id + " " + direction + ".", "POST",
        "/api/reference/collections/" + spec.key + "/" + id + "/move",
        { direction: direction }, () => this.render());
    });
    container.querySelectorAll("[data-ed]").forEach((btn) => {
      const id = btn.getAttribute("data-ed").split("|")[1];
      const item = items.find((i) => i.item_id === id);
      btn.onclick = () => this._listEdit(spec, cols, item);
    });
  },

  _listEdit(spec, cols, item) {
    const row = document.getElementById("rlrow-" + item.item_id);
    row.innerHTML = '<td colspan="' + (cols.length + 1) + '"><div class="row">' +
      cols.map((f) => '<div class="field"><label>' + esc(f.label) + "</label>" +
        (f.readonly || f.immutable
          ? '<div class="ro">' + fieldDisplay(item[f.key]) + "</div>"
          : inputControl("ce-" + f.key, f)) + "</div>").join("") +
      '<button class="btn small primary" id="ce-save">Save&hellip;</button>' +
      '<button class="btn small" id="ce-cancel">Cancel</button></div></td>';
    cols.filter((f) => !f.readonly && !f.immutable).forEach((f) => {
      const el = document.getElementById("ce-" + f.key);
      const current = item[f.key];
      if (current === null || current === undefined) return;
      // A multi-select cannot be filled by assigning `.value`; each held value has to be
      // marked selected, or editing a person would quietly drop their roles.
      if (el.multiple) {
        const held = new Set(Array.isArray(current) ? current : [current]);
        [...el.options].forEach((o) => { o.selected = held.has(o.value); });
      } else {
        el.value = current;
      }
    });
    document.getElementById("ce-cancel").onclick = () => this.render();
    document.getElementById("ce-save").onclick = () => {
      const fields = {};
      cols.filter((f) => !f.readonly && !f.immutable).forEach((f) => {
        const v = val("ce-" + f.key);
        if (v !== "" || Array.isArray(v)) fields[f.key] = v;
      });
      App.amend("Update " + item.item_id + ".", "POST",
        "/api/reference/collections/" + spec.key + "/" + item.item_id, { fields: fields }, () => this.render());
    };
  },
};
