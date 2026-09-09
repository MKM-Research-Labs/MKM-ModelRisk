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

// The one company this instance governs: its name and its logo.
//
// Split from reference.js, which is a tab strip over the reference LISTS — divisions,
// lines of business, calculating agents, people, each of them a set you add to and
// remove from. This is the tab that is not a list at all, and that is the whole reason
// it is separate: there is exactly one institution per instance, so there is no "add
// another" and no remove, and the screen has to say so by not offering them.
//
// Both values live on the MRC settings rather than in a reference collection, because
// the institution is not one of the things the institution keeps a register of. The
// logo is the adopter's own upload and heads every generated PDF.
//
// Assigns onto Reference; loads after reference.js.

Object.assign(Reference, {

  // The one company per instance: its name + logo, stored on the MRC settings.
  // A single record — there is no option to add another company.
  async _renderInstitution(container) {
    const s = await App.get("/api/mrc/settings");
    const name = (s.fields && s.fields.org_name) || "";
    const logoImg = s.logo
      ? '<img src="/api/mrc/logo?ts=' + Date.now() + '" alt="logo" style="max-height:64px;' +
        'border:1px solid var(--line);border-radius:var(--radius-md);padding:var(--space-2);background:var(--panel)">'
      : '<span class="muted">No logo uploaded.</span>';
    container.innerHTML =
      '<div class="section-header">Company</div>' +
      '<p class="muted">There is a single company per instance &mdash; its name and logo head the ' +
      "console and the PDF reports. There is no option to add another.</p>" +
      '<div class="inforow" id="inst-name-row"><div class="k">Company name</div><div class="v">' +
      (name ? esc(name) : '<span class="muted">Not set</span>') +
      '</div><span class="edit-btn" id="inst-name-edit">edit</span></div>' +
      '<div class="section-header" style="margin-top:var(--space-8)">Logo</div>' +
      '<p class="muted">Used in the Meeting Pack and Model Risk Report PDF headers.</p>' +
      '<div class="row" style="align-items:center">' + logoImg + "</div>" +
      '<div class="row" style="margin-top:var(--space-4)"><input type="file" id="inst-logo-file" accept="image/png,image/jpeg">' +
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
});
