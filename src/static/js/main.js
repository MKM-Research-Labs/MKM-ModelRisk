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

const TABS = {
  inventory: Inventory, chain: Chain, product: Product, mlapps: MLApps,
  clients: Clients, mrc: MRC,
  documents: GovDocs, audit: Audit, reports: AuditReports, reference: Reference,
};

// Tabs that share the persistent MRC-region bar, and how each re-filters when the
// region selection changes (without rebuilding the bar).
const REGION_TABS = ["mrc", "inventory", "product", "mlapps", "audit"];
const REGION_RELOAD = {
  mrc: () => MRC.render(),
  inventory: () => Inventory.loadList(),
  product: () => Product.loadList(),
  mlapps: () => MLApps.loadList(),
  audit: () => Audit._draw(),
};

// Render each panel once, then just re-show it on later visits so switching tabs
// is instant. A panel re-renders only when marked dirty — by any mutation (data
// changed) or a region-bar selection (which changes what the lists show).
const Nav = {
  _dirty: new Set(Object.keys(TABS)),   // all need a first render

  markAllDirty() { Object.keys(TABS).forEach((t) => this._dirty.add(t)); },

  // A region selection: refresh the visible tab now; re-render the rest lazily.
  onRegionChange(active) {
    REGION_TABS.forEach((t) => { if (t !== active) this._dirty.add(t); });
    if (REGION_RELOAD[active]) REGION_RELOAD[active]();
  },

  async show(name) {
    document.querySelectorAll(".tab").forEach((b) =>
      b.classList.toggle("active", b.getAttribute("data-tab") === name));
    document.querySelectorAll(".panel").forEach((p) =>
      p.classList.toggle("active", p.id === "tab-" + name));
    if (REGION_TABS.indexOf(name) >= 0) {
      MrcNav.setReload(() => this.onRegionChange(name));
      await MrcNav.showFor();
    } else {
      MrcNav.hide();
    }
    if (this._dirty.has(name)) {
      this._dirty.delete(name);
      try {
        await TABS[name].render();
      } catch (e) {
        this._dirty.add(name);            // render failed → try again next visit
        App.toast(e.message, "error");
      }
    }
  },
};

function showTab(name) { return Nav.show(name); }

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".tab").forEach(function (btn) {
    btn.onclick = function () { showTab(btn.getAttribute("data-tab")); };
  });
  document.getElementById("confirm-ok").onclick = function () { App.confirmPending(); };
  document.getElementById("confirm-cancel").onclick = function () { App.closeConfirm(); };
  document.getElementById("reg-submit").onclick = function () { Inventory.submitRegister(); };
  document.getElementById("reg-cancel").onclick = function () { Inventory.closeRegister(); };
  document.getElementById("mlapp-reg-submit").onclick = function () { MLApps.submitRegister(); };
  document.getElementById("mlapp-reg-cancel").onclick = function () { MLApps.closeRegister(); };
  document.getElementById("product-reg-submit").onclick = function () { Product.submitRegister(); };
  document.getElementById("product-reg-cancel").onclick = function () { Product.closeRegister(); };
  // Changing the org scope re-filters the inventory if it's on screen.
  const refreshInventory = function () {
    if (document.getElementById("m-list")) Inventory.loadList();
  };
  OrgScope.onChange(refreshInventory);
  // Load the risk policy and the theme first so badges/heatmaps colour from them on the
  // first render, then show the inventory. The theme carries which token each status is
  // drawn in (config/theme.py); the policy overrides it per division. Failure of either
  // is non-fatal — a badge with no colour renders as the dash an unrated record shows.
  Promise.all([Policy.load(), Theme.load()]).then(function () { showTab("inventory"); });
  // Populate the scope dropdowns, then re-filter (applies any saved selection).
  OrgScope.init().then(refreshInventory);
  // The actor picker lists real People, so it loads with the reference data.
  Actor.init();
});
