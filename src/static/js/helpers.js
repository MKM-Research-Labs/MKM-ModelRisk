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
// Two registries loaded once at startup — the theme's colour tokens and the risk-policy
// registry — plus the two primitive formatters everything else builds on.
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

// The risk-policy registry: the firm-wide seed + each division's live policy, loaded
// once at startup. Colours, labels and ordering resolve per a model's division and
// fall back to the seed, then to the built-in palette above.
const Policy = {
  _seed: null,
  _divisions: {},
  _states: {},
  async load() {
    try {
      const reg = await App.get("/api/risk-policy");
      this._seed = reg.seed || null;
      this._divisions = reg.divisions || {};
      this._states = reg.states || {};
    } catch (e) { /* keep the built-in fallbacks */ }
  },
  // A division's policy lifecycle: {state: seed|draft|approved, approved_at}. The bands
  // everywhere else are the APPROVED ones; "draft" means the admin has since edited the
  // policy and it is waiting on the division's MRC.
  state(division) { return (division && this._states[division]) || null; },
  _for(division) { return (division && this._divisions[division]) || this._seed; },
  ratingColour(name, division) {
    const p = this._for(division);
    const r = p && (p.risk_ratings || []).find((x) => x.name === name);
    return r ? r.colour : null;
  },
  // Ratings are ordered most-severe first, so the list index is the sort key.
  ratingOrder(name, division) {
    const p = this._for(division);
    if (!p) return null;
    const i = (p.risk_ratings || []).findIndex((x) => x.name === name);
    return i < 0 ? null : i;
  },
  // Option lists for the risk fields, from the division's policy (null when not loaded,
  // so callers fall back to the field spec's constant options).
  ratingNames(division) {
    const p = this._for(division);
    return p ? (p.risk_ratings || []).map((r) => r.name) : null;
  },
  // The full ratings ({name, colour, explanation, score}) in policy order, for the surfaces
  // that count or colour every rating rather than just naming them.
  ratings(division) {
    const p = this._for(division);
    return p ? (p.risk_ratings || []) : null;
  },
  dimensionBandNames(key, division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions[key];
    return dim ? (dim.bands || []).map((b) => b.name) : null;
  },
  // A dimension's full bands ({name, colour, explanation, score}) — what the Admin editor
  // defines, for the surfaces that show a band the way Admin does rather than by name.
  dimensionBands(key, division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions[key];
    return dim ? (dim.bands || []) : null;
  },
  // The band a level dimension (Materiality/Complexity) names, for its colour and the
  // admin's explanation of what that level means.
  band(key, name, division) {
    const bands = this.dimensionBands(key, division) || [];
    return bands.find((b) => b.name === name) || null;
  },
  tierScores(division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions.mission_criticality;
    return dim ? (dim.bands || []).map((b) => b.score) : null;
  },
  // A dimension's admin-defined display label (so a renamed dimension shows through).
  dimensionLabel(key, division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions[key];
    return (dim && dim.label) || null;
  },
  // What to call a dimension, always. A division renames one and every screen that
  // asks follows; nothing anywhere else may spell out "Materiality" or "Complexity",
  // because the day a division renames one, every such spelling becomes a lie. Where
  // no policy has been drafted yet the key itself is humanised — derived from the
  // structure rather than a name somebody typed into the source.
  dimensionName(key, division) {
    return this.dimensionLabel(key, division) ||
      key.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
  },
  // Mission-Criticality bands as {value: score, label: name} for a select — the model
  // stores the score, but the owner picks by the admin-defined band name.
  missionOptions(division) {
    const p = this._for(division);
    const bands = (((p || {}).dimensions || {}).mission_criticality || {}).bands || [];
    return bands.length ? bands.map((b) => ({ value: b.score, label: b.name })) : null;
  },
  // The Mission-Criticality band a tier selects (band score == tier), clamped like the
  // backend: out-of-range → nearest, missing → most conservative (first) band.
  mcBand(tier, division) {
    const p = this._for(division);
    const bands = (((p || {}).dimensions || {}).mission_criticality || {}).bands || [];
    if (!bands.length) return null;
    const byScore = {}; bands.forEach((b) => { byScore[b.score] = b; });
    const t = parseInt(tier, 10);
    if (byScore[t]) return byScore[t];
    if (isNaN(t)) return bands[0];
    const scores = bands.map((b) => b.score);
    return byScore[Math.min(Math.max(t, Math.min.apply(null, scores)), Math.max.apply(null, scores))] || null;
  },
  // The rating a subject's cell resolves to, repeating the risk engine's lookup
  // (model_inventory/risk.py): Mission-Criticality band → Materiality|Complexity → rating.
  // Null when either axis is unset, so the subject is not on the heatmap at all.
  gridRating(tier, materiality, complexity, division) {
    if (!materiality || !complexity) return null;
    const p = this._for(division);
    const band = this.mcBand(tier, division);
    if (!p || !band) return null;
    return ((p.grid || {})[band.name] || {})[materiality + "|" + complexity] || null;
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
