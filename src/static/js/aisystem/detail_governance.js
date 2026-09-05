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
// What an AI System answers to, which a model does not.
//
// Three loaders, each fetched on demand rather than served with the record: the legal
// regimes that apply to it, the configuration snapshots recording what it was actually
// running, and the operating envelope it must stay inside.
//
// They are together because they are one question asked at three depths — what are the
// rules, what was this thing when it ran, and what is it allowed to do. A reviewer
// reads them in that order, and an incident is investigated in the reverse one.
//
// Assigns onto AISystemDetail; loads after detail_core.js.

Object.assign(AISystemDetail, {

  // Which regimes bite, and why. Resolved server-side: applicability is config the
  // institution can extend, and a copy of the rules in the console would answer
  // differently the moment somebody added a regime.
  async _loadRegimes() {
    const box = document.getElementById("ais-regimes");
    if (!box) return;
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/regimes");
      if (!body.regimes.length) {
        box.className = "empty";
        box.textContent = "No regime applies on the markets recorded for this system.";
        return;
      }
      box.className = "";
      box.innerHTML = body.regimes.map((r) =>
        '<div class="inforow"><div class="k">' + esc(r.name) + '</div><div class="v">' +
        esc(r.because) + '<span class="muted" style="font-size:var(--size-xs)"> &middot; ' +
        r.clauses + " obligations</span></div></div>").join("");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  // The configuration history, with what moved at each version. Fetched rather than
  // read off the record: the record carries the CURRENT values, and the whole point of
  // the history is the gap between those and what was written down.
  async _loadSnapshots() {
    const box = document.getElementById("ais-snapshots");
    if (!box) return;
    const btn = document.getElementById("ais-snapshot");
    if (btn) {
      btn.onclick = () => App.amend(
        "Take a configuration snapshot of " + this.recordId() + ".", "POST",
        "/api/ai-systems/" + encodeURIComponent(this.recordId()) + "/snapshots", {},
        () => this.refresh());
    }
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/snapshots");
      if (!body.snapshots.length) {
        box.className = "empty";
        box.textContent = "No snapshot taken. The configuration is whatever the fields " +
          "above say today, with nothing recording what it was before.";
        return;
      }
      box.className = "";
      box.innerHTML = body.snapshots.slice().reverse().map((s) => {
        const moved = (s.changed || []).length
          ? (s.changed || []).map((c) => "<code>" + esc(c.field) + "</code> " +
              esc(String(c.before == null || c.before === "" ? "—" : c.before)) +
              " &rarr; " + esc(String(c.after == null || c.after === "" ? "—" : c.after))
            ).join("<br>")
          : '<span class="muted">first snapshot</span>';
        return '<div class="inforow"><div class="k">v' + esc(s.config_version) +
          '<div class="muted" style="font-size:var(--size-xs)">' +
          esc(String(s.taken_at || "").replace("T", " ").slice(0, 16)) +
          "</div></div><div class=\"v\">" + moved + "</div></div>";
      }).join("");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  // The envelope, read against the configuration in force now. Staleness comes from
  // the server: a console deciding it here would decide it differently from the report.
  async _loadEnvelope() {
    const box = document.getElementById("ais-envelope");
    if (!box) return;
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/envelope");
      const e = body.envelope;
      if (!e) {
        box.className = "empty";
        box.textContent = "No envelope measured. How much this system's output varies " +
          "under a fixed configuration is unrecorded.";
        return;
      }
      box.className = "";
      const limits = e.limits
        ? Object.keys(e.limits).sort((a, b) => a - b)
            .map((p) => "p" + esc(p) + " " + Math.round(e.limits[p] * 10000) / 10000)
            .join(" &ndash; ")
        : "&mdash;";
      // Stale and refused are both findings, not gaps, and are coloured as such.
      const tone = e.status === "ok" ? "green" : "amber";
      box.innerHTML = '<div class="inforow"><div class="k">Envelope</div><div class="v">' +
        limits + ' <span class="badge" style="background:' + Theme.value(tone) + '">' +
        esc(e.status) + "</span>" +
        '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">' +
        esc(e.runs) + " runs, configuration v" + esc(e.config_version) +
        (e.detail ? " &mdash; " + esc(e.detail) : "") + "</div></div></div>";
    } catch (err) {
      box.className = "empty";
      box.textContent = err.message;
    }
  },
});
