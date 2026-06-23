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

// Admin tab: maintain the Company / Division / Department menu lists. Reuses the
// shared Collections renderer — each menu list is just a collection of values.
const Reference = {
  async render() {
    const res = await App.get("/api/reference");
    const specs = { collections: res.collections };
    const el = document.getElementById("tab-reference");
    el.innerHTML =
      '<div class="card"><h3>Administration — people &amp; menu lists</h3>' +
      '<p class="muted">Manage the people directory and the Company / Division / Department ' +
      "menus. People populate the Owner, Peer reviewer and Chair dropdowns; the menus populate " +
      "the organisation dropdowns. Everyone may amend; every change is recorded in the audit trail.</p>" +
      Collections.render(res.data, specs, false) + "</div>";
    Collections.bind("/api/reference/collections/", specs, false, () => this.render(), res.data);
  },
};
