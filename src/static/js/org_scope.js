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

// Header org-scope: there is a single institution (Phase MRC-5). Its name lives
// on the MRC settings under org_name; the header shows the logo + that name.
// No filtering — every model in the instance belongs to it.
const OrgScope = {
  _onChange: null,

  async init() {
    let logo = "", name = "";
    try {
      const s = await App.get("/api/mrc/settings");
      if (s && s.logo) {
        logo = '<img src="/api/mrc/logo?ts=' + Date.now() + '" alt="logo" ' +
          'style="max-height:28px;vertical-align:middle;margin-right:8px;border-radius:4px">';
      }
      if (s && s.fields && s.fields.org_name) {
        name = '<b style="vertical-align:middle">' + esc(s.fields.org_name) + "</b>";
      }
    } catch (e) { /* settings not yet reachable */ }
    if (!name) name = '<span class="muted">Set the institution name in Admin &rarr; MRC.</span>';
    const el = document.getElementById("org-scope-display");
    if (el) el.innerHTML = logo + name;
  },

  // No scope filter — every model in the instance belongs to the institution.
  get() { return {}; },
  matches() { return true; },
  onChange(fn) { this._onChange = fn; },
};
