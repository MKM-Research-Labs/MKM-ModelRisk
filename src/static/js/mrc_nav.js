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

// The two-tier MRC region navigator (divisions on the top row, their committees
// below) shared by the MRC, Models, Products and Audit Trail tabs. The selection
// lives here on `state` so the chosen region persists as the user moves between
// those tabs. state = {div, mrc}: both null = "All"; a division with mrc null =
// the whole division; div + mrc = one committee's scope.
const MrcNav = {
  state: { div: null, mrc: null },

  // The division a committee rolls up to: a Division-level MRC's scope is itself
  // a division; a Department-level one inherits its department's division;
  // Company-level (or unresolved) MRCs share a "Company" bucket.
  divisionOf(c, ref) {
    if (!c) return "Company";
    if (c.level === "Division") return c.scope_value || "Company";
    if (c.level === "Department") {
      const dept = ((ref && ref.department) || []).find((d) => d.value === c.scope_value);
      return (dept && dept.division) || "Other";
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

  // Divisions in reference order first, then any extra buckets (Company/Other).
  orderedDivisions(groups, ref) {
    const refOrder = ((ref && ref.division) || []).map((d) => d.value).filter((dv) => groups[dv]);
    return refOrder.concat(Object.keys(groups).filter((dv) => !refOrder.includes(dv)));
  },

  // Repair the shared state if its division/committee no longer exists.
  normalize(committees, ref) {
    const s = this.state || { div: null, mrc: null };
    if (!s.div) { this.state = { div: null, mrc: null }; return; }
    const groups = this.groups(committees, ref);
    if (!groups[s.div]) { this.state = { div: null, mrc: null }; return; }
    if (s.mrc && !groups[s.div].some((c) => c.value === s.mrc)) {
      this.state = { div: s.div, mrc: null }; return;
    }
    this.state = { div: s.div, mrc: s.mrc };
  },

  // Two-tier tab strip: an "All" tab and the divisions on top; when a division is
  // active, its "All <div>" tab plus that division's committees appear below.
  html(committees, ref) {
    if (!committees.length) return "";
    const state = this.state;
    const groups = this.groups(committees, ref);
    const tab = (label, active, attr) =>
      '<button class="dtab' + (active ? " active" : "") + '" ' + attr + ">" + esc(label) + "</button>";
    const top = tab("All", !state.div, 'data-all="1"') +
      this.orderedDivisions(groups, ref)
        .map((dv) => tab(dv, state.div === dv, 'data-div="' + esc(dv) + '"')).join("");
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
      if (c.level === "Department") return data.department === c.scope_value;
      return true;
    }
    if (state.div === "Company" || state.div === "Other") return true;  // synthetic buckets
    return data.division === state.div;                 // whole division
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
