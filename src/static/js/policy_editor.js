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

// The furniture every per-division, MRC-ratified editor draws: pick a division, and say
// where that division stands. Three editors run the `ratified_policy` lifecycle — Risk,
// ML Review Policy and Functional Groups — and each had built its own copy of the picker
// and its own copy of the badge, which is how the third one came to exist at all.
//
// What is genuinely per-policy is the SEED wording: what a division running on nothing
// yet is actually doing differs (the firm-wide seed, everything-asked-nothing-required,
// no groups at all). Draft and approved are the lifecycle itself and read the same
// wherever they appear, so they live here and stop drifting apart.
const PolicyEditor = {
  // `prefix` names the editor's element ids ("rp", "mrp", "fg"), because all three can be
  // mounted under the same Admin tab bar and a shared id would have them fighting over
  // each other's status line. `extra` is markup that sits beside the picker for an editor
  // that has something to put there (Risk hangs its Categorisation PDF link off it).
  header(prefix, divisions, current, extra) {
    const options = divisions.map((d) =>
      "<option" + (d === current ? " selected" : "") + ">" + esc(d) + "</option>").join("");
    return '<div class="row" style="justify-content:space-between;align-items:center">' +
      '<div class="row" style="align-items:center;gap:var(--space-4)">' +
      '<label class="muted" style="font-size:var(--size-xs)">Division</label>' +
      '<select id="' + prefix + '-div">' + options + "</select>" + (extra || "") +
      '</div><div id="' + prefix + '-status"></div></div>';
  },

  bindDivision(prefix, onChange) {
    const sel = document.getElementById(prefix + "-div");
    if (sel) sel.onchange = () => onChange(sel.value);
  },

  // `seed` is the one line each policy has to supply: what a division that has ratified
  // nothing is running on, which only that policy can say.
  status(prefix, state, seed) {
    const el = document.getElementById(prefix + "-status");
    if (!el) return;
    const map = {
      seed: '<span class="muted">' + seed + "</span>",
      draft: '<span class="badge" style="background:var(--amber)">Draft — awaiting MRC ' +
        "sign-off</span>",
      approved: '<span class="badge" style="background:var(--green)">Approved</span>' +
        '<span class="muted" style="margin-left:var(--space-3)">edits start a new ' +
        "draft</span>",
    };
    el.innerHTML = map[state] || "";
  },
};
