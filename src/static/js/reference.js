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

// Admin tab: sub-tabs for each section (left to right) — Company, Division,
// Department, MRC, People. The org lists reuse the shared Collections renderer;
// a Division picks its Company and a Department its Division. The MRC tab shows
// the committees list and, below it, the MRC's own detail (settings + Terms of
// Reference) — one place for everything about the committee.
const Reference = {
  _tab: "company",
  _TABS: [
    ["company", "Company"], ["division", "Division"], ["department", "Department"],
    ["mrc", "MRC"], ["calculating_agent", "Calc Agent"], ["people", "People"],
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
    const res = await App.get("/api/reference");
    const spec = res.collections.find((c) => c.key === this._tab);
    // MRC committees are entities with a drill-in detail (fields + per-committee
    // Terms of Reference), not a plain inline-edit table.
    if (this._tab === "mrc") {
      Committees.render(container, spec, res.data.mrc || []);
      return;
    }
    // There is only ever one company: show it as a single editable record (name
    // + owner) with the logo — no list/add/remove table.
    if (this._tab === "company") {
      await this._renderCompany(container, spec, res.data.company || []);
      return;
    }
    const specs = { collections: [spec] };
    const data = {};
    data[this._tab] = res.data[this._tab] || [];
    container.innerHTML = Collections.render(data, specs, false);
    Collections.bind("/api/reference/collections/", specs, false, () => this.render(), data);
  },

  // The company's "value" field is its name; label it as such.
  _companyLabel(f) { return f.key === "value" ? "Company name" : f.label; },

  async _renderCompany(container, spec, items) {
    const logoHtml = await this._logoSection();
    if (!items.length) {
      // Bootstrap only: no company exists yet, so offer a one-time create form.
      const inputs = spec.fields.map((f) =>
        '<div class="field"><label>' + esc(this._companyLabel(f)) + (f.required ? " *" : "") +
        "</label>" + inputControl("co-add-" + f.key, f) + "</div>").join("");
      container.innerHTML = '<div class="section-header">Company</div>' +
        '<p class="muted">Define the institution &mdash; everything else links to it.</p>' +
        '<div class="row">' + inputs + '<button class="btn small" id="co-add">Create&hellip;</button></div>' +
        logoHtml;
      document.getElementById("co-add").onclick = () => {
        const fields = {};
        spec.fields.forEach((f) => { const v = val("co-add-" + f.key); if (v !== "") fields[f.key] = v; });
        App.amend("Set the company.", "POST", "/api/reference/collections/company",
          { fields: fields }, () => this.render());
      };
      document.getElementById("logo-upload").onclick = () => this._uploadLogo();
      return;
    }
    const item = items[0];
    const rows = spec.fields.map((f) =>
      '<div class="inforow" id="corow-' + f.key + '"><div class="k">' + esc(this._companyLabel(f)) +
      '</div><div class="v">' + fieldDisplay(item[f.key]) +
      '</div><span class="edit-btn" data-coed="' + f.key + '">edit</span></div>').join("");
    container.innerHTML = '<div class="section-header">Company</div>' + rows + logoHtml;
    document.querySelectorAll("[data-coed]").forEach((btn) => {
      const f = spec.fields.find((x) => x.key === btn.getAttribute("data-coed"));
      btn.onclick = () => this._editCompanyField(item, f);
    });
    document.getElementById("logo-upload").onclick = () => this._uploadLogo();
  },

  _editCompanyField(item, f) {
    const row = document.getElementById("corow-" + f.key);
    row.innerHTML = '<div class="k">' + esc(this._companyLabel(f)) + '</div><div class="editor">' +
      inputControl("coed-input", f) + '<button class="btn small primary" id="coed-save">Save&hellip;</button>' +
      '<button class="btn small" id="coed-cancel">Cancel</button></div>';
    const input = document.getElementById("coed-input");
    if (item[f.key] !== null && item[f.key] !== undefined) input.value = item[f.key];
    document.getElementById("coed-cancel").onclick = () => this.render();
    document.getElementById("coed-save").onclick = () => {
      const fields = {};
      fields[f.key] = input.value.trim();
      App.amend("Update the company.", "POST",
        "/api/reference/collections/company/" + item.item_id, { fields: fields }, () => this.render());
    };
  },

  // The (single) company's logo — used in the Meeting Pack & Model Risk Report
  // PDF headers. Stored as the institution branding logo.
  async _logoSection() {
    const s = await App.get("/api/mrc/settings");
    const logo = s.logo
      ? '<img src="/api/mrc/logo?ts=' + Date.now() + '" alt="logo" style="max-height:64px;' +
        'border:1px solid var(--line);border-radius:6px;padding:4px;background:#fff">'
      : '<span class="muted">No logo uploaded.</span>';
    return '<div class="section-header">Company logo</div>' +
      '<p class="muted">Used in the Meeting Pack and Model Risk Report PDF headers.</p>' +
      '<div class="row" style="align-items:center">' + logo + "</div>" +
      '<div class="row" style="margin-top:8px"><input type="file" id="logo-file" accept="image/png,image/jpeg">' +
      '<button class="btn small" id="logo-upload">Upload logo</button></div>';
  },

  _uploadLogo() {
    const fileInput = document.getElementById("logo-file");
    if (!fileInput.files.length) { App.toast("Choose an image first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    fetch("/api/mrc/settings/logo", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json(); throw new Error(e.error || "upload failed"); }
      App.toast("Logo uploaded", "ok");
      this.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
