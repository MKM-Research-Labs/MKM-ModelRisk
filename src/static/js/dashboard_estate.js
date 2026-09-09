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

// The dashboard's two context panels: the shape of the estate, and which way it is
// moving.
//
// Separate from the queue beside them because they answer a different question. The
// queue is what is owed today and by whom; these say how much there is to govern and
// whether the governing is getting better — the figure an executive asks for second,
// and the one a single day's count cannot give.
//
// Assigns onto Dashboard; loads after dashboard.js.

Object.assign(Dashboard, {

  _estate(d) {
    const e = d.estate || {};
    const o = d.operational || {};
    const kinds = Object.keys(e.by_kind || {}).map((k) =>
      this._line(k, e.by_kind[k])).join("");
    const tiers = Object.keys(e.by_tier || {}).map((t) =>
      this._line(t === "untiered" ? "Untiered" : "Tier " + t, e.by_tier[t])).join("");
    return '<div class="card"><h3>The estate</h3>' + kinds + tiers +
      this._line("Operational failures, " + (o.window_days || 0) + " days",
                 o.failures_in_window, o.failures_in_window ? this._colour("act") : null) +
      "</div>";
  },

  _direction(d) {
    const dir = d.direction || {};
    const share = dir.share_meeting_standard == null
      ? "—" : Math.round(dir.share_meeting_standard * 100) + "%";
    const trend = this._trend(dir.trend);
    return '<div class="card"><h3>Meeting the standard</h3>' +
      '<div style="font-size:var(--size-xl);font-weight:700">' + esc(share) + "</div>" +
      this._line("Records audited", dir.records_audited) +
      this._line("Meeting the standard", dir.records_meeting_standard,
                 this._colour("clear")) +
      this._line("Below the standard", dir.records_below_standard,
                 dir.records_below_standard ? this._colour("act") : null) +
      trend + "</div>";
  },

  // The one chart on the page. "Is this getting better?" is the second question
  // every executive asks, and a figure for today cannot answer it. Drawn from the
  // observed series only — with no history it says so, because a flat line and an
  // empty history look identical and only one of them is true.
  _trend(series) {
    if (series == null || !series.length) {
      return '<div class="muted" style="margin-top:var(--space-4)">No history yet — ' +
        "the observation runs daily, and the trend appears once it has looked more " +
        "than once.</div>";
    }
    const points = series
      .map((row) => (row.share_meeting_standard == null ? null : row.share_meeting_standard))
      .filter((v) => v !== null);
    if (points.length < 2) {
      return '<div class="muted" style="margin-top:var(--space-4)">Observed once so ' +
        "far — a trend needs a second look.</div>";
    }
    const colour = this._colour("clear");
    const W = 240, H = 44;
    // Scale to the observed range, never to 0–100: a governed estate lives in the
    // top few percent, and a full-height axis would draw every real movement flat.
    const lo = Math.min.apply(null, points), hi = Math.max.apply(null, points);
    const span = (hi - lo) || 1;
    const x = (i) => (i * W) / (points.length - 1);
    const y = (v) => H - ((v - lo) / span) * (H - 8) - 4;
    const path = points.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
    const first = Math.round(points[0] * 100), last = Math.round(points[points.length - 1] * 100);
    const delta = last - first;
    // preserveAspectRatio="none" so the chart fills the panel's width instead of
    // being scaled to its height and centred; the strokes are marked non-scaling so
    // stretching the box does not stretch the line with it.
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" height="44" ' +
      'preserveAspectRatio="none" ' +
      'style="display:block;margin:var(--space-5) 0" role="img" aria-label="' +
      esc("Records meeting the standard, " + first + " to " + last + " per cent over " +
          points.length + " observations") + '">' +
      '<path d="' + path + " L" + W + "," + H + " L0," + H + ' Z" fill="' + colour +
      '" opacity="0.12"></path>' +
      '<path d="' + path + '" fill="none" stroke="' + colour +
      '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"></path>' +
      '<path d="M' + W + "," + y(points[points.length - 1]).toFixed(1) + " L" + W +
      "," + y(points[points.length - 1]).toFixed(1) + '" stroke="' + colour +
      '" stroke-width="7" stroke-linecap="round" vector-effect="non-scaling-stroke">' +
      "</path></svg>" +
      '<div class="muted" style="font-size:var(--size-xs)">' +
      esc(first + "% → " + last + "% over " + points.length + " observations") +
      (delta === 0 ? "" : esc(" · " + (delta > 0 ? "+" : "") + delta + " points")) +
      "</div>";
  },

  _line(label, value, colour) {
    return '<div class="inforow"><span class="k">' + esc(label) + "</span>" +
      '<span class="v"' + (colour ? ' style="color:' + colour + '"' : "") + ">" +
      esc(value == null ? "—" : value) + "</span></div>";
  },
});
