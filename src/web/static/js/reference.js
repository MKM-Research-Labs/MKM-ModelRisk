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
    container.innerHTML = Collections.render(data, specs, false);
    Collections.bind("/api/reference/collections/", specs, false, () => this.render(), data);
  },
};
