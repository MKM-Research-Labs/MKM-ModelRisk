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

// The input control for one field spec — the single place a form decides what widget a
// field gets and which options it offers.
//
// It lived in inventory.js, which made it look like a models-screen concern. It is not:
// every register form, add-a-row form and inline editor in the console builds its
// controls through this, so a division whose policy renames a band has to be answered
// here once rather than per screen.
//
// The three field groups named at the top are the ones whose options do NOT come from
// the field spec. Materiality and complexity come from the DIVISION's risk policy, the
// functional group from what that division's MRC has ratified, and the lifecycle stage
// from the division's ratified choice out of the institution's catalogue — so the same
// field offers different choices on two records that differ only by division. The risk
// dimensions fall back to the spec's constant options where the division has no policy
// of its own; the stages fall back to the spec's options (the catalogue default) where
// the registry has nothing for the division, before it has loaded or for an unknown one.
// They are named as constants for the reason the file is separate: a field key spelled
// out at each use is a field key that gets missed at one of them.
//
// Loads after policy_registry.js and helpers.js, whose registries it reads. Stages is
// read at call time, so stages.js loads after this file rather than before it.

// Risk choice fields whose options come from a division's policy, not the field spec.
const POLICY_DIMENSION_FIELD = { materiality: "materiality", complexity: "complexity" };
// Likewise, but from the division's ratified functional groups rather than its risk
// policy. Named here for the same reason the dimensions are: a field key spelled out
// at each use is a field key that gets missed at one of them.
const FUNCTIONAL_GROUP_FIELD = "functional_group";
// And the lifecycle stage, from the division's ratified choice out of the institution's
// catalogue (stages.js). Read at call time, so stages.js need not load before this.
const LIFECYCLE_STAGE_FIELD = "lifecycle_stage";

// Build the input control for one field spec. For the risk fields the option list comes
// from the entity's DIVISION policy (falling back to the spec's constant options / 1-3).
function inputControl(id, spec, division) {
  // The record stores a group's ID and the owner picks by its NAME, so this is a
  // value/label select rather than a list of words — the same shape as the tier band
  // picker below, for the same reason. A division whose MRC has ratified nothing has
  // no groups, and the control says so rather than offering an empty dropdown that
  // looks broken.
  if (spec.key === FUNCTIONAL_GROUP_FIELD) {
    const groups = Groups.options(division);
    if (!groups.length) {
      return '<select id="' + id + '" disabled><option value="">' +
        "No groups ratified for this division</option></select>";
    }
    const opts = '<option value=""></option>' + groups.map((g) =>
      '<option value="' + esc(g.value) + '">' + esc(g.label) + "</option>").join("");
    return '<select id="' + id + '">' + opts + "</select>";
  }
  if (spec.type === "choice") {
    let options = spec.options;
    if (spec.key === "rag_rating") options = Policy.ratingNames(division) || options;
    // The stages this division's committee agreed to use, narrowed from the
    // institution's catalogue. The spec's own options are the catalogue default and
    // stand in until the registry has loaded, so the control is never empty.
    else if (spec.key === LIFECYCLE_STAGE_FIELD) {
      const stages = Stages.options(division);
      if (stages.length) {
        const opts = ['<option value=""></option>'].concat(stages.map((s) =>
          '<option value="' + esc(s.value) + '">' + esc(s.label) + "</option>")).join("");
        return '<select id="' + id + '">' + opts + "</select>";
      }
    }
    else if (POLICY_DIMENSION_FIELD[spec.key]) {
      options = Policy.dimensionBandNames(POLICY_DIMENSION_FIELD[spec.key], division) || options;
    }
    // A status vocabulary submits the STORED value and shows the label beside it,
    // so renaming a status changes every screen without moving anything on record.
    const shown = spec.option_labels || {};
    const opts = ["", ...options].map((o) =>
      '<option value="' + esc(o) + '">' + esc(shown[o] || o) + "</option>").join("");
    return '<select id="' + id + '">' + opts + "</select>";
  }
  if (spec.type === "tier") {
    // Pick by the division's Mission-Criticality band NAME; the option value is the
    // band score the model actually stores. Fallback to bare tiers 1-3.
    const bands = Policy.missionOptions(division);
    if (bands) {
      const opts = '<option value=""></option>' + bands.map((b) =>
        '<option value="' + esc(b.value) + '">' + esc(b.label) + "</option>").join("");
      return '<select id="' + id + '">' + opts + "</select>";
    }
    const opts = ["", 1, 2, 3].map((o) => "<option>" + esc(o) + "</option>").join("");
    return '<select id="' + id + '">' + opts + "</select>";
  }
  // Several of the options at once (a person's roles). The stored value is a list, so the
  // control is a real multi-select rather than a comma-separated text box; each option
  // carries the spec's explanation as its tooltip, so an administrator granting a role can
  // see what it means.
  if (spec.type === "multichoice") {
    const explain = spec.explanations || {};
    const shown = spec.option_labels || {};
    const opts = (spec.options || []).map((o) =>
      '<option value="' + esc(o) + '"' +
      (explain[o] ? ' title="' + esc(explain[o]) + '"' : "") + ">" + esc(shown[o] || o) +
      "</option>").join("");
    // A multi-select has no intrinsic width, so it collapsed to its content on a
    // narrow viewport — a roles picker too cramped to read.
    return '<select id="' + id + '" multiple style="min-width:180px" size="' +
      Math.min((spec.options || []).length, 6) + '">' + opts + "</select>";
  }
  if (spec.type === "date") {
    // "When was this done" defaults to today, because it is nearly always today and a
    // blank date is how a register ends up full of undateable rows. Opt-in per field:
    // a due date or an expected completion must NOT default to today.
    // Local date, not toISOString(), which is UTC and lands on yesterday all evening
    // in the western hemisphere and on tomorrow in the east.
    const today = spec.default_today
      ? ' value="' + new Date().toLocaleDateString("en-CA") + '"' : "";
    return '<input id="' + id + '" type="date"' + today + ">";
  }
  if (spec.type === "textarea") {
    return '<textarea id="' + id + '" rows="4" style="width:100%;resize:vertical"></textarea>';
  }
  return '<input id="' + id + '">';
}
