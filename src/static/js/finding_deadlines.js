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

// A record's open completeness findings and when each falls due.
//
// The dashboard says a record has findings past their deadline; this says which, when
// each was first seen, and when it was due. Shown at the top of a record's Remediation
// stage (models, ML Applications, AI Systems, through review_panel.js) and its
// Remediation tab (products), because that is where the owner goes to put them right.
//
// Read-only and fetched, never computed here: the dates come from the same arithmetic
// the dashboard row uses (src/governance/attention/deadlines.py), so the two screens
// cannot quote different deadlines for the same finding. Status labels arrive with
// the payload, so an adopter's wording is never hardcoded in this file.
const FINDING_STATUS_COLOUR = {
  overdue: "red", due_soon: "amber", open: "green", unobserved: "grey",
};

const FindingDeadlines = {
  // The placeholder a host drops into its markup; ``load`` fills it.
  html(elId) {
    return '<div class="section-header">Open findings</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">What the completeness audit finds missing ' +
      "on this record, and the deadline its band sets for putting it right. The clock starts " +
      "the first day the daily audit saw the gap.</p>" +
      '<div id="' + esc(elId) + '" class="empty">Loading&hellip;</div>';
  },

  async load(box, recordId) {
    if (!box) return;
    try {
      const res = await App.get("/api/findings/" + encodeURIComponent(recordId));
      if (!res.findings.length) {
        box.className = "empty";
        box.textContent = "Nothing open. The audit finds this record complete.";
        return;
      }
      box.className = "";
      box.innerHTML = '<table style="table-layout:fixed;width:100%"><colgroup>' +
        '<col style="width:30%"><col style="width:12%"><col style="width:16%">' +
        '<col style="width:16%"><col style="width:10%"><col style="width:16%"></colgroup>' +
        "<thead><tr><th>Finding</th><th>Band</th><th>First seen</th><th>Due</th>" +
        "<th>Over</th><th>Status</th></tr></thead><tbody>" +
        res.findings.map((f) => this._row(f)).join("") + "</tbody></table>" +
        (res.observed ? "" : '<p class="muted" style="font-size:var(--size-xs)">The daily ' +
          "audit has not run yet, so no finding has a first-seen date to count from.</p>");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  _row(f) {
    const colour = Theme.value(FINDING_STATUS_COLOUR[f.status] || "grey");
    const over = f.days_over > 0 ? esc(f.days_over) + " d" : "&mdash;";
    return "<tr><td>" + esc(f.label || f.key || "") +
      (f.action ? '<br><span class="muted" style="font-size:var(--size-xs)">' +
        esc(f.action) + "</span>" : "") + "</td>" +
      "<td>" + esc(f.band || "") + " (" + esc(f.sla_days) + " d)</td>" +
      "<td>" + esc(f.first_seen || "—") + "</td><td>" + esc(f.due || "—") + "</td>" +
      "<td>" + over + "</td>" +
      '<td><span class="badge" style="background:' + colour + '">' +
      esc(f.status_label) + "</span></td></tr>";
  },
};
