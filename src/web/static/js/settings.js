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
    container.innerHTML =
      '<div class="card"><h3>MRC settings &amp; branding</h3>' +
      '<p class="muted">These populate the console header cards and the Meeting Pack PDF header. ' +
      "The company logo is set on the Company tab.</p>" + rows + "</div>";
    this._bind(s);
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
