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
      let statusCell, rationaleCell;
      if (retired) {
        statusCell = vqBadge(q.status);
        rationaleCell = fieldDisplay(q.rationale);
      } else {
        const opts = statuses.map((o) =>
          "<option" + (o === q.status ? " selected" : "") + ">" + o + "</option>").join("");
        // data-vq-item drives auto-save: changing the status or leaving the
        // rationale posts the row straight away (see _bindValidationSaves).
        statusCell = '<select data-vq-item="' + esc(q.item_id) + '" id="vq-' + esc(q.item_id) +
          '-status" style="width:100%">' + opts + "</select>";
        // A three-line textarea (not a single-line input) so a full rationale is
        // visible; it scrolls once the text runs past three lines.
        rationaleCell = '<textarea data-vq-item="' + esc(q.item_id) + '" id="vq-' + esc(q.item_id) +
          '-rationale" rows="3" style="width:100%;resize:vertical;overflow-y:auto">' +
          esc(q.rationale || "") + "</textarea>";
      }
      return "<tr><td>" + (i + 1) + "</td><td><b>" + fieldDisplay(q.short_label) +
        '</b><br><span class="muted">' + fieldDisplay(q.question) + "</span></td><td>" + statusCell +
        "</td><td>" + rationaleCell + "</td></tr>";
    }).join("");
    return '<p class="muted">The nine SR 26-2 questions every model owner should be able to answer. ' +
      "Set the status and add a rationale &mdash; each change saves automatically.</p>" +
      '<div class="summary">' + card("Addressed", counts.Addressed, "#388e3c") +
      card("Partially", counts["Partially Addressed"], "#f57c00") +
      card("Not Addressed", counts["Not Addressed"], "#d32f2f") +
      card("N/A", counts["Not Applicable"], "#9e9e9e") + "</div>" +
      '<div class="muted" style="margin-bottom:6px">Coverage: ' + counts.Addressed + "/" + total +
      " (" + pct + "%)</div>" +
      '<div class="progress"><div class="bar" style="width:' + pct + "%;background:" + barColor(pct) + '"></div></div>' +
      // Fixed layout so the column widths below are enforced: Status sits compact
      // on the left and the Rationale takes all the remaining space (there is no
      // Save column any more).
      '<table style="table-layout:fixed;width:100%"><colgroup><col style="width:4%">' +
      '<col style="width:30%"><col style="width:12%"><col style="width:54%"></colgroup>' +
      "<thead><tr><th>#</th><th>Question</th><th>Status</th><th>Rationale</th></tr>" +
      "</thead><tbody>" + rows + "</tbody></table>";
  },

  // W4a: 3×3 heatmap grid (Materiality × Complexity → RAG) for the model's
  // tier. The current cell is highlighted; the rating headline is its colour.
  heatmap(hm) {
    const tierCaption = hm.tier_label
      ? '<div class="section-header">' + esc(hm.tier_label) + " heatmap</div>"
      : "";
    // Axes and cell colours come from the division's policy (echoed on the envelope),
    // falling back to the classic Low/Medium/High + RAG palette for older payloads.
    const axes = hm.axes || {};
    const ratingColours = hm.rating_colours || RAG_COLORS;
    const matOrder = axes.materiality || ["Low", "Medium", "High"];
    const cols = axes.complexity || ["Low", "Medium", "High"];
    const rows = matOrder.slice().reverse();  // highest materiality at the top
    const grid = hm.grid || {};
    const cellRag = (m, c) => grid[m + "|" + c] || "";
    const table = rows.map(function (m) {
      const cells = cols.map(function (c) {
        const rag = cellRag(m, c);
        const bg = ratingColours[rag] || RAG_COLORS[rag] || "#9e9e9e";
        const here = (m === hm.materiality && c === hm.complexity);
        const style = "background:" + bg + "22;color:" + bg + ";" +
          (here ? "outline:3px solid " + bg + ";outline-offset:-3px;font-weight:800;" : "");
        return '<td class="hcell" style="' + style + '">' + esc(rag || "—") +
          (here ? '<br><span style="font-size:10px">YOU</span>' : "") + "</td>";
      }).join("");
      return "<tr><th>" + esc(m) + "</th>" + cells + "</tr>";
    }).join("");
    // Axis titles live outside the table so they can't stretch the row-label
    // column: materiality runs vertically down the left, complexity across
    // above the column headers.
    return tierCaption + '<div class="heatmap-wrap">' +
      '<div class="hm-y-axis">Materiality</div>' +
      "<div>" +
      '<div class="hm-x-axis">Complexity &rarr;</div>' +
      '<table class="heatmap"><thead><tr><th></th>' +
      cols.map((c) => "<th>" + esc(c) + "</th>").join("") +
      "</tr></thead><tbody>" + table + "</tbody></table>" +
      "</div></div>" +
      '<div class="muted" style="font-size:11px;margin-top:2px">' +
      "Set Materiality and Complexity on the Overview tab.</div>";
  },

  // W4c — chronological table of approved sign-offs on this model. Rendered
  // as a supporting section on the Risk Rating
  // tab. Empty when no sign-offs have been recorded yet.
  signoffHistory(history) {
    const items = history || [];
    if (!items.length) return "";
    const rows = items.map(function (s) {
      const outcome = s.outcome || "Approved";
      const oColor = outcome === "Rejected" ? "#d32f2f" : "#388e3c";
      return "<tr><td>" + fieldDisplay(s.date) + '</td><td style="color:' + oColor +
        ';font-weight:600">' + esc(outcome) + "</td><td>" +
        (s.from_rating ? ragBadge(s.from_rating) : '<span class="muted">—</span>') +
        "</td><td>" + ragBadge(s.to_rating) + "</td><td>" +
        fieldDisplay(s.meeting_id) + "</td><td>" + fieldDisplay(s.next_review_date) + "</td><td>" +
        fieldDisplay(s.note) + "</td></tr>";
    }).join("");
    return '<div class="section-header">Sign-off history</div>' +
      '<table class="signoff-history"><thead><tr><th>Date</th><th>Outcome</th><th>From</th><th>To</th>' +
      "<th>Meeting</th><th>Next review</th><th>Note</th></tr></thead><tbody>" + rows +
      "</tbody></table>";
  },

  risk(rating, showEvents = true) {
    const hm = rating.heatmap || {};
    const hmRag = hm.rag;
    const hmColor = RAG_COLORS[hmRag] || "#9e9e9e";
    const headline = hmRag
      ? '<div class="riskbanner" style="border-color:' + hmColor + ";background:" + hmColor + '14">' +
        '<div class="muted" style="text-align:center">HEATMAP RATING</div>' +
        '<div style="text-align:center;font-size:28px;font-weight:800;color:' + hmColor + '">' +
        esc(hmRag) + "</div>" +
        '<div style="text-align:center" class="muted">Materiality: <b>' + esc(hm.materiality) +
        "</b> &middot; Complexity: <b>" + esc(hm.complexity) + "</b></div></div>"
      : '<div class="riskbanner" style="border-color:#9e9e9e;background:#9e9e9e14">' +
        '<div class="muted" style="text-align:center">HEATMAP RATING</div>' +
        '<div style="text-align:center;font-size:16px" class="muted">Set Materiality and Complexity on Overview to place this model on the heatmap.</div>' +
        "</div>";
    // Events are a product-level (production) concern, so the count shows only on
    // products, not models.
    const events = showEvents ? '<div class="row" style="gap:16px;margin:12px 0"><div class="scard" ' +
      'style="border-left-color:#1976d2"><div class="lbl">Events (past ' + rating.events_window_days +
      ' days)</div><div class="val">' + rating.events_in_window + "</div></div></div>" : "";
    const signoff = this._signoffPanel(rating);
    // A prior sign-off made under an older categorisation is no longer valid: the owner
    // must re-confirm the classification and re-request MRC sign-off.
    const reclassify = rating.needs_reclassification
      ? '<div class="riskbanner" style="border-color:var(--amber);background:#fff8e1">' +
        '<div style="font-weight:700;color:#b26a00">Re-classification needed</div>' +
        '<div class="muted" style="font-size:12px">The division\'s risk categorisation has ' +
        "changed since this model was signed off. Re-confirm Materiality, Complexity and " +
        "Mission Criticality on Overview, then request MRC sign-off again.</div></div>"
      : "";
    return '<p class="muted">Risk rating is set by the owner via Materiality and Complexity ' +
      "(the heatmap), and takes effect once the MRC signs that cell off.</p>" +
      reclassify + headline + signoff + this.heatmap(hm) + events +
      this.signoffHistory(rating.signoff_history);
  },

  // W4c: sign-off state. A rating needs MRC sign-off until the committee has
  // actually approved the current heatmap RAG — this includes the case where the
  // owner and the heatmap already agree (agreement is not approval).
  _signoffPanel(rating) {
    const pending = rating.pending_signoff;
    const proposed = (rating.heatmap || {}).rag;
    if (pending) {
      const detail = pending.status === "Attached"
        ? 'on the agenda of <span class="code">' + esc(pending.meeting_id) + "</span> — " +
          esc(pending.meeting_title || "") +
          (pending.meeting_date ? " (" + esc(pending.meeting_date) + ")" : "")
        : "queued for <b>" + esc(pending.target_mrc || "its MRC") +
          "</b> — it will be added to that committee's next scheduled meeting";
      return '<div class="dz-row" style="border:1px solid #f57c00;background:#fff8e1;padding:10px 14px;border-radius:6px;margin:8px 0">' +
        '<div class="dz-text"><b>Pending MRC sign-off</b>' +
        '<p class="muted">Proposed <b>' + esc(pending.proposed_rag) + "</b> " + detail + ".</p></div></div>";
    }
    // Once the MRC has signed the current rating off, offer to revoke it (which
    // keeps the rating but returns the subject to needing sign-off).
    if (rating.signed_off) {
      return '<div class="dz-row" style="border:1px solid #388e3c;background:#e8f5e9;padding:10px 14px;border-radius:6px;margin:8px 0">' +
        '<div class="dz-text"><b>MRC signed off — ' + esc(proposed) + "</b>" +
        '<p class="muted">This rating has current MRC sign-off. Revoking keeps the rating but returns it to needing sign-off.</p></div>' +
        '<div class="dz-action"><button class="btn small danger" id="revoke-signoff">Revoke sign-off&hellip;</button></div></div>';
    }
    // Nothing to sign off until the owner has placed the model on the heatmap.
    if (!proposed) return "";
    const differs = proposed !== rating.approved_rag;
    const headline = differs
      ? "Heatmap " + esc(proposed) + " differs from approved " + esc(rating.approved_rag || "—")
      : esc(proposed) + " rating not yet signed off by the MRC";
    const sub = differs
      ? "Request an MRC sign-off to promote the heatmap rating to the approved rating."
      : "Owner and heatmap agree, but this rating still needs formal MRC sign-off.";
    return '<div class="dz-row" style="border:1px solid var(--line);padding:10px 14px;border-radius:6px;margin:8px 0">' +
      '<div class="dz-text"><b>' + headline + "</b>" +
      '<p class="muted">' + sub + "</p></div>" +
      '<div class="dz-action"><button class="btn small primary" id="req-signoff" data-proposed="' +
      esc(proposed) + '">Request MRC sign-off&hellip;</button></div></div>';
  },

  versions(data, spec, retired) {
    const items = data.version_history || [];
    const banner = '<div class="vbanner"><span class="muted">CURRENT VERSION</span> <b style="color:#1976d2">v' +
      fieldDisplay(data.version) + "</b></div>";
    const timeline = items.length ? items.map(function (v) {
      const rm = retired ? "" : ' <button class="btn small danger" data-rm="version_history|' + esc(v.item_id) + '">Remove</button>';
      return '<div class="vitem"><div><b>' + fieldDisplay(v.version) + "</b>" + lifecycleBadge(v.lifecycle) +
        '<span class="muted" style="float:right">' + fieldDisplay(v.date) + "</span></div><div>" +
        fieldDisplay(v.description) + '</div><div class="muted">Author: ' + fieldDisplay(v.author) +
        (v.ref_document ? " · Ref: " + esc(v.ref_document) : "") + "</div>" + rm + "</div>";
    }).join("") : '<div class="empty">No version history yet.</div>';
    const add = retired ? "" : '<div class="row" style="margin-top:10px">' +
      spec.fields.map((f) => '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
        inputControl("add-version_history-" + f.key, f) + "</div>").join("") +
      '<button class="btn small" data-add="version_history">Add version…</button></div>';
    return banner + timeline + add;
  },

  audit(events) {
    if (!events.length) return '<div class="empty">No recorded changes for this model yet.</div>';
    // A readable field label where we can resolve one, else the raw key.
    const label = (k) => { try { const s = Inventory.specByKey(k); return (s && s.label) || k; } catch (_) { return k; } };
    // Normalise each event into one or more {field, old, new} change rows. The
    // payloads already carry the diff: field updates hold from/value, collection
    // updates hold _changes {field:{from,to}}, document uploads are additions to
    // the documents collection. Reason is dropped as redundant.
    const changesFor = (e) => {
      const p = e.payload || {};
      switch (e.event_type) {
        case "ModelFieldUpdated":
        case "ProductFieldEdited":
        case "HandoffFieldUpdated":
          return [{ field: label(p.field), old: p.from, new: p.value }];
        case "ModelRegistered":
        case "ProductRegistered":
          return [{ field: "Registered", old: null, new: p.name || p.product || e.aggregate_id }];
        case "CollectionItemUpdated":
          if (p._changes) return Object.keys(p._changes).map((k) => (
            { field: (p.collection ? p.collection + " · " : "") + label(k), old: p._changes[k].from, new: p._changes[k].to }));
          return [{ field: (p.collection || "item") + " updated", old: null, new: p.item_id }];
        case "CollectionItemAdded":
          if (p.collection === "documents")
            return [{ field: "Document uploaded", old: null, new: p.original_name || p.filename }];
          return [{ field: (p.collection || "item") + " added", old: null,
                    new: p.description || p.title || p.value || p.question || p.item_id }];
        case "CollectionItemRemoved":
          return [{ field: (p.collection || "item") + " removed", old: p.item_id, new: null }];
        default:
          return [{ field: e.event_type, old: null, new: null }];
      }
    };
    const cell = (v) => (v === null || v === undefined || v === "" ? "—" : esc(String(v)));
    const rows = [];
    events.forEach((e) => {
      const when = e.recorded_at.replace("T", " ").slice(0, 19);
      changesFor(e).forEach((c) => {
        rows.push("<tr><td>" + esc(when) + "</td><td>" + esc(c.field) + "</td><td>" + cell(c.old) +
          "</td><td>" + cell(c.new) + "</td><td>" + esc(e.actor) + "</td></tr>");
      });
    });
    return "<table><thead><tr><th>When (UTC)</th><th>Field</th><th>Old</th><th>New</th><th>Actor</th>" +
      "</tr></thead><tbody>" + rows.join("") + "</tbody></table>";
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
