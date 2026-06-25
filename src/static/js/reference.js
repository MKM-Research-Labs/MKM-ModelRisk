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
// Department, MRC settings, People. The org lists reuse the shared Collections
// renderer; a Division picks its Company and a Department its Division.
const Reference = {
  _tab: "company",
  _TABS: [
    ["company", "Company"], ["division", "Division"], ["department", "Department"],
    ["market_data_model", "Market Data"], ["calculating_agent", "Calc Agent"],
    ["mrc", "MRC"], ["people", "People"],
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
    if (this._tab === "mrc") {
      await Settings.render(container);
      return;
    }
    const res = await App.get("/api/reference");
    const spec = res.collections.find((c) => c.key === this._tab);
    const specs = { collections: [spec] };
    const data = {};
    data[this._tab] = res.data[this._tab] || [];
    let html = Collections.render(data, specs, false);
    if (this._tab === "company") html += await this._logoSection();
    container.innerHTML = html;
    Collections.bind("/api/reference/collections/", specs, false, () => this.render(), data);
    if (this._tab === "company") {
      document.getElementById("logo-upload").onclick = () => this._uploadLogo();
    }
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
