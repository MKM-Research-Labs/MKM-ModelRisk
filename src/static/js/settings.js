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

// MRC settings & branding editor (org details + logo) — shown on the Admin tab.
// Drives the console header cards and the Meeting Pack PDF header.
const Settings = {
  _container: null,

  async render(container) {
    this._container = container;
    const s = await App.get("/api/mrc/settings");
    const rows = s.specs.map((f) =>
      '<div class="inforow" id="srow-' + f.key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + fieldDisplay(s.fields[f.key]) +
      '</div><span class="edit-btn" data-sed="' + f.key + '">edit</span></div>').join("");
    const tor = s.tor
      ? '<div class="row" style="align-items:center;margin-top:8px">' +
        '<a href="/api/mrc/tor" target="_blank">&darr; ' + esc(s.tor.original_name) + "</a>" +
        '<button class="btn small" id="tor-replace" style="margin-left:auto">Replace&hellip;</button></div>'
      : '<div class="muted" style="margin-top:8px">No Terms of Reference uploaded.</div>';
    container.innerHTML =
      '<div class="card"><h3>MRC detail</h3>' +
      '<p class="muted">These populate the console header cards and the Meeting Pack PDF header. ' +
      "The company logo is set on the Company tab.</p>" + rows +
      '<div class="section-header" style="margin-top:16px">Terms of Reference</div>' + tor +
      '<div class="row" style="margin-top:6px"><input type="file" id="tor-file">' +
      '<button class="btn small primary" id="tor-upload">Upload ToR</button></div>' +
      "</div>";
    this._bind(s);
    document.getElementById("tor-upload").onclick = () => this._uploadTor();
  },

  _uploadTor() {
    const fileInput = document.getElementById("tor-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    fetch("/api/mrc/settings/tor", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json(); throw new Error(e.error || "upload failed"); }
      App.toast("Terms of Reference uploaded", "ok");
      this.render(this._container);
    }).catch((e) => App.toast(e.message, "error"));
  },

  _bind(s) {
    const self = this;
    const byKey = {};
    s.specs.forEach((f) => { byKey[f.key] = f; });
    document.querySelectorAll("[data-sed]").forEach(function (btn) {
      const key = btn.getAttribute("data-sed");
      btn.onclick = function () { self._edit(byKey[key], s.fields[key]); };
    });
  },

  _edit(f, current) {
    const row = document.getElementById("srow-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      inputControl("set-input", f) + '<button class="btn small primary" id="set-save">Save…</button>' +
      '<button class="btn small" id="set-cancel">Cancel</button></div>';
    const input = document.getElementById("set-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("set-cancel").onclick = () => this.render(this._container);
    document.getElementById("set-save").onclick = () => {
      App.amend('Set ' + f.label + ' = "' + input.value + '".', "POST", "/api/mrc/settings/field",
        { field: f.key, value: input.value.trim() }, () => this.render(this._container));
    };
  },
};
