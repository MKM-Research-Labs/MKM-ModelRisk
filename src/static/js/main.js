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

const TABS = {
  inventory: Inventory, product: Product, mrc: MRC, documents: GovDocs, bibliography: Bibliography,
  audit: Audit, reports: AuditReports, reference: Reference,
};

// Tabs that share the persistent MRC-region bar, and how each re-filters when the
// region selection changes (without rebuilding the bar).
const REGION_RELOADERS = {
  mrc: () => MRC.render(),
  inventory: () => Inventory.loadList(),
  product: () => Product.loadList(),
  audit: () => Audit._draw(),
};

async function showTab(name) {
  document.querySelectorAll(".tab").forEach(function (b) {
    b.classList.toggle("active", b.getAttribute("data-tab") === name);
  });
  document.querySelectorAll(".panel").forEach(function (p) {
    p.classList.toggle("active", p.id === "tab-" + name);
  });
  if (REGION_RELOADERS[name]) {
    MrcNav.setReload(REGION_RELOADERS[name]);
    await MrcNav.showFor();
  } else {
    MrcNav.hide();
  }
  try {
    await TABS[name].render();
  } catch (e) {
    App.toast(e.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".tab").forEach(function (btn) {
    btn.onclick = function () { showTab(btn.getAttribute("data-tab")); };
  });
  document.getElementById("confirm-ok").onclick = function () { App.confirmPending(); };
  document.getElementById("confirm-cancel").onclick = function () { App.closeConfirm(); };
  document.getElementById("reg-submit").onclick = function () { Inventory.submitRegister(); };
  document.getElementById("reg-cancel").onclick = function () { Inventory.closeRegister(); };
  document.getElementById("product-reg-submit").onclick = function () { Product.submitRegister(); };
  document.getElementById("product-reg-cancel").onclick = function () { Product.closeRegister(); };
  // Changing the org scope re-filters the inventory if it's on screen.
  const refreshInventory = function () {
    if (document.getElementById("m-list")) Inventory.loadList();
  };
  OrgScope.onChange(refreshInventory);
  showTab("inventory");
  // Populate the scope dropdowns, then re-filter (applies any saved selection).
  OrgScope.init().then(refreshInventory);
});
