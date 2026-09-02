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

  // --- what the selection means to the tabs that share the bar ---
  //
  // Scope is read straight off the org tree now: a record is in a division, or in
  // a line of business, and no committee stands between the two. So `normalize`,
  // `inScope` and `currentScope` no longer need `committees` — they still take it,
  // unused, so the six call sites across the list tabs read alike. The two
  // committee helpers at the end genuinely do use it.

  // Does a model/product `data` fall under the current selection?
  inScope(committees, ref, data) {
    const state = this.state;
    if (!state.div) return true;                        // "All"
    data = data || {};
    if (state.lob) return data.line_of_business === state.lob;
    return data.division === state.div;                 // whole division
  },

  // The org assignment implied by the current selection, for pre-filling the
  // register modals: {division, line_of_business}.
  currentScope(committees, ref) {
    const s = this.state || {};
    return { division: s.div || "", line_of_business: s.lob || "" };
  },

  // The committee the MRC page falls back to when it needs one concrete
  // committee and the user has not picked from its list. Resolved in priority
  // order: the committee for the selected line of business, then the one for the
  // selected division, then a Company-level one, then whatever exists.
  activeCommittee(committees, ref) {
    const s = this.state || {};
    const at = (level, value) =>
      (committees || []).find((c) => c.level === level && c.scope_value === value);
    let c = s.lob && at("Line of Business", s.lob);
    if (!c) c = s.div && at("Division", s.div);
    if (!c) c = (committees || []).find((x) => x.level === "Company");
    if (c) return c.value;
    return committees && committees.length ? committees[0].value : null;
  },

  // An explicit committee pick → move the org selection to that committee's own
  // scope, so the rest of the console follows it.
  selectCommittee(committees, ref, value) {
    const c = (committees || []).find((x) => x.value === value);
    if (!c) { this.state = { div: null, lob: null }; return; }
    if (c.level === "Line of Business") {
      const lob = ((ref && ref.line_of_business) || []).find((l) => l.value === c.scope_value);
      this.state = { div: (lob && lob.division) || null, lob: c.scope_value || null };
    } else if (c.level === "Division") {
      this.state = { div: c.scope_value || null, lob: null };
    } else {
      this.state = { div: null, lob: null };
    }
  },
};
