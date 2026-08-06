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

// Fallback palette (used before the policy loads, or for unknown values). The live
// colours/labels/order come from the risk policy, resolved per a model's division.
const RAG_COLORS = { Green: "#388e3c", Amber: "#f57c00", Red: "#d32f2f" };
const TIER_COLORS = { 1: "#d32f2f", 2: "#f57c00", 3: "#1976d2", 4: "#388e3c", 5: "#9e9e9e" };

// The risk-policy registry: the firm-wide seed + each division's live policy, loaded
// once at startup. Colours, labels and ordering resolve per a model's division and
// fall back to the seed, then to the built-in palette above.
const Policy = {
  _seed: null,
  _divisions: {},
  _states: {},
  async load() {
    try {
      const reg = await App.get("/api/risk-policy");
      this._seed = reg.seed || null;
      this._divisions = reg.divisions || {};
      this._states = reg.states || {};
    } catch (e) { /* keep the built-in fallbacks */ }
  },
  // A division's policy lifecycle: {state: seed|draft|approved, approved_at}. The bands
  // everywhere else are the APPROVED ones; "draft" means the admin has since edited the
  // policy and it is waiting on the division's MRC.
  state(division) { return (division && this._states[division]) || null; },
  _for(division) { return (division && this._divisions[division]) || this._seed; },
  ratingColour(name, division) {
    const p = this._for(division);
    const r = p && (p.risk_ratings || []).find((x) => x.name === name);
    return r ? r.colour : null;
  },
  // Ratings are ordered most-severe first, so the list index is the sort key.
  ratingOrder(name, division) {
    const p = this._for(division);
    if (!p) return null;
    const i = (p.risk_ratings || []).findIndex((x) => x.name === name);
    return i < 0 ? null : i;
  },
  // Option lists for the risk fields, from the division's policy (null when not loaded,
  // so callers fall back to the field spec's constant options).
  ratingNames(division) {
    const p = this._for(division);
    return p ? (p.risk_ratings || []).map((r) => r.name) : null;
  },
  dimensionBandNames(key, division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions[key];
    return dim ? (dim.bands || []).map((b) => b.name) : null;
  },
  // A dimension's full bands ({name, colour, explanation, score}) — what the Admin editor
  // defines, for the surfaces that show a band the way Admin does rather than by name.
  dimensionBands(key, division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions[key];
    return dim ? (dim.bands || []) : null;
  },
  // The band a level dimension (Materiality/Complexity) names, for its colour and the
  // admin's explanation of what that level means.
  band(key, name, division) {
    const bands = this.dimensionBands(key, division) || [];
    return bands.find((b) => b.name === name) || null;
  },
  tierScores(division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions.mission_criticality;
    return dim ? (dim.bands || []).map((b) => b.score) : null;
  },
  // A dimension's admin-defined display label (so a renamed dimension shows through).
  dimensionLabel(key, division) {
    const p = this._for(division);
    const dim = p && p.dimensions && p.dimensions[key];
    return (dim && dim.label) || null;
  },
  // Mission-Criticality bands as {value: score, label: name} for a select — the model
  // stores the score, but the owner picks by the admin-defined band name.
  missionOptions(division) {
    const p = this._for(division);
    const bands = (((p || {}).dimensions || {}).mission_criticality || {}).bands || [];
    return bands.length ? bands.map((b) => ({ value: b.score, label: b.name })) : null;
  },
  // The Mission-Criticality band a tier selects (band score == tier), clamped like the
  // backend: out-of-range → nearest, missing → most conservative (first) band.
  mcBand(tier, division) {
    const p = this._for(division);
    const bands = (((p || {}).dimensions || {}).mission_criticality || {}).bands || [];
    if (!bands.length) return null;
    const byScore = {}; bands.forEach((b) => { byScore[b.score] = b; });
    const t = parseInt(tier, 10);
    if (byScore[t]) return byScore[t];
    if (isNaN(t)) return bands[0];
    const scores = bands.map((b) => b.score);
    return byScore[Math.min(Math.max(t, Math.min.apply(null, scores)), Math.max.apply(null, scores))] || null;
  },
};

// Display a scalar value, or an em dash when empty.
function fieldDisplay(value) {
  if (value === null || value === undefined || value === "") return '<span class="muted">—</span>';
  return esc(value);
}

// RAG rating as a coloured dot + label; colour from the division's policy.
function ragBadge(rating, division) {
  const color = Policy.ratingColour(rating, division) || RAG_COLORS[rating];
  if (!color) return '<span class="muted">—</span>';
  return '<span class="ragdot"><span class="dot" style="background:' + color +
    '"></span><span style="color:' + color + '">' + esc(rating) + "</span></span>";
}

// Sort key for a rating (lower = higher risk), from the division's policy order.
function ragOrder(rating, division) {
  const order = Policy.ratingOrder(rating, division);
  return order !== null ? order : (RAG_ORDER[rating] !== undefined ? RAG_ORDER[rating] : 99);
}

// Mission-Criticality as a coloured pill showing the division's band NAME (was "Tier N");
// colour and name come from the division's Mission-Criticality band for that tier score.
function tierBadge(tier, division) {
  const band = Policy.mcBand(tier, division);
  const color = (band && band.colour) || TIER_COLORS[tier];
  const label = (band && band.name) || TIER_DESCRIPTORS[tier] || ("Tier " + tier);
  if (!color) return '<span class="muted">—</span>';
  return '<span class="badge" style="background:' + color + '">' + esc(label) + "</span>";
}

const MEETING_STATUS_COLORS = {
  Scheduled: "#1976d2", "In Progress": "#f57c00", Held: "#388e3c", Cancelled: "#9e9e9e",
};

// MRC meeting status as a coloured pill.
function statusBadge(status) {
  const color = MEETING_STATUS_COLORS[status];
  if (!color) return fieldDisplay(status);
  return '<span class="badge" style="background:' + color + '">' + esc(status) + "</span>";
}

// Fallback descriptors (before the policy loads); live labels are the division's
// Mission-Criticality band names.
const TIER_DESCRIPTORS = { 1: "Mission critical", 2: "Important", 3: "Not important" };

// The descriptor shown next to the Mission-Criticality pill: the band's admin-defined
// explanation. Empty when the band carries none (the pill already names it).
function tierFullLabel(tier, division) {
  const band = Policy.mcBand(tier, division);
  if (band && band.explanation) return band.explanation;
  const d = (band && band.name) || TIER_DESCRIPTORS[tier];
  return d ? "Tier " + tier + " - " + d : "";
}

const VQ_COLORS = {
  "Addressed": "#388e3c", "Partially Addressed": "#f57c00",
  "Not Addressed": "#d32f2f", "Not Applicable": "#9e9e9e",
};

// Validation-question status badge.
function vqBadge(status) {
  const color = VQ_COLORS[status] || "#9e9e9e";
  return '<span class="badge" style="background:' + color + '">' + esc(status || "—") + "</span>";
}

// A model is "Due Soon" when its next review falls within this many days.
const DUE_SOON_DAYS = 30;

// Derive a model's review status from its next-review date (vs today):
// Overdue (past), Due Soon (within DUE_SOON_DAYS), On Track (later), or Not
// Scheduled (no/invalid date).
function reviewStatus(nextDate) {
  if (!nextDate) return "Not Scheduled";
  const due = new Date(nextDate + "T00:00:00");
  if (isNaN(due.getTime())) return "Not Scheduled";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((due - today) / 86400000);
  if (days < 0) return "Overdue";
  if (days <= DUE_SOON_DAYS) return "Due Soon";
  return "On Track";
}

// Sort order for the RAG column (lower sorts first): highest-risk first.
const RAG_ORDER = { Red: 0, Amber: 1, Green: 2 };

// The latest MRC sign-off outcome as a sortable string ("" when none).
function mrcOutcome(data) {
  const hist = (data && data.signoff_history) || [];
  return hist.length ? (hist[hist.length - 1].outcome || "Approved") : "";
}

const LIFECYCLE_COLORS = {
  "New": "#1976d2", "Being Enhanced": "#f57c00",
  "No New Development": "#9e9e9e", "Marked for Removal": "#d32f2f",
};

// Version-lifecycle badge (W4d): where a model version sits in its development arc.
function lifecycleBadge(lifecycle) {
  if (!lifecycle) return "";
  const color = LIFECYCLE_COLORS[lifecycle] || "#9e9e9e";
  return ' <span class="badge" style="background:' + color + '">' + esc(lifecycle) + "</span>";
}

// MRC status for a list row: the latest sign-off outcome (green, or red if
// rejected), or a dash when the MRC has not yet ruled. The detail view also
// surfaces pending requests; the list keeps to the decided outcome.
function mrcStatusBadge(data) {
  // An active request (queued to a committee, awaiting its decision) is the
  // model's current MRC state — it is waiting on approval — so Pending takes
  // precedence over any earlier decided outcome. "Pending" / "Attached" mirrors
  // the server's definition of an active request (api_models_signoff.pending_signoff).
  const reqs = (data && data.signoff_requests) || [];
  if (reqs.some((r) => r.status === "Pending" || r.status === "Attached")) {
    return '<span style="color:#f57c00;font-weight:600">Pending</span>';
  }
  const hist = (data && data.signoff_history) || [];
  const latest = hist.length ? hist[hist.length - 1] : null;
  if (!latest) return '<span class="muted">—</span>';
  const outcome = latest.outcome || "Approved";
  const color = outcome === "Rejected" ? "var(--red)" : "#388e3c";
  return '<span style="color:' + color + ';font-weight:600">' + esc(outcome) + "</span>";
}

// Every uploaded document is stored, but the console lists each one once and only
// where a reader can do something with it. Defaults mirror config/files.py;
// configure() makes the server's configuration authoritative once specs load.
const DocLinks = {
  _hidden: ["tex"],
  _inline: ["pdf", "png", "jpg", "jpeg", "txt"],

  configure(specs) {
    if (!specs) return;
    if (specs.hidden_doc_extensions) this._hidden = specs.hidden_doc_extensions;
    if (specs.inline_view_extensions) this._inline = specs.inline_view_extensions;
  },

  _ext(name) {
    const parts = String(name || "").split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  },

  // The documents of one category that the console shows. A hidden extension (the
  // LaTeX source filed beside its PDF) stays stored and can still be replaced by
  // re-uploading it — it is simply not listed as a second row saying the same thing.
  visible(docs, category) {
    const self = this;
    return (docs || []).filter((d) =>
      d.category === category && self._hidden.indexOf(self._ext(d.original_name)) < 0);
  },

  // How many documents a panel actually lists, for its tab badge — counting the
  // stored total instead would promise rows the tab does not show.
  countIn(docs, categories) {
    const self = this;
    return (categories || []).reduce((total, c) => total + self.visible(docs, c).length, 0);
  },

  // "View" opens the document in a new tab, for the formats a browser renders;
  // anything else is download-only.
  actions(base, id, doc) {
    const url = base + esc(id) + "/documents/" + esc(doc.item_id) + "/download";
    const view = this._inline.indexOf(this._ext(doc.original_name)) < 0 ? "" :
      '<a href="' + url + '?inline=1" target="_blank" rel="noopener">View</a> ';
    return view + '<a href="' + url + '">Download</a>';
  },
};

// Mirrors config CLOSED_REMEDIATION_STATUS.
const CLOSED_REMEDIATION_STATUS = "Closed";

// How many remediation steps are still outstanding. The tab badge answers "how much
// is left to do?", not "how many were ever raised", so a closed step stops counting.
// The tab itself still lists every step — closing one is history, not deletion.
function openRemediationCount(steps) {
  return (steps || []).filter((s) => s.status !== CLOSED_REMEDIATION_STATUS).length;
}

// Human-readable file size.
function fmtSize(bytes) {
  if (bytes === null || bytes === undefined) return "—";
  const kb = bytes / 1024;
  return kb < 1024 ? kb.toFixed(1) + " KB" : (kb / 1024).toFixed(1) + " MB";
}

// An uploaded_at stamp shown to the minute (UTC, as stored by add_document):
// "2026-07-30T11:13:28+00:00" → "2026-07-30 11:13". Documents are retained per
// upload, so the time — not just the date — is what distinguishes one dated
// monitoring result from the next when several land on the same day.
function fmtTimestamp(iso) {
  const s = String(iso || "");
  if (!s) return "—";
  return s.slice(0, 16).replace("T", " ");
}
