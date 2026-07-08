// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial
// research and educational use only. Any commercial use, including
// but not limited to use in or for products or services offered for sale,
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
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

const RISK_COLORS = { Acceptable: "#388e3c", Conditional: "#f57c00", Unacceptable: "#d32f2f" };

// Overall risk rating badge.
function riskBadge(rating) {
  const color = RISK_COLORS[rating];
  if (!color) return '<span class="muted">—</span>';
  return '<span class="badge" style="background:' + color + '">' + esc(rating) + "</span>";
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

const REVIEW_COLORS = {
  "Overdue": "#d32f2f", "Due Soon": "#f57c00", "Upcoming": "#1976d2",
  "On Track": "#388e3c", "Not Scheduled": "#9e9e9e",
};

// Model review-status badge (Overdue / Due Soon / Upcoming / On Track).
function reviewBadge(status) {
  const color = REVIEW_COLORS[status] || "#9e9e9e";
  return '<span class="badge" style="background:' + color + '">' + esc(status || "—") + "</span>";
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
