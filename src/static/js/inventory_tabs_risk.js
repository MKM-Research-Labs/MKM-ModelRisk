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
// The Risk Rating tab: the heatmap and the assessment behind it.
//
// Shared by all four governed record types -- a model, an ML Application, an AI System
// and a Product are placed on the same grid, because a rating that means different
// things on different screens is not a rating.
//
// The axis names come from the division's ratified policy, never from here. The
// built-in names are a fallback for a payload that predates the policy, and must not
// be used for a rename: an institution that renamed a dimension in Admin has to see
// its own word on every screen.
//
// Assigns onto DetailTabs; loads after inventory_tabs.js.

Object.assign(DetailTabs, {
  // The dimension names a division uses, from the risk-rating envelope. They fall back to
  // the built-in names only for a payload that predates the policy (never for a rename).
  axisLabels(hm) {
    const labels = (hm && hm.axis_labels) || {};
    return {
      mission_criticality: labels.mission_criticality || "Mission Criticality",
      materiality: labels.materiality || "Materiality",
      complexity: labels.complexity || "Complexity",
    };
  },

  // W4a: the Materiality × Complexity → RAG grid for the model's Mission-Criticality
  // band. The current cell is highlighted; the rating headline is its colour.
  heatmap(hm) {
    const labels = this.axisLabels(hm);
    // Captioned the way Admin → Risk captions the same table: the band's colour, the
    // dimension it belongs to, then the band itself.
    const tierCaption = hm.tier_label
      ? '<div class="grid-cap" style="display:flex;align-items:center;gap:var(--space-4);margin:var(--space-7) 0 var(--space-3)">' +
        '<span style="display:inline-block;width:12px;height:12px;border-radius:var(--radius-sm);background:' +
        esc(hm.tier_colour || Theme.value("grey")) + '"></span>' +
        '<span style="font-size:var(--size-xxs);text-transform:uppercase;color:var(--muted);letter-spacing:.04em">' +
        esc(labels.mission_criticality) + "</span>" +
        '<span style="font-size:14px;font-weight:700">' + esc(hm.tier_label) + "</span></div>"
      : "";
    // Axes and cell colours come from the division's policy (echoed on the envelope),
    // falling back to the classic Low/Medium/High + RAG palette for older payloads.
    const axes = hm.axes || {};
    const ratingColours = hm.rating_colours || {};
    const matOrder = axes.materiality || ["Low", "Medium", "High"];
    const cols = axes.complexity || ["Low", "Medium", "High"];
    const rows = matOrder.slice().reverse();  // highest materiality at the top
    const grid = hm.grid || {};
    const cellRag = (m, c) => grid[m + "|" + c] || "";
    const table = rows.map(function (m) {
      const cells = cols.map(function (c) {
        const rag = cellRag(m, c);
        const bg = ratingColours[rag] || Theme.hex("rag", rag) || Theme.value("grey");
        const here = (m === hm.materiality && c === hm.complexity);
        const style = "background:" + bg + "22;color:" + bg + ";" +
          (here ? "outline:3px solid " + bg + ";outline-offset:-3px;font-weight:800;" : "");
        return '<td class="hcell" style="' + style + '">' + esc(rag || "—") +
          (here ? '<br><span style="font-size:var(--size-xxs)">YOU</span>' : "") + "</td>";
      }).join("");
      return "<tr><th>" + esc(m) + "</th>" + cells + "</tr>";
    }).join("");
    // Axis titles live outside the table so they can't stretch the row-label
    // column: materiality runs vertically down the left, complexity across
    // above the column headers.
    return tierCaption + '<div class="heatmap-wrap">' +
      '<div class="hm-y-axis">' + esc(labels.materiality) + "</div>" +
      "<div>" +
      '<div class="hm-x-axis">' + esc(labels.complexity) + " &rarr;</div>" +
      '<table class="heatmap"><thead><tr><th></th>' +
      cols.map((c) => "<th>" + esc(c) + "</th>").join("") +
      "</tr></thead><tbody>" + table + "</tbody></table>" +
      "</div></div>" +
      '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-1)">' +
      esc(labels.materiality) + " and " + esc(labels.complexity) +
      " are set above; this table is the division's policy, not a per-model setting.</div>";
  },

  risk(rating, showEvents = true, division) {
    const hm = rating.heatmap || {};
    const labels = this.axisLabels(hm);
    const subject = showEvents ? "product" : "model";
    const hmRag = hm.rag;
    // The rating's colour is the division's, from the policy on the envelope — a renamed
    // or re-coloured rating shaded this banner with the built-in palette before.
    const hmColor = (hm.rating_colours || {})[hmRag] || Theme.hex("rag", hmRag) ||
      Theme.value("grey");
    const headline = hmRag
      ? '<div class="riskbanner" style="border-color:' + hmColor + ";background:" + hmColor + '14">' +
        '<div class="muted" style="text-align:center">HEATMAP RATING</div>' +
        '<div style="text-align:center;font-size:28px;font-weight:800;color:' + hmColor + '">' +
        esc(hmRag) + "</div>" +
        '<div style="text-align:center" class="muted">' + esc(labels.materiality) + ": <b>" +
        esc(hm.materiality) + "</b> &middot; " + esc(labels.complexity) + ": <b>" +
        esc(hm.complexity) + "</b></div></div>"
      : '<div class="riskbanner" style="border-color:var(--grey);background:' + Theme.value("grey") + '14">' +
        '<div class="muted" style="text-align:center">HEATMAP RATING</div>' +
        '<div style="text-align:center;font-size:var(--size-lg)" class="muted">Set ' +
        esc(labels.materiality) + " and " + esc(labels.complexity) + " above to place this " +
        subject + " on the heatmap.</div>" +
        "</div>";
    // Events are a product-level (production) concern, so the count shows only on
    // products, not models.
    const events = showEvents ? '<div class="row" style="gap:var(--space-8);margin:var(--space-6) 0"><div class="scard" ' +
      'style="border-left-color:var(--accent)"><div class="lbl">Events (past ' + rating.events_window_days +
      ' days)</div><div class="val">' + rating.events_in_window + "</div></div></div>" : "";
    const signoff = this._signoffPanel(rating);
    // A prior sign-off made under an older categorisation is no longer valid: the owner
    // must re-confirm the classification and re-request MRC sign-off.
    const reclassify = rating.needs_reclassification
      ? '<div class="riskbanner" style="border-color:var(--amber);background:var(--warn-bg)">' +
        '<div style="font-weight:700;color:var(--warn-ink-alt)">Re-classification needed</div>' +
        '<div class="muted" style="font-size:var(--size-sm)">The division\'s risk categorisation has ' +
        "changed since this " + subject + " was signed off. Re-confirm " +
        esc(labels.materiality) + ", " + esc(labels.complexity) + " and " +
        esc(labels.mission_criticality) +
        " above, then request MRC sign-off again.</div></div>"
      : "";
    return '<p class="muted">Risk rating is set by the owner via ' + esc(labels.materiality) +
      " and " + esc(labels.complexity) +
      " (the heatmap), and takes effect once the MRC signs that cell off.</p>" +
      reclassify + headline + signoff + this.heatmap(hm) + events +
      this.signoffHistory(rating.signoff_history, division);
  },
});
