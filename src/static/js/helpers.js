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
// What the institution decided, as the server resolved it.
//
// Two registries loaded once at startup — the theme's colour tokens and the functional
// groups each division's MRC has ratified — plus the two primitive formatters
// everything else builds on. The risk-policy registry was the third and is now
// policy_registry.js, which loads immediately after this file.
//
// Nothing here names a colour: a badge asks for a token and the served stylesheet
// resolves it, so recolouring the console is a config change and never a JavaScript
// one. main.js waits on load() before the first render, so the maps are populated by
// the time anything is drawn. If the fetch fails the console still renders — every
// badge falls back to whatever its caller does with a null colour, which is the same
// dash an unrated record has always shown.
//
// How a record's state is turned into a badge is badges.js; documents are
// doc_links.js. Both load after this file and depend on the registries here.

// Which token a status is drawn in, from config/theme.py via /api/theme. Nothing here
// names a colour: a badge asks for the token and the served stylesheet resolves it, so
// recolouring the console is a config change and never a JavaScript one.
//
// main.js waits on load() before the first render, so the maps are populated by the
// time anything is drawn. If the fetch fails the console still renders — every badge
// simply falls back to whatever its caller does with a null colour, which is the same
// dash an unrated record has always shown.
const Theme = {
  _tokens: {},
  _status: {},
  _defaults: {},
  async load() {
    try {
      const theme = await App.get("/api/theme");
      this._tokens = theme.tokens || {};
      this._status = theme.status_colours || {};
      this._defaults = theme.status_defaults || {};
      // The graph's drawing vocabulary travels with the colours it draws with.
      this._lineage = theme.lineage_nodes || {};
    } catch (e) { /* the stylesheet still carries the token values */ }
  },
  // A token's literal value. Needed where the colour is manipulated rather than just
  // used — the heatmap appends two hex digits of alpha to shade a cell, and "var(--red)22"
  // means nothing. Those sites therefore require hex-valued tokens; a tint() built on
  // color-mix() would lift that constraint, at the cost of changing the shade slightly.
  value(token) { return this._tokens[token]; },
  // A token as CSS refers to it. Inline styles resolve var() normally; SVG
  // presentation attributes do NOT, so anything drawing into a canvas must use a
  // class or a style attribute rather than fill="..." with one of these.
  ref(token) { return token ? "var(--" + token + ")" : null; },
  // The colour a value is drawn in, or null when the domain has no default and the
  // value is unrecognised — callers render that as a dash rather than inventing one.
  colour(domain, value) {
    return this.ref(this._token(domain, value));
  },
  // As colour(), but the literal value — for the callers that sit alongside policy
  // colours (raw hex out of the division's policy) and must be the same kind of thing.
  hex(domain, value) {
    const token = this._token(domain, value);
    return token ? this.value(token) : null;
  },
  _token(domain, value) {
    const map = this._status[domain] || {};
    return map[String(value)] || this._defaults[domain] || null;
  },
};

// Human-readable file size.
function fmtSize(bytes) {
  if (bytes === null || bytes === undefined) return "—";
  const kb = bytes / 1024;
  return kb < 1024 ? kb.toFixed(1) + " KB" : (kb / 1024).toFixed(1) + " MB";
}

// An uploaded_at stamp shown to the minute (UTC, as stored by add_document):
// "2026-07-30T11:13:28+00:00" → "2026-07-30 11:13". Documents are retained per
// upload, so the time — not just the date — is what distinguishes one dated
// monitoring result from the next when several land on the same day.
function fmtTimestamp(iso) {
  const s = String(iso || "");
  if (!s) return "—";
  return s.slice(0, 16).replace("T", " ");
}

// The functional-group registry: every division's ratified groups, loaded once at
// startup beside the risk policy and resolved per record's division.
//
// A record stores a group's ID and screens show its NAME, so this is what stands
// between the two. There is no seed and no fallback: a division whose MRC has ratified
// nothing has no groups, and a record there can be filed under none — which is the
// honest state, not a gap to paper over with a default.
const Groups = {
  _divisions: {},
  _states: {},
  // Re-read whenever a screen that uses the groups is entered, and the moment a
  // committee ratifies a change -- NOT once at startup. A list loaded at page open
  // goes stale as soon as an administrator adds a group and its MRC signs it off, and
  // the console stays open across exactly that: the picker kept offering the old list
  // and the register kept grouping by it, with nothing on screen to say why. The
  // registers re-fetch their field specs for the same reason ("Always re-fetch so
  // admin changes to the reference menus show up promptly", Inventory.specs).
  async load() {
    try {
      const reg = await App.get("/api/functional-groups");
      this._divisions = reg.divisions || {};
      this._states = reg.states || {};
    } catch (e) { /* no groups; every record shows as unfiled */ }
  },
  // A division's groups in the order its committee arranged them — the order is part of
  // what was ratified, so nothing re-sorts it.
  forDivision(division) { return (division && this._divisions[division]) || []; },
  // ``{value: id, label: name}`` for a picker: the record stores the id, the owner
  // picks by the name.
  options(division) {
    return this.forDivision(division).map((g) => ({ value: g.id, label: g.name || g.id }));
  },
  // What to show for a stored id. An id the division no longer defines resolves to the
  // id itself rather than to a blank: a record filed under a group that has since gone
  // should read as needing attention, not as never having been filed.
  nameFor(id, division) {
    if (!id) return "";
    const found = this.forDivision(division).find((g) => g.id === id);
    return found ? (found.name || found.id) : id;
  },
  // Whether the division's groups are the ones its MRC signed off, or a draft is
  // outstanding — the same notice the risk policy carries, for the same reason.
  state(division) { return (division && this._states[division]) || null; },
};
