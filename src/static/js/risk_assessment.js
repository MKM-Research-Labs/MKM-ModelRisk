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

// The Risk Assessment surface shared by the model and product Risk tabs: how a risk
// dimension is labelled, displayed and picked, which policy those bands come from, and the
// Dimension / Rating / Rationale table itself. It mirrors Admin -> Risk deliberately — the
// admin defines the vocabulary there, and the owner picks from it (and justifies the pick)
// here — so the two read as one system rather than two vocabularies for the same thing.

// Risk-assessment field labels follow the division's policy: "Tier" shows as the
// Mission-Criticality dimension's admin-defined label, and Materiality/Complexity
// reflect a rename too. Falls back to the field spec's own label.
const RISK_FIELD_DIMENSION = {
  tier: "mission_criticality", materiality: "materiality", complexity: "complexity",
};
// Each dimension's rationale row is labelled after the dimension it justifies, so a
// renamed dimension renames its justification too ("Tier rationale" was left behind when
// Tier became the Mission-Criticality band name).
const RISK_RATIONALE_DIMENSION = {
  tier_rationale: "mission_criticality", materiality_rationale: "materiality",
  complexity_rationale: "complexity",
};
function riskFieldLabel(f, division) {
  const dim = RISK_FIELD_DIMENSION[f.key];
  if (dim) { const l = Policy.dimensionLabel(dim, division); if (l) return l; }
  const rationale = RISK_RATIONALE_DIMENSION[f.key];
  if (rationale) {
    const l = Policy.dimensionLabel(rationale, division);
    if (l) return l + " rationale";
  }
  return f.label;
}

// A risk dimension's set value, shown the way Admin defines the band: its colour and name
// as a pill, then the admin's own explanation of what that band means. Mission Criticality
// already reads this way; Materiality and Complexity used to show a bare "High".
function bandDisplay(f, value, division) {
  const key = RISK_FIELD_DIMENSION[f.key];
  const band = key ? Policy.band(key, value, division) : null;
  if (!band) return fieldDisplay(value);
  return '<span class="badge" style="background:' + (band.colour || Theme.value("grey")) + '">' +
    esc(band.name) + "</span>" +
    (band.explanation ? ' <span class="muted">' + esc(band.explanation) + "</span>" : "");
}

// The bands an owner picks between for one risk dimension: what the record stores, plus
// the name/colour/explanation the admin gave the band. Null when the division's policy
// defines none, so the caller falls back to the plain control.
function dimensionChoices(f, division) {
  const key = RISK_FIELD_DIMENSION[f.key];
  if (!key) return null;
  const bands = Policy.dimensionBands(key, division);
  if (!bands || !bands.length) return null;
  // Mission Criticality stores the band SCORE (the legacy tier integer); Materiality and
  // Complexity store the band name.
  return bands.map((b) => ({ value: f.type === "tier" ? b.score : b.name, name: b.name,
                             colour: b.colour, explanation: b.explanation }));
}

// A dimension picker shaped like the Admin band table — colour, name and the band's own
// explanation — so the owner chooses from the same vocabulary the admin defined, with the
// admin's reasoning in front of them instead of a bare list of words. Returns null when
// the division has no bands (caller falls back to inputControl). The chosen value sits on
// a hidden input carrying the caller's id, so the existing save paths — which read
// ``.value`` and listen for ``change`` — work unchanged.
function bandPicker(id, f, division, current) {
  const choices = dimensionChoices(f, division);
  if (!choices) return null;
  const chosen = (current === null || current === undefined) ? "" : String(current);
  const opts = choices.map((c) => {
    const on = String(c.value) === chosen;
    return '<label class="bandopt' + (on ? " on" : "") + '">' +
      '<input type="radio" name="' + esc(id) + '-band" value="' + esc(c.value) + '"' +
      (on ? " checked" : "") + ">" +
      '<span class="bswatch" style="background:' + esc(c.colour || Theme.value("grey")) + '"></span>' +
      '<span class="bname">' + esc(c.name) + "</span>" +
      '<span class="bexpl">' + esc(c.explanation || "") + "</span></label>";
  }).join("");
  return '<input type="hidden" id="' + esc(id) + '" value="' + esc(chosen) + '">' +
    '<div class="bandpick" data-bandpick="' + esc(id) + '">' + opts + "</div>";
}

// Wire a rendered bandPicker: keep the hidden input in step and fire ``change`` on it, so
// a caller that auto-saves on change behaves exactly as it does for a <select>.
function bindBandPicker(id) {
  const host = document.querySelector('[data-bandpick="' + id + '"]');
  if (!host) return;
  const input = document.getElementById(id);
  host.querySelectorAll("input[type=radio]").forEach((radio) => {
    radio.onchange = () => {
      input.value = radio.value;
      host.querySelectorAll(".bandopt").forEach((l) => l.classList.toggle("on", l.contains(radio)));
      input.dispatchEvent(new Event("change"));
    };
  });
}

// Which policy the bands on a subject's Risk tab come from, mirroring the state chip in
// Admin → Risk. A subject is categorised against its division's APPROVED policy, so an
// admin edit that is still a draft offers no new bands here — saying so is the difference
// between "the console ignored my change" and "my change is with the MRC".
function policyNotice(division) {
  const s = Policy.state(division);
  if (!s) return "";
  const where = esc(division) + " risk policy";
  const chip = (colour, text) => '<span class="badge" style="background:' + colour + '">' +
    esc(text) + "</span> ";
  if (s.state === "draft") {
    return '<div class="policy-note draft">' + chip("var(--amber)", "Draft with the MRC") +
      "The bands below are the approved <b>" + where + "</b>" +
      (s.approved_at ? " (ratified " + esc(s.approved_at) + ")" : "") +
      ". A newer draft is awaiting this division's MRC — its bands become available here " +
      "once the committee signs it off (Admin &rarr; Risk).</div>";
  }
  if (s.state === "approved") {
    return '<div class="policy-note">The bands below come from the approved <b>' + where +
      "</b>" + (s.approved_at ? ", ratified " + esc(s.approved_at) : "") +
      " (Admin &rarr; Risk).</div>";
  }
  return '<div class="policy-note">The bands below come from the firm-wide seed policy — ' +
    esc(division) + " has not ratified its own yet (Admin &rarr; Risk).</div>";
}

// The Risk Assessment table. One row per risk dimension in three columns — the dimension,
// the band the owner picked, and the owner's justification for picking it — so a reviewer
// reads a choice and its reasoning on one line instead of hunting down alternating rows.
// The three dimensions are structural (the heatmap is Materiality x Complexity per
// Mission-Criticality band, and the Admin editor defines exactly these three); everything
// the division CALLS them, and every band inside them, comes from its policy.
const RISK_TABLE_ROWS = [
  { dimension: "tier", rationale: "tier_rationale" },
  { dimension: "materiality", rationale: "materiality_rationale" },
  { dimension: "complexity", rationale: "complexity_rationale" },
];

// ``opts``: {data, division, spec(key) -> field spec, editLink(key) -> html, ratingBadge}.
// Each editable cell carries ``row-<key>``, the id the inline editors already look up, so
// editing works the same in a cell as it did in a row.
function riskAssessmentTable(opts) {
  const d = opts.data || {};
  const cell = (key, inner) =>
    '<td id="row-' + key + '" class="rt-cell">' + inner + opts.editLink(key) + "</td>";
  const rows = RISK_TABLE_ROWS.map((r) => {
    const f = opts.spec(r.dimension);
    if (!f) return "";
    // Mission Criticality stores a band score, so it resolves through the tier badge;
    // the level dimensions resolve by band name.
    const value = r.dimension === "tier"
      ? ((d.tier || d.tier === 0)
          ? tierBadge(d.tier, opts.division) + ' <span class="muted">' +
            esc(tierFullLabel(d.tier, opts.division)) + "</span>"
          : '<span class="muted">&mdash;</span>')
      : bandDisplay(f, d[r.dimension], opts.division);
    const rationale = opts.spec(r.rationale)
      ? cell(r.rationale, fieldDisplay(d[r.rationale]))
      : "<td></td>";
    return "<tr><th>" + esc(riskFieldLabel(f, opts.division)) + "</th>" +
      cell(r.dimension, value) + rationale + "</tr>";
  }).join("");
  // The rating the three choices land on. The committee sets it, so only its rationale is
  // editable here — the cell itself is what the heatmap below says.
  const overall = "<tr><th>Overall rating</th><td>" +
    (opts.ratingBadge || '<span class="muted">&mdash;</span>') + "</td>" +
    (opts.spec("rating_rationale")
      ? cell("rating_rationale", fieldDisplay(d.rating_rationale))
      : "<td></td>") + "</tr>";
  return '<table class="risk-assess"><thead><tr><th>Dimension</th><th>Rating</th>' +
    "<th>Rationale</th></tr></thead><tbody>" + rows + overall + "</tbody></table>";
}

// A one-line heads-up for a LIST: which of the divisions on it have a categorisation draft
// waiting on their MRC. A list speaks the approved vocabulary, so a band renamed in Admin
// but not yet ratified simply does not appear here — which reads as the console having
// ignored the edit. The subject Risk tabs say this per division; a list says it once.
function policyDraftNotice(divisions) {
  const pending = [...new Set((divisions || []).filter(Boolean))]
    .filter((d) => ((Policy.state(d) || {}).state) === "draft");
  if (!pending.length) return "";
  return '<div class="policy-note draft"><span class="badge" style="background:var(--amber)">' +
    "Draft with the MRC</span> " + esc(pending.join(", ")) +
    (pending.length > 1 ? " have" : " has") + " a risk-policy draft awaiting sign-off. This " +
    "list shows the approved bands and ratings until the committee ratifies it " +
    "(Admin &rarr; Risk).</div>";
}
