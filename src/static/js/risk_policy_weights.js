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

// Admin -> Risk -> Audit, below the settings: what each missing thing is worth here.
//
// The criticality weights of the completeness audit — one table each for fields,
// collections and documentation. Every row shows the firm-wide value, so a blank
// input reads as what it means; a division states only where it has decided
// differently, and that departure is printed in every completeness report.
//
// The catalogue (names, labels, firm-wide values, bounds) comes from the server with
// the policy, built from the same sections the validator checks, so this never
// offers a name the committee could not ratify.
const RiskPolicyWeights = {
  // ``policy`` is the draft being edited and ``onChange`` saves it, exactly as for
  // the settings above, so the weights reach the MRC in the same proposal.
  render(host, policy, catalogue, onChange) {
    if (!host || !catalogue) return;
    const audit = policy.audit || (policy.audit = {});
    host.innerHTML =
      '<h4 style="margin-top:var(--space-9)">Criticality weights</h4>' +
      '<p class="muted" style="font-size:var(--size-xs)">How much each missing item counts ' +
      "before escalation, from " + catalogue.min.toFixed(2) + " to " +
      catalogue.max.toFixed(2) + ". Blank means the firm-wide value. Anything set here " +
      "is listed against this division in every completeness report.</p>" +
      catalogue.sections.map((s) => this._section(s, audit[s.policy_key] || {})).join("");
    this._bind(host, audit, catalogue, onChange);
  },

  _section(section, set) {
    const changed = section.rows.filter((r) => set[r.name] !== undefined).length;
    return '<details style="margin-top:var(--space-4)"><summary>' + esc(section.label) +
      " weights " + '<span class="muted">(' + section.rows.length + " items" +
      (changed ? ", " + changed + " set by this division" : "") + ")</span></summary>" +
      '<table style="table-layout:fixed;width:100%"><colgroup><col style="width:60%">' +
      '<col style="width:20%"><col style="width:20%"></colgroup>' +
      "<thead><tr><th>" + esc(section.label) + "</th><th>Firm-wide</th>" +
      "<th>This division</th></tr></thead><tbody>" +
      section.rows.map((r) =>
        "<tr><td>" + esc(r.label) + "</td>" +
        '<td class="muted">' + r.firm.toFixed(2) + "</td>" +
        '<td><input data-weight="' + esc(section.policy_key) + '" data-name="' + esc(r.name) +
        '" data-label="' + esc(r.label) + '" value="' +
        esc(set[r.name] === undefined ? "" : set[r.name]) +
        '" placeholder="' + r.firm.toFixed(2) + '" style="width:100%;text-align:right">' +
        "</td></tr>").join("") +
      "</tbody></table></details>";
  },

  _bind(host, audit, catalogue, onChange) {
    host.querySelectorAll("[data-weight]").forEach((input) => {
      input.onchange = () => {
        const key = input.getAttribute("data-weight");
        const name = input.getAttribute("data-name");
        const set = audit[key] || (audit[key] = {});
        const text = input.value.trim();
        // Cleared means the firm-wide value: the name is removed, not stored as the
        // firm's number, so a later change to the firm-wide table still reaches it.
        if (!text) { delete set[name]; onChange(); return; }
        const value = Number(text);
        if (!isFinite(value) || value < catalogue.min || value > catalogue.max) {
          App.toast(input.getAttribute("data-label") + " must be a weight from " +
                    catalogue.min.toFixed(2) + " to " + catalogue.max.toFixed(2), "error");
          input.value = set[name] === undefined ? "" : set[name];
          return;
        }
        set[name] = value;
        onChange();
      };
    });
  },
};
