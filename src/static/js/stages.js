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
// The lifecycle stages a record may be in, per division.
//
// Two layers behind one registry: the institution's CATALOGUE, which its Company MRC
// ratifies, and each division's ratified choice from it. The server resolves the two
// together and hands back the stages already narrowed per division, so the rule
// "a division that has ratified nothing offers the whole catalogue" is written once,
// on the server, rather than a second time here.
//
// Its own file rather than another member of helpers.js, which has been split twice
// already for holding subjects that were never one (badges and documents on
// 2026-09-05, the risk policy on 2026-09-09).

const Stages = {
  _divisions: {},
  _labels: {},
  _catalogue: [],
  _states: {},
  // Re-read whenever a screen that uses the stages is entered, and the moment a
  // committee ratifies a change — NOT once at startup. A list loaded at page open goes
  // stale as soon as a catalogue is ratified, and the console stays open across exactly
  // that. Same rule, and the same reason, as Groups in helpers.js.
  async load() {
    try {
      const reg = await App.get("/api/lifecycle-stages");
      this._divisions = reg.divisions || {};
      this._labels = reg.labels || {};
      this._catalogue = reg.catalogue || [];
      this._states = reg.states || {};
    } catch (e) { /* no registry; every screen falls back to the field spec */ }
  },

  // The values a record in this division may be in, in the order its committee put
  // them. Empty where the registry has not loaded or the division is unknown, which is
  // the signal to fall back to the field spec's own options.
  forDivision(division) {
    const stages = division && this._divisions[division];
    if (stages && stages.length) return stages;
    // A record with no division — or one not on the admin list — still has to offer
    // something, and the catalogue is what every division starts from.
    return this._catalogue.map((s) => s.value);
  },

  // ``{value, label}`` for a picker: the record stores the value, the owner picks by
  // the word the institution ratified for it.
  options(division) {
    const shown = this._labelsFor(division);
    return this.forDivision(division).map((v) => ({ value: v, label: shown[v] || v }));
  },

  _labelsFor(division) {
    const own = division && this._labels[division];
    if (own && Object.keys(own).length) return own;
    const out = {};
    this._catalogue.forEach((s) => { out[s.value] = s.label || s.value; });
    return out;
  },

  // What to show for a stored value. One the division no longer uses resolves to the
  // value itself rather than to a blank: a record left behind by a re-cut should read
  // as needing attention, not as never having been set.
  labelFor(value, division) {
    if (!value) return "";
    return this._labelsFor(division)[value] || value;
  },

  // Whether a division is running on its own ratified list or on the whole catalogue.
  // Read by the Admin editor; a screen that only draws records does not care.
  stateFor(division) {
    return (this._states[division] || {}).state || "seed";
  },
};
