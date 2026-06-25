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

const Audit = {
  async render() {
    const el = document.getElementById("tab-audit");
    const events = await App.get("/api/audit");
    let rows = "";
    events.forEach(function (e) {
      const when = e.recorded_at.replace("T", " ").slice(0, 19);
      rows +=
        "<tr><td>" + esc(e.global_seq) + "</td><td>" + esc(when) + "</td>" +
        "<td>" + esc(e.actor) + "</td>" +
        "<td>" + esc(e.aggregate_type) + "<br><span class='pill'>" + esc(e.aggregate_id) + "</span></td>" +
        "<td>" + esc(e.event_type) + "</td>" +
        "<td>" + esc(e.reason || "—") + "</td></tr>";
    });
    const body = events.length
      ? "<table><thead><tr><th>#</th><th>When (UTC)</th><th>Actor</th><th>Aggregate</th><th>Event</th><th>Reason</th></tr></thead><tbody>" +
        rows + "</tbody></table>"
      : '<div class="empty">No events yet. Every change you make appears here, in order, immutably.</div>';
    el.innerHTML =
      '<div class="card"><h3>Audit trail — the immutable event log</h3>' +
      '<p class="muted">Every recorded change, newest first. This is the source of truth; ' +
      "the inventory and meeting views above are projections of it.</p>" + body + "</div>";
  },
};
