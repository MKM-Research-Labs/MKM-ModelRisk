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

// What the console is, at the top level: which tabs exist, which of them answer to the
// region navigator, and what a link into one of them means.
//
// The bootstrap is the last thing to run. It waits on the three registries -- the
// theme's tokens, the risk policy and the functional groups -- before the first render,
// because every screen below draws vocabulary and colour from them, and a screen that
// rendered first would show an adopter's renamed status by its stored value.
//
// A tab is registered here rather than discovering itself, so the set of tabs is one
// list you can read. REGION_TABS says which of them the org navigator applies to, and
// DEEP_LINK says what a #hash resolves to -- a deep link lands on a list, so anything
// deeper has to say how to open the record it names.

const TABS = {
  dashboard: Dashboard,
  inventory: Inventory, chain: Chain, product: Product, mlapps: MLApps,
  aisystems: AISystems,
  clients: Clients, mrc: MRC,
  documents: GovDocs, audit: Audit, reports: AuditReports, reference: Reference,
};

// Tabs that share the persistent MRC-region bar, and how each re-filters when the
// region selection changes (without rebuilding the bar).
const REGION_TABS = ["mrc", "inventory", "product", "mlapps", "aisystems", "audit"];
const REGION_RELOAD = {
  mrc: () => MRC.render(),
  inventory: () => Inventory.loadList(),
  product: () => Product.loadList(),
  mlapps: () => MLApps.loadList(),
  aisystems: () => AISystems.loadList(),
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
    // A tab lands on its list. The panels are cached so switching is instant, and
    // that cache used to include an open detail: opening an AI System, leaving the
    // tab and coming back showed that one record with its list hidden underneath and
    // no list in sight. Screens with a detail view say how to get back to the list;
    // the rest define nothing and are unaffected.
    if (TABS[name] && TABS[name].onShow) TABS[name].onShow();
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

// A link from outside: the ERM's click-through, or somebody's bookmark.
// "#<tab>" opens that tab; "#<tab>/<id>" opens the record on it. Only these four
// take an id — a tab with no per-record screen simply opens. Nothing else is
// routed: the console is one page, and inventing routes it does not have would
// strand the reader on a blank panel with no way to say what went wrong.
const DEEP_LINK = {
  inventory: (id) => Detail.show(id),
  product: (id) => ProductDetail.show(id),
  mlapps: (id) => MLAppDetail.show(id),
  aisystems: (id) => AISystemDetail.show(id),
  mrc: (id) => MRC.openMeeting(id),
};

// Open whatever the current hash names. Returns false when it names nothing we
// have, so the caller can fall back to the landing tab rather than showing blank.
function openHash() {
  const parts = (location.hash || "").replace(/^#/, "").split("/");
  const tab = parts[0];
  if (!tab || !TABS[tab]) return false;
  showTab(tab).then(function () {
    if (parts[1] && DEEP_LINK[tab]) DEEP_LINK[tab](decodeURIComponent(parts[1]));
  });
  return true;
}

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
  document.getElementById("ais-reg-submit").onclick = function () { AISystems.submitRegister(); };
  document.getElementById("ais-reg-cancel").onclick = function () { AISystems.closeRegister(); };
  document.getElementById("product-reg-submit").onclick = function () { Product.submitRegister(); };
  document.getElementById("product-reg-cancel").onclick = function () { Product.closeRegister(); };
  // Changing the org scope re-filters the inventory if it's on screen.
  const refreshInventory = function () {
    if (document.getElementById("m-list")) Inventory.loadList();
  };
  OrgScope.onChange(refreshInventory);
  // Load the risk policy and the theme first so badges/heatmaps colour from them on the
  // first render, then show the landing tab. The theme carries which token each status is
  // drawn in (config/theme.py); the policy overrides it per division. Failure of either
  // is non-fatal — a badge with no colour renders as the dash an unrated record shows.
  //
  // The dashboard lands rather than the inventory: the first question a reader has is
  // whether anything needs them, and a register cannot answer it.
  Promise.all([Policy.load(), Groups.load(), Stages.load(), Theme.load()])
    .then(function () {
    if (!openHash()) showTab("dashboard");
  });
  // A second link, followed while the console is already open, must move the page
  // too — otherwise the URL changes and nothing else does.
  window.addEventListener("hashchange", openHash);
  // Populate the scope dropdowns, then re-filter (applies any saved selection).
  OrgScope.init().then(refreshInventory);
  // The actor picker lists real People, so it loads with the reference data.
  Actor.init();
});
