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

// Visual badge helpers, matching the PhysicalRisk governance palette.
const RAG_COLORS = { Green: "#388e3c", Amber: "#f57c00", Red: "#d32f2f" };
const TIER_COLORS = { 1: "#d32f2f", 2: "#f57c00", 3: "#1976d2", 4: "#388e3c", 5: "#9e9e9e" };

// Display a scalar value, or an em dash when empty.
function fieldDisplay(value) {
  if (value === null || value === undefined || value === "") return '<span class="muted">—</span>';
  return esc(value);
}

// RAG rating as a coloured dot + label.
function ragBadge(rating) {
  const color = RAG_COLORS[rating];
  if (!color) return '<span class="muted">—</span>';
  return '<span class="ragdot"><span class="dot" style="background:' + color +
    '"></span><span style="color:' + color + '">' + esc(rating) + "</span></span>";
}

// Tier as a coloured pill ("Tier 2").
function tierBadge(tier) {
  const color = TIER_COLORS[tier];
  if (!color) return '<span class="muted">—</span>';
  return '<span class="badge" style="background:' + color + '">Tier ' + esc(tier) + "</span>";
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

// Mirrors config TIER_LABELS (tiers 1-3 by criticality).
const TIER_DESCRIPTORS = { 1: "Mission critical", 2: "Important", 3: "Not important" };

// "Tier 2 - Substantial" descriptor.
function tierFullLabel(tier) {
  const d = TIER_DESCRIPTORS[tier];
  return d ? "Tier " + tier + " - " + d : "";
}

// Composite-rating colours, used by the Risk Rating tab. There is deliberately no
// badge helper: the composite is shown only on that tab, beside the components it
// is derived from, never as a bare verdict elsewhere.
const RISK_COLORS = { Acceptable: "#388e3c", Conditional: "#f57c00", Unacceptable: "#d32f2f" };

const VQ_COLORS = {
  "Addressed": "#388e3c", "Partially Addressed": "#f57c00",
  "Not Addressed": "#d32f2f", "Not Applicable": "#9e9e9e",
};

// Validation-question status badge.
function vqBadge(status) {
  const color = VQ_COLORS[status] || "#9e9e9e";
  return '<span class="badge" style="background:' + color + '">' + esc(status || "—") + "</span>";
}

const REVIEW_COLORS = {
  "Overdue": "#d32f2f", "Due Soon": "#f57c00", "Upcoming": "#1976d2",
  "On Track": "#388e3c", "Not Scheduled": "#9e9e9e",
};

// Model review-status badge (Overdue / Due Soon / Upcoming / On Track).
function reviewBadge(status) {
  const color = REVIEW_COLORS[status] || "#9e9e9e";
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

// Sort orders for badge columns (lower sorts first): highest-risk first.
const RAG_ORDER = { Red: 0, Amber: 1, Green: 2 };
const REVIEW_ORDER = { "Overdue": 0, "Due Soon": 1, "On Track": 2, "Upcoming": 2, "Not Scheduled": 3 };

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
  const hist = (data && data.signoff_history) || [];
  const latest = hist.length ? hist[hist.length - 1] : null;
  if (!latest) return '<span class="muted">—</span>';
  const outcome = latest.outcome || "Approved";
  const color = outcome === "Rejected" ? "var(--red)" : "#388e3c";
  return '<span style="color:' + color + ';font-weight:600">' + esc(outcome) + "</span>";
}

// Human-readable file size.
function fmtSize(bytes) {
  if (bytes === null || bytes === undefined) return "—";
  const kb = bytes / 1024;
  return kb < 1024 ? kb.toFixed(1) + " KB" : (kb / 1024).toFixed(1) + " MB";
}

// Yes/No test flag as a tick or cross.
function yesNo(value) {
  if (value === "Yes") return '<span style="color:#388e3c">&#10004; Yes</span>';
  if (value === "No") return '<span style="color:#d32f2f">&#10008; No</span>';
  return '<span class="muted">—</span>';
}
