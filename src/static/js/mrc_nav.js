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

// The two-tier MRC region navigator (divisions on the top row, their committees
// below) shared by the MRC, Models, Products and Audit Trail tabs. The selection
// lives here on `state` so the chosen region persists as the user moves between
// those tabs. state = {div, mrc}: both null = "All"; a division with mrc null =
// the whole division; div + mrc = one committee's scope.
const MrcNav = {
  state: { div: null, mrc: null },
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
  // so no flicker.
  async showFor() {
    const el = document.getElementById("region-nav");
    if (!el) return;
    el.style.display = "";
    const { committees, ref } = await this.load();
    this.normalize(committees, ref);
    const key = JSON.stringify(this.state) + "|" +
      committees.map((c) => c.value).join(",") + "|" +
      ((ref && ref.division) || []).map((d) => d.value).join(",");
    if (key === this._key && el.firstChild) return;   // unchanged → leave as-is
    this._key = key;
    el.innerHTML = this.html(committees, ref);
    this.bind(el, committees, ref, () => {
      this._key = null;                 // selection changed → allow re-render
      this.showFor();
      if (this._reload) this._reload();
    });
  },

  // The division a committee rolls up to: a Division-level MRC's scope is itself
  // a division; a Line of Business-level one inherits its line of business's division;
  // Company-level (or unresolved) MRCs share a "Company" bucket.
  divisionOf(c, ref) {
    if (!c) return "Company";
    if (c.level === "Division") return c.scope_value || "Company";
    if (c.level === "Line of Business") {
      const lob = ((ref && ref.line_of_business) || []).find((d) => d.value === c.scope_value);
      return (lob && lob.division) || "Other";
    }
    return "Company";
  },

  // committees grouped by division: { divisionValue: [committee, …] }.
  groups(committees, ref) {
    const groups = {};
    committees.forEach((c) => {
      const dv = this.divisionOf(c, ref);
      (groups[dv] = groups[dv] || []).push(c);
    });
    return groups;
  },

  // Every division from reference data (in reference order), so the top row
  // showcases the whole org tree — including divisions with no committees or
  // models yet, so you can select one and register into it. Any extra buckets
  // committees roll up to (Company/Other) are appended after.
  orderedDivisions(groups, ref) {
    const refOrder = ((ref && ref.division) || []).map((d) => d.value);
    return refOrder.concat(Object.keys(groups).filter((dv) => !refOrder.includes(dv)));
  },

  // Repair the shared state if its division/committee no longer exists.
  normalize(committees, ref) {
    const s = this.state || { div: null, mrc: null };
    if (!s.div) { this.state = { div: null, mrc: null }; return; }
    const groups = this.groups(committees, ref);
    // A division is valid if it exists in reference data (even with no
    // committees) or is a synthetic Company/Other bucket.
    if (!this.orderedDivisions(groups, ref).includes(s.div)) {
      this.state = { div: null, mrc: null }; return;
    }
    if (s.mrc && !(groups[s.div] || []).some((c) => c.value === s.mrc)) {
      this.state = { div: s.div, mrc: null }; return;
    }
    this.state = { div: s.div, mrc: s.mrc };
  },

  // Two-tier tab strip: an "All" tab and the divisions on top; when a division is
  // active, its "All <div>" tab plus that division's committees appear below.
  html(committees, ref) {
    const state = this.state;
    const groups = this.groups(committees, ref);
    const divisions = this.orderedDivisions(groups, ref);
    if (!divisions.length) return "";
    const tab = (label, active, attr) =>
      '<button class="dtab' + (active ? " active" : "") + '" ' + attr + ">" + esc(label) + "</button>";
    const top = tab("All", !state.div, 'data-all="1"') +
      divisions.map((dv) => tab(dv, state.div === dv, 'data-div="' + esc(dv) + '"')).join("");
    let second = "";
    if (state.div && groups[state.div]) {
      second =
        '<div class="dtabs" style="margin-top:8px;border-top:1px solid var(--line);padding-top:8px">' +
        tab("All " + state.div, !state.mrc, 'data-divall="1"') +
        groups[state.div].map((c) =>
          tab(c.name || c.value, state.mrc === c.value, 'data-mrc="' + esc(c.value) + '"')).join("") +
        "</div>";
    }
    return '<div class="card" style="padding:8px 12px;margin-bottom:12px">' +
      '<div class="dtabs">' + top + "</div>" + second + "</div>";
  },

  // Wire selection clicks inside `container`; update the shared state and call
  // onChange() (no args) so the calling tab can re-render/re-filter.
  bind(container, committees, ref, onChange) {
    const set = (s) => { this.state = s; onChange(); };
    container.querySelectorAll("[data-all]").forEach((b) =>
      (b.onclick = () => set({ div: null, mrc: null })));
    container.querySelectorAll("[data-div]").forEach((b) =>
      (b.onclick = () => set({ div: b.getAttribute("data-div"), mrc: null })));
    container.querySelectorAll("[data-divall]").forEach((b) =>
      (b.onclick = () => set({ div: this.state.div, mrc: null })));
    container.querySelectorAll("[data-mrc]").forEach((b) =>
      (b.onclick = () => set({ div: this.state.div, mrc: b.getAttribute("data-mrc") })));
  },

  // Does a model/product `data` fall under the current selection?
  inScope(committees, ref, data) {
    const state = this.state;
    if (!state.div) return true;                        // "All"
    data = data || {};
    if (state.mrc) {
      const c = committees.find((x) => x.value === state.mrc);
      if (!c || c.level === "Company") return true;
      if (c.level === "Division") return data.division === c.scope_value;
      if (c.level === "Line of Business") return data.line_of_business === c.scope_value;
      return true;
    }
    if (state.div === "Company" || state.div === "Other") return true;  // synthetic buckets
    return data.division === state.div;                 // whole division
  },

  // The org assignment implied by the current selection, for pre-filling the
  // register modals: {division, line_of_business}. A Line of Business-level committee pins
  // both; a Division-level one (or the whole-division view) pins only the
  // division. Synthetic buckets (Company/Other) pin nothing.
  currentScope(committees, ref) {
    const s = this.state || {};
    let division = (s.div && s.div !== "Company" && s.div !== "Other") ? s.div : "";
    let line_of_business = "";
    if (s.mrc) {
      const c = (committees || []).find((x) => x.value === s.mrc);
      if (c && c.level === "Line of Business") {
        line_of_business = c.scope_value || "";
        division = this.divisionOf(c, ref) || division;
      } else if (c && c.level === "Division") {
        division = c.scope_value || division;
      }
    }
    return { division, line_of_business };
  },

  // The committee the MRC page should show for the current shared selection —
  // it always needs a concrete committee, unlike the list pages' "All" view.
  activeCommittee(committees, ref) {
    const has = (v) => committees.some((c) => c.value === v);
    if (this.state.mrc && has(this.state.mrc)) return this.state.mrc;
    if (this.state.div) {
      const g = this.groups(committees, ref)[this.state.div];
      if (g && g.length) return g[0].value;
    }
    return committees.length ? committees[0].value : null;
  },

  // Explicit committee pick (from the MRC page) → set both div and committee.
  selectCommittee(committees, ref, value) {
    const c = committees.find((x) => x.value === value);
    this.state = { div: c ? this.divisionOf(c, ref) : null, mrc: value };
  },
};
