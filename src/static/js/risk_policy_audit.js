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

// Admin -> Risk -> Audit: what the completeness audit scores this division against.
//
// These numbers decide every completeness figure and every remediation deadline for
// the division's models — the thing a regulator asks to see the basis for — so they
// sit on the policy its MRC ratifies rather than in the platform's source. Each is
// optional: leave one blank and the firm-wide value stands.
//
// Kept in its own file because the policy editor is already long, and because this
// panel is a flat list of numbers with nothing in common with the band tables.
const AUDIT_SETTINGS = [
  { key: "acceptable_at", label: "Acceptable at", percent: true,
    hint: "A record at or above this completeness is reported as acceptable." },
  { key: "conditional_at", label: "Conditional at", percent: true,
    hint: "Below the acceptable line but at or above this is conditional; under it, unacceptable." },
  { key: "untiered_weight", label: "Untiered weight",
    hint: "Applied where a record carries no Mission Criticality band. Above the lowest tier " +
          "on purpose: the missing band is itself a reason to look." },
  { key: "unrated_multiplier", label: "Unrated multiplier",
    hint: "Applied where a record has no risk rating, so an unrated model escalates rather " +
          "than escaping the ranking." },
  { key: "event_pressure_per_event", label: "Event pressure, each",
    hint: "Added per operational failure in the rolling window." },
  { key: "event_pressure_cap", label: "Event pressure, capped at",
    hint: "The ceiling on that pressure, so one bad year cannot dominate the ranking." },
  { key: "broken_doc_escalation", label: "Broken document escalation",
    hint: "Applied to a document the record claims to hold but which cannot be retrieved." },
];

const RiskPolicyAudit = {
  // ``policy`` is the draft being edited; ``onChange`` saves it as the editor does
  // for every other change, so this lands in the same draft the MRC signs off.
  render(host, policy, onChange) {
    const audit = policy.audit || (policy.audit = {});
    host.innerHTML =
      '<p class="muted" style="font-size:11px">What the completeness audit scores this ' +
      "division against. Blank means the firm-wide value, so a division only states what " +
      "it has decided differently. Percentages are written as percentages; the rest are " +
      "multipliers, where 1 leaves a score unchanged.</p>" +
      '<table style="table-layout:fixed;width:100%"><colgroup><col style="width:26%">' +
      '<col style="width:14%"><col style="width:60%"></colgroup>' +
      "<thead><tr><th>Setting</th><th>Value</th><th>What it does</th></tr></thead><tbody>" +
      AUDIT_SETTINGS.map((s) => {
        const raw = audit[s.key];
        const shown = raw === undefined || raw === null || raw === ""
          ? "" : (s.percent ? Math.round(raw * 1000) / 10 : raw);
        return "<tr><td>" + esc(s.label) + "</td>" +
          '<td><input data-audit="' + s.key + '" value="' + esc(shown) +
          '" placeholder="firm-wide" style="width:100%;text-align:right">' +
          (s.percent ? ' <span class="muted">%</span>' : "") + "</td>" +
          '<td class="muted">' + esc(s.hint) + "</td></tr>";
      }).join("") + "</tbody></table>";
    this._bind(host, audit, onChange);
  },

  _bind(host, audit, onChange) {
    host.querySelectorAll("[data-audit]").forEach((input) => {
      input.onchange = () => {
        const setting = AUDIT_SETTINGS.find((s) => s.key === input.getAttribute("data-audit"));
        const text = input.value.trim();
        // Cleared means "use the firm-wide value" — the key is removed rather than
        // stored as zero, which would be a division deliberately scoring nothing.
        if (!text) { delete audit[setting.key]; onChange(); return; }
        const value = Number(text);
        if (!isFinite(value) || value < 0) {
          App.toast(setting.label + " must be a number", "error");
          return;
        }
        audit[setting.key] = setting.percent ? value / 100 : value;
        onChange();
      };
    });
  },
};
