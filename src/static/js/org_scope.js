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

// Header org-scope: there is a single institution (the backend allows only one
// Company). Rather than a picker, the header shows that company's logo and name;
// models are registered into it and the inventory is scoped to it.
const OrgScope = {
  _onChange: null,
  _company: "",

  async init() {
    const data = (await App.get("/api/reference")).data || {};
    const companies = data.company || [];
    this._company = companies.length ? companies[0].value : "";
    let logo = "";
    try {
      const s = await App.get("/api/mrc/settings");
      if (s && s.logo) {
        logo = '<img src="/api/mrc/logo?ts=' + Date.now() + '" alt="logo" ' +
          'style="max-height:28px;vertical-align:middle;margin-right:8px;border-radius:4px">';
      }
    } catch (e) { /* no branding logo set */ }
    const name = this._company
      ? '<b style="vertical-align:middle">' + esc(this._company) + "</b>"
      : '<span class="muted">No company set</span>';
    const el = document.getElementById("org-scope-display");
    if (el) el.innerHTML = logo + name;
  },

  // {company} — the single institution (empty before one is defined).
  get() {
    return this._company ? { company: this._company } : {};
  },

  // True if model data matches the current scope (empty scope matches all).
  matches(data) {
    const scope = this.get();
    return Object.keys(scope).every((k) => (data || {})[k] === scope[k]);
  },

  onChange(fn) { this._onChange = fn; },
};
