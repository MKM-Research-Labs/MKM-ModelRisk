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

// Custom (non-generic) tab renderers for the model detail: Validation, Risk
// Rating, Versions timeline and the per-model Audit trail.
function barColor(pct) {
  return pct >= 75 ? "#388e3c" : pct >= 45 ? "#f57c00" : "#d32f2f";
}

const DetailTabs = {
  validation(data, retired) {
    const questions = data.validation_questions || [];
    const counts = { "Addressed": 0, "Partially Addressed": 0, "Not Addressed": 0, "Not Applicable": 0 };
    questions.forEach((q) => { if (counts[q.status] !== undefined) counts[q.status]++; });
    const total = questions.length;
    const pct = total ? Math.round((counts.Addressed / total) * 100) : 0;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    const statuses = ["Addressed", "Partially Addressed", "Not Addressed", "Not Applicable"];
    const rows = questions.map(function (q, i) {
      let statusCell, rationaleCell, actionCell;
      if (retired) {
        statusCell = vqBadge(q.status);
        rationaleCell = fieldDisplay(q.rationale);
        actionCell = "";
      } else {
        const opts = statuses.map((o) =>
          "<option" + (o === q.status ? " selected" : "") + ">" + o + "</option>").join("");
        statusCell = '<select id="vq-' + esc(q.item_id) + '-status">' + opts + "</select>";
        rationaleCell = '<input id="vq-' + esc(q.item_id) + '-rationale" value="' +
          esc(q.rationale || "") + '">';
        actionCell = '<button class="btn small primary" data-vq-save="' + esc(q.item_id) +
          '">Save&hellip;</button>';
      }
      return "<tr><td>" + (i + 1) + "</td><td><b>" + fieldDisplay(q.short_label) +
        '</b><br><span class="muted">' + fieldDisplay(q.question) + "</span></td><td>" + statusCell +
        "</td><td>" + rationaleCell + "</td><td>" + actionCell + "</td></tr>";
    }).join("");
    return '<p class="muted">The nine SR 26-2 questions every model owner should be able to answer. ' +
      "Set the status and add a rationale, then Save the row.</p>" +
      '<div class="summary">' + card("Addressed", counts.Addressed, "#388e3c") +
      card("Partially", counts["Partially Addressed"], "#f57c00") +
      card("Not Addressed", counts["Not Addressed"], "#d32f2f") +
      card("N/A", counts["Not Applicable"], "#9e9e9e") + "</div>" +
      '<div class="muted" style="margin-bottom:6px">Coverage: ' + counts.Addressed + "/" + total +
      " (" + pct + "%)</div>" +
      '<div class="progress"><div class="bar" style="width:' + pct + "%;background:" + barColor(pct) + '"></div></div>' +
      "<table><thead><tr><th>#</th><th>Question</th><th>Status</th><th>Rationale</th><th></th></tr>" +
      "</thead><tbody>" + rows + "</tbody></table>";
  },

  risk(rating) {
    const color = RISK_COLORS[rating.rating] || "#9e9e9e";
    const pct = Math.round(rating.score * 100);
    const comps = rating.components.map(function (c) {
      const s = Math.round(c.score * 100);
      return '<div style="margin-bottom:10px"><div><b>' + esc(c.label) + '</b> <span class="muted">(' +
        Math.round(c.weight * 100) + '% weight)</span><span style="float:right;color:' + barColor(s) + '">' +
        s + '%</span></div><div class="progress"><div class="bar" style="width:' + s + "%;background:" +
        barColor(s) + '"></div></div></div>';
    }).join("");
    return '<p class="muted">Composite of validation coverage, remediation health, review currency, ' +
      "assumption risk and limitation risk.</p>" +
      '<div class="riskbanner" style="border-color:' + color + ";background:" + color + '14">' +
      '<div class="muted" style="text-align:center">EFFECTIVE RATING</div>' +
      '<div style="text-align:center;font-size:28px;font-weight:800;color:' + color + '">' + esc(rating.rating) + "</div>" +
      '<div style="text-align:center" class="muted">Composite Score: ' + pct + "%</div></div>" +
      '<div class="section-header">Component Breakdown</div>' + comps;
  },

  versions(data, spec, retired) {
    const items = data.version_history || [];
    const banner = '<div class="vbanner"><span class="muted">CURRENT VERSION</span> <b style="color:#1976d2">v' +
      fieldDisplay(data.version) + "</b></div>";
    const timeline = items.length ? items.map(function (v) {
      const rm = retired ? "" : ' <span class="edit-btn" data-rm="version_history|' + esc(v.item_id) + '">remove</span>';
      return '<div class="vitem"><div><b>' + fieldDisplay(v.version) + '</b><span class="muted" style="float:right">' +
        fieldDisplay(v.date) + "</span></div><div>" + fieldDisplay(v.description) + '</div><div class="muted">Author: ' +
        fieldDisplay(v.author) + (v.ref_document ? " · Ref: " + esc(v.ref_document) : "") + "</div>" + rm + "</div>";
    }).join("") : '<div class="empty">No version history yet.</div>';
    const add = retired ? "" : '<div class="row" style="margin-top:10px">' +
      spec.fields.map((f) => '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
        inputControl("add-version_history-" + f.key, f) + "</div>").join("") +
      '<button class="btn small" data-add="version_history">Add version…</button></div>';
    return banner + timeline + add;
  },

  audit(events) {
    if (!events.length) return '<div class="empty">No recorded changes for this model yet.</div>';
    const rows = events.map(function (e) {
      const when = e.recorded_at.replace("T", " ").slice(0, 19);
      return "<tr><td>" + esc(when) + "</td><td>" + esc(e.event_type) + "</td><td>" + esc(e.actor) +
        "</td><td>" + esc(e.reason || "—") + "</td></tr>";
    }).join("");
    return "<table><thead><tr><th>When (UTC)</th><th>Event</th><th>Actor</th><th>Reason</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
  },

  // Read-only renderer for items projected from MRC meetings (decisions /
  // actions linked to this model). Includes the source meeting on every row.
  linkedItems(label, items, fields) {
    if (!items.length) {
      return '<p class="muted">' + esc(label) +
        " are recorded against MRC meetings — link a meeting decision or action " +
        "to this model and it will appear here.</p>" +
        '<div class="empty">No ' + esc(label.toLowerCase()) + " linked yet.</div>";
    }
    const head = fields.map((k) => "<th>" + esc(k.replace("_", " ")) + "</th>").join("") +
      "<th>From meeting</th>";
    const rows = items.map(function (it) {
      const cells = fields.map((k) => "<td>" + fieldDisplay(it[k]) + "</td>").join("");
      const meeting = "<td>" + esc(it.meeting_title || it.meeting_id) +
        '<br><span class="muted">' + esc(it.meeting_id) +
        (it.meeting_date ? " · " + esc(it.meeting_date) : "") + "</span></td>";
      return "<tr>" + cells + meeting + "</tr>";
    }).join("");
    return '<p class="muted">' + esc(label) + " linked to this model from the MRC meeting log " +
      "(read-only).</p>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + rows + "</tbody></table>";
  },
};
