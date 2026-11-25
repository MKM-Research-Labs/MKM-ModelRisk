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
  overdue: "red", due_soon: "amber", open: "green", baseline: "grey", unobserved: "grey",
};

const FindingDeadlines = {
  // The placeholder a host drops into its markup; ``load`` fills it.
  html(elId) {
    return '<div class="section-header">Open findings</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">What the completeness audit finds missing ' +
      "on this record, and the first day the daily audit saw each gap.</p>" +
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
      // Deadlines can be switched off (FINDING_DEADLINES_ENFORCED): then no finding
      // carries a due date, and the Band, Due and Over columns are left out rather
      // than printed as a column of dashes.
      const dated = res.findings.some((f) => f.due);
      const cols = dated ? [30, 12, 16, 16, 10, 16] : [50, 25, 25];
      const heads = dated ? ["Finding", "Band", "First seen", "Due", "Over", "Status"]
                          : ["Finding", "First seen", "Status"];
      box.innerHTML = '<table style="table-layout:fixed;width:100%"><colgroup>' +
        cols.map((w) => '<col style="width:' + w + '%">').join("") + "</colgroup>" +
        "<thead><tr>" + heads.map((h) => "<th>" + h + "</th>").join("") +
        "</tr></thead><tbody>" +
        res.findings.map((f) => this._row(f, dated)).join("") + "</tbody></table>" +
        (res.observed ? "" : '<p class="muted" style="font-size:var(--size-xs)">The daily ' +
          "audit has not run yet, so no finding has a first-seen date to count from.</p>");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  _row(f, dated) {
    const colour = Theme.value(FINDING_STATUS_COLOUR[f.status] || "grey");
    const over = f.days_over > 0 ? esc(f.days_over) + " d" : "&mdash;";
    return "<tr><td>" + esc(f.label || f.key || "") +
      (f.action ? '<br><span class="muted" style="font-size:var(--size-xs)">' +
        esc(f.action) + "</span>" : "") + "</td>" +
      (dated ? "<td>" + esc(f.band || "") + " (" + esc(f.sla_days) + " d)</td>" : "") +
      "<td>" + esc(f.first_seen || "—") + "</td>" +
      (dated ? "<td>" + esc(f.due || "—") + "</td><td>" + over + "</td>" : "") +
      '<td><span class="badge" style="background:' + colour + '">' +
      esc(f.status_label) + "</span></td></tr>";
  },
};
