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
