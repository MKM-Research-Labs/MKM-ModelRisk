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
// How a record's state is shown.
//
// Every badge and label the console draws — the risk rating, the tier, the lifecycle
// stage, the review's due status, the MRC's position — plus the two display primitives
// they share.
//
// Split out of helpers.js, which had grown to 442 lines holding three unrelated
// subjects. These functions have one thing in common and it is not "miscellaneous":
// each takes a stored value and returns what a person should read, which is exactly
// the boundary where an adopter's renamed vocabulary has to be honoured. A field's
// spec is asked first for that reason — a status renamed in Admin must not display by
// its stored value.
//
// Colours come from Theme in helpers.js and Policy in policy_registry.js, both of
// which load first.

// Display a scalar value, or an em dash when empty.
// What a stored value is shown as. A status vocabulary separates the two — the
// record holds "Production" while the division may call that stage something else
// — so anything displaying a field's value asks its spec first.
// The undecided owner ratification on a record, if there is one. Mirrors
// _owner_ratification.pending_owner_request on the server: the newest owner
// request decides, and only while it is still queued or on an agenda.
function pendingOwnerRatification(data) {
  const requests = ((data || {}).signoff_requests || []).filter((r) => r.kind === "owner");
  const latest = requests[requests.length - 1];
  if (!latest) return null;
  return (latest.status === "Pending" || latest.status === "Attached") ? latest : null;
}

function optionLabel(spec, value) {
  const shown = spec && spec.option_labels;
  if (!shown || value === null || value === undefined || value === "") return fieldDisplay(value);
  return fieldDisplay(shown[value] || value);
}

function fieldDisplay(value) {
  if (value === null || value === undefined || value === "") return '<span class="muted">—</span>';
  // A multi-value field (a person's roles) reads as a list, not as "a,b,c".
  if (Array.isArray(value)) {
    return value.length
      ? value.map((v) => '<span class="pill">' + esc(v) + "</span>").join(" ")
      : '<span class="muted">—</span>';
  }
  return esc(value);
}

// RAG rating as a coloured dot + label; colour from the division's policy.
function ragBadge(rating, division) {
  const color = Policy.ratingColour(rating, division) || Theme.colour("rag", rating);
  if (!color) return '<span class="muted">—</span>';
  return '<span class="ragdot"><span class="dot" style="background:' + color +
    '"></span><span style="color:' + color + '">' + esc(rating) + "</span></span>";
}

// The text colour that reads on a given background: dark on a light colour, white on
// a dark one. A division picks its own rating colours, and a yellow Amber under the
// white text a .badge assumes is unreadable. Relative luminance, per WCAG.
function readableOn(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || "");
  if (!m) return "var(--inverse)";
  const lin = [0, 2, 4].map((i) => {
    const c = parseInt(m[1].slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  const lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
  return lum > 0.4 ? "var(--text)" : "var(--inverse)";
}

// Sort key for a rating (lower = higher risk), from the division's policy order.
function ragOrder(rating, division) {
  const order = Policy.ratingOrder(rating, division);
  return order !== null ? order : (RAG_ORDER[rating] !== undefined ? RAG_ORDER[rating] : 99);
}

// Mission-Criticality as a coloured pill showing the division's band NAME (was "Tier N");
// colour and name come from the division's Mission-Criticality band for that tier score.
function tierBadge(tier, division) {
  // An unrated record shows a dash, never a band name. Policy.mcBand falls back to the
  // first band for a non-numeric tier, so without this guard a record nobody has rated
  // renders as "Critical" in red -- a rating no one gave, on a risk register.
  if (tier === null || tier === undefined || tier === "") return '<span class="muted">—</span>';
  const band = Policy.mcBand(tier, division);
  const color = (band && band.colour) || Theme.colour("mission_criticality", tier);
  const label = (band && band.name) || TIER_DESCRIPTORS[tier] || ("Tier " + tier);
  if (!color) return '<span class="muted">—</span>';
  return '<span class="badge" style="background:' + color + '">' + esc(label) + "</span>";
}

// MRC meeting status as a coloured pill.
function statusBadge(status) {
  const color = Theme.colour("meeting_status", status);
  if (!color) return fieldDisplay(status);
  return '<span class="badge" style="background:' + color + '">' + esc(status) + "</span>";
}

// Fallback descriptors (before the policy loads); live labels are the division's
// Mission-Criticality band names.
const TIER_DESCRIPTORS = { 1: "Mission critical", 2: "Important", 3: "Not important" };

// The descriptor shown next to the Mission-Criticality pill: the band's admin-defined
// explanation. Empty when the band carries none (the pill already names it).
function tierFullLabel(tier, division) {
  if (tier === null || tier === undefined || tier === "") return "—";
  const band = Policy.mcBand(tier, division);
  if (band && band.explanation) return band.explanation;
  const d = (band && band.name) || TIER_DESCRIPTORS[tier];
  return d ? "Tier " + tier + " - " + d : "";
}

// Validation-question status badge.
function vqBadge(status) {
  const color = Theme.colour("validation_question", status);
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

// A subject's CURRENT MRC state — the one thing the status column, the summary tile and
// the Risk tab must all agree on. It mirrors the risk engine (model_inventory/risk.py):
// an active request supersedes any earlier decision; a Rejected or Revoked latest decision
// is not a sign-off; and an approval granted before the division ratified its current
// categorisation is stale, because it was made against categories that no longer exist.
// A sign-off covers one cell, so it stops covering the subject once the owner moves it to
// another — "Rating moved" is approved-but-not-for-where-it-now-sits.
// Returns "Pending" | "Rejected" | "Revoked" | "Re-classify" | "Rating moved" |
// "Not placed" | "Approved" | "".
function mrcState(data, division) {
  const reqs = (data && data.signoff_requests) || [];
  if (reqs.some((r) => r.status === "Pending" || r.status === "Attached")) return "Pending";
  const hist = (data && data.signoff_history) || [];
  const latest = hist.length ? hist[hist.length - 1] : null;
  if (!latest) return "";
  const outcome = latest.outcome || "Approved";
  if (outcome === "Rejected" || outcome === "Revoked") return outcome;
  const div = division === undefined ? data.division : division;
  const ratified = (Policy.state(div) || {}).approved_at;
  if (ratified && latest.date && latest.date < ratified) return "Re-classify";
  const rag = Policy.gridRating(data.tier, data.materiality, data.complexity, div);
  if (!rag) return "Not placed";
  if (latest.to_rating !== rag) return "Rating moved";
  return "Approved";
}

// Version-lifecycle badge (W4d): where a model version sits in its development arc.
function lifecycleBadge(lifecycle) {
  if (!lifecycle) return "";
  const color = Theme.colour("lifecycle", lifecycle);
  return ' <span class="badge" style="background:' + color + '">' + esc(lifecycle) + "</span>";
}

// MRC status for a list row: the latest sign-off outcome (green, or red if
// rejected), or a dash when the MRC has not yet ruled. The detail view also
// surfaces pending requests; the list keeps to the decided outcome.
function mrcStatusBadge(data) {
  const state = mrcState(data);
  if (!state) return '<span class="muted">—</span>';
  // Each non-approved state says, on hover, what the Risk tab says at length: the approval
  // is in the history but does not cover the subject as it now stands.
  const hist = (data && data.signoff_history) || [];
  const approvedRating = (hist.length ? hist[hist.length - 1].to_rating : "") || "—";
  const hints = {
    "Re-classify": "Signed off under an older categorisation — re-confirm the " +
      "classification and request sign-off again.",
    "Rating moved": "The MRC approved " + approvedRating + "; the heatmap now says " +
      (Policy.gridRating(data.tier, data.materiality, data.complexity, data.division) || "—") +
      ". Request sign-off for the rating it now carries.",
    "Not placed": Policy.dimensionName("materiality", data.division) + " or " +
      Policy.dimensionName("complexity", data.division).toLowerCase() +
      " is unset, so this is not on the heatmap and there is no rating to sign off.",
  };
  const title = hints[state] ? ' title="' + esc(hints[state]) + '"' : "";
  return '<span style="color:' + Theme.colour("mrc_state", state) +
    ';font-weight:600"' + title + ">" + esc(state) + "</span>";
}
