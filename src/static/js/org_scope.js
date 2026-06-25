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

// Header org-scope: the Company a model lives under. The selection filters the
// inventory and is applied to newly registered models.
const OrgScope = {
  _onChange: null,
  _KEY: "mkm-org-scope",

  async init() {
    const data = (await App.get("/api/reference")).data || {};
    this._fill("scope-company", data.company, "All companies");
    this._set("scope-company", this._saved().company);
    document.getElementById("scope-company").onchange = () => this._changed();
  },

  _fill(id, items, allLabel) {
    const sel = document.getElementById(id);
    const opts = ['<option value="">' + allLabel + "</option>"]
      .concat((items || []).map((it) => "<option>" + esc(it.value) + "</option>"));
    sel.innerHTML = opts.join("");
  },

  _set(id, value) {
    const sel = document.getElementById(id);
    if (value && [...sel.options].some((o) => o.value === value)) sel.value = value;
  },

  _saved() {
    try {
      return JSON.parse(localStorage.getItem(this._KEY)) || {};
    } catch (e) {
      return {};
    }
  },

  _changed() {
    try {
      localStorage.setItem(this._KEY, JSON.stringify(this.get()));
    } catch (e) { /* ignore storage failures */ }
    if (this._onChange) this._onChange();
  },

  // {company} — only included when a company is selected.
  get() {
    const scope = {};
    const company = document.getElementById("scope-company").value;
    if (company) scope.company = company;
    return scope;
  },

  // True if model data matches the current scope (a blank scope matches all).
  matches(data) {
    const scope = this.get();
    return Object.keys(scope).every((k) => (data || {})[k] === scope[k]);
  },

  onChange(fn) { this._onChange = fn; },
};
