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

// The two-tier org navigator (divisions on the top row, their lines of business
// below) shared by the MRC, Models, Products and Audit Trail tabs. The selection
// lives here on `state` so the chosen region persists as the user moves between
// those tabs. state = {div, lob}: both null = "All"; a division with lob null =
// the whole division; div + lob = one line of business.
//
// The org hierarchy is Company > Division > Line of Business. MRC committees are
// *attached* to that tree, not part of it — so they are not what this bar
// navigates. The MRC tab lists the committees in the selected region instead.
const MrcNav = {
  state: { div: null, lob: null },
  _cache: null,             // {ref, committees} — shared so tab switches don't re-fetch
  _gen: 0,                  // bumped by invalidate(); see load()

  // Reference data for the nav, fetched once and reused across tabs. Any mutation
  // (via App.confirmPending) invalidates it, so committee/division edits show up.
  //
  // An invalidate() landing while a fetch is in flight must not be swallowed: the
  // response was read before the mutation, so caching it would pin the nav to
  // pre-mutation data until something else invalidated. Stamp each load with the
  // generation it started in and only cache when that generation still stands —
  // otherwise return the fresh read without caching it, and let the next load
  // re-fetch.
  async load() {
    if (!this._cache) {
      const gen = this._gen;
      const ref = (await App.get("/api/reference")).data || {};
      const committees = (ref.mrc || []).filter((c) => c.archived !== "true");
      const loaded = { ref, committees };
      if (gen === this._gen) this._cache = loaded;
      return loaded;
    }
    return this._cache;
  },

  invalidate() { this._cache = null; this._key = null; this._gen += 1; },

  // --- the single persistent bar (#region-nav), shared across the four tabs ---
  _reload: null,            // the active tab's re-filter callback
  _key: null,               // render signature, so tab switches don't rebuild it

  // Route region selections to the active tab's list.
  setReload(fn) { this._reload = fn; },

  hide() {
    const el = document.getElementById("region-nav");
    if (el) el.style.display = "none";
  },

  // Show the bar for a region tab and render it (from cache) if not already
  // current. Merely switching tabs leaves the existing DOM in place — no rebuild,
  // so no flicker. The signature covers what the bar draws: the org tree, not the
  // committee list, which is why committee edits alone leave it standing.
  async showFor() {
    const el = document.getElementById("region-nav");
    if (!el) return;
    el.style.display = "";
    const { committees, ref } = await this.load();
    this.normalize(committees, ref);
    const key = JSON.stringify(this.state) + "|" +
      ((ref && ref.division) || []).map((d) => d.value).join(",") + "|" +
      ((ref && ref.line_of_business) || []).map((l) => l.value + "@" + l.division).join(",");
    if (key === this._key && el.firstChild) return;   // unchanged → leave as-is
    this._key = key;
    el.innerHTML = this.html(ref);
    this.bind(el, () => {
      this._key = null;                 // selection changed → allow re-render
      this.showFor();
      if (this._reload) this._reload();
    });
  },

  // The lines of business under `div`, in reference order.
  lobsForDivision(div, ref) {
    if (!div) return [];
    return ((ref && ref.line_of_business) || []).filter((l) => l.division === div);
  },

  // Every division from reference data, in reference order, so the top row
  // showcases the whole org tree — including divisions with no lines of business
  // or models yet, so you can select one and register into it.
  orderedDivisions(ref) {
    return ((ref && ref.division) || []).map((d) => d.value);
  },

  // Repair the shared state if its division/line of business no longer exists.
  // `committees` is unused — see the note above the scope helpers below.
  normalize(committees, ref) {
    const s = this.state || { div: null, lob: null };
    if (!s.div) { this.state = { div: null, lob: null }; return; }
    if (!this.orderedDivisions(ref).includes(s.div)) {
      this.state = { div: null, lob: null }; return;
    }
    if (s.lob && !this.lobsForDivision(s.div, ref).some((l) => l.value === s.lob)) {
      this.state = { div: s.div, lob: null }; return;
    }
    this.state = { div: s.div, lob: s.lob };
  },

  // Two-tier tab strip: an "All" tab and the divisions on top; when a division is
  // active, its "All <div>" tab plus that division's lines of business below.
  html(ref) {
    const state = this.state;
    const divisions = this.orderedDivisions(ref);
    if (!divisions.length) return "";
    const tab = (label, active, attr) =>
      '<button class="dtab' + (active ? " active" : "") + '" ' + attr + ">" + esc(label) + "</button>";
    const top = tab("All", !state.div, 'data-all="1"') +
      divisions.map((dv) => tab(dv, state.div === dv, 'data-div="' + esc(dv) + '"')).join("");
    let second = "";
    const lobs = state.div ? this.lobsForDivision(state.div, ref) : [];
    if (lobs.length) {
      second =
        '<div class="dtabs" style="margin-top:var(--space-4);border-top:1px solid var(--line);padding-top:var(--space-4)">' +
        tab("All " + state.div, !state.lob, 'data-divall="1"') +
        lobs.map((l) =>
          tab(l.value, state.lob === l.value, 'data-lob="' + esc(l.value) + '"')).join("") +
        "</div>";
    }
    return '<div class="card" style="padding:var(--space-4) var(--space-6);margin-bottom:var(--space-6)">' +
      '<div class="dtabs">' + top + "</div>" + second + "</div>";
  },

  // Wire selection clicks inside `container`; update the shared state and call
  // onChange() (no args) so the calling tab can re-render/re-filter.
  bind(container, onChange) {
    const set = (s) => { this.state = s; onChange(); };
    container.querySelectorAll("[data-all]").forEach((b) =>
      (b.onclick = () => set({ div: null, lob: null })));
    container.querySelectorAll("[data-div]").forEach((b) =>
      (b.onclick = () => set({ div: b.getAttribute("data-div"), lob: null })));
    container.querySelectorAll("[data-divall]").forEach((b) =>
      (b.onclick = () => set({ div: this.state.div, lob: null })));
    container.querySelectorAll("[data-lob]").forEach((b) =>
      (b.onclick = () => set({ div: this.state.div, lob: b.getAttribute("data-lob") })));
  },
};
