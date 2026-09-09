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

// What the selected region MEANS to the tabs that share the navigator.
//
// mrc_nav.js owns the bar itself — loading the org tree, drawing the two rows, and
// remembering the selection as the user moves between the MRC, Models, Products and
// Audit Trail tabs. This answers the question those tabs then ask of it: is this record
// in scope, which committee is the active one, and what does picking a committee do to
// the selection.
//
// The distinction that matters: scope is read straight off the ORG TREE — a record is
// in a division and a line of business — while a committee is ATTACHED to that tree
// rather than part of it. So a committee never decides whether a record is in scope; it
// is looked up FROM the scope. Collapsing the two is the bug this separation exists to
// make hard, because a Company-level committee governs everything and would drag every
// record into scope with it.
//
// bindLineOfBusinessPicker is here for the same reason: a register form's division /
// line-of-business pair is the same org tree, asked at a different moment.
//
// Assigns onto MrcNav; loads after mrc_nav.js.

Object.assign(MrcNav, {

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
});

// The Line of Business picker on a register form, filtered to the division chosen
// beside it and refilled whenever that changes.
//
// Unfiltered, the field would offer every line of business in the institution, and a
// record filed under another division's line would route to THAT division's committee —
// the opposite of what naming one is for. Lines of business belong to a division
// (`line_of_business` carries it), so the pair has to be chosen together.
//
// Shared because both register forms need it and neither is the natural owner; the
// third caller should not have to discover this twice.
function bindLineOfBusinessPicker(prefix, ref) {
  const division = document.getElementById(prefix + "-division");
  const lob = document.getElementById(prefix + "-line_of_business");
  if (!division || !lob) return;
  const fill = () => {
    const options = MrcNav.lobsForDivision(division.value, ref).map((l) => l.value);
    // Blank first and selected: a division with no lines of business, or a record
    // governed at division level, has no answer to give and must not be made to
    // invent one.
    lob.innerHTML = '<option value=""></option>' +
      options.map((o) => '<option value="' + esc(o) + '">' + esc(o) + "</option>").join("");
  };
  fill();
  division.onchange = fill;
}
