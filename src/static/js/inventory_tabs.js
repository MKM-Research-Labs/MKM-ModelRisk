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
  return pct >= 75 ? Theme.value("green") : pct >= 45 ? Theme.value("amber") : Theme.value("red");
}

const DetailTabs = {
  // The dimension names a division uses, from the risk-rating envelope. They fall back to
  // the built-in names only for a payload that predates the policy (never for a rename).
  axisLabels(hm) {
    const labels = (hm && hm.axis_labels) || {};
    return {
      mission_criticality: labels.mission_criticality || "Mission Criticality",
      materiality: labels.materiality || "Materiality",
      complexity: labels.complexity || "Complexity",
    };
  },

  // W4a: the Materiality × Complexity → RAG grid for the model's Mission-Criticality
  // band. The current cell is highlighted; the rating headline is its colour.
  heatmap(hm) {
    const labels = this.axisLabels(hm);
    // Captioned the way Admin → Risk captions the same table: the band's colour, the
    // dimension it belongs to, then the band itself.
    const tierCaption = hm.tier_label
      ? '<div class="grid-cap" style="display:flex;align-items:center;gap:var(--space-4);margin:var(--space-7) 0 var(--space-3)">' +
        '<span style="display:inline-block;width:12px;height:12px;border-radius:var(--radius-sm);background:' +
        esc(hm.tier_colour || Theme.value("grey")) + '"></span>' +
        '<span style="font-size:var(--size-xxs);text-transform:uppercase;color:var(--muted);letter-spacing:.04em">' +
        esc(labels.mission_criticality) + "</span>" +
        '<span style="font-size:14px;font-weight:700">' + esc(hm.tier_label) + "</span></div>"
      : "";
    // Axes and cell colours come from the division's policy (echoed on the envelope),
    // falling back to the classic Low/Medium/High + RAG palette for older payloads.
    const axes = hm.axes || {};
    const ratingColours = hm.rating_colours || {};
    const matOrder = axes.materiality || ["Low", "Medium", "High"];
    const cols = axes.complexity || ["Low", "Medium", "High"];
    const rows = matOrder.slice().reverse();  // highest materiality at the top
    const grid = hm.grid || {};
    const cellRag = (m, c) => grid[m + "|" + c] || "";
    const table = rows.map(function (m) {
      const cells = cols.map(function (c) {
        const rag = cellRag(m, c);
        const bg = ratingColours[rag] || Theme.hex("rag", rag) || Theme.value("grey");
        const here = (m === hm.materiality && c === hm.complexity);
        const style = "background:" + bg + "22;color:" + bg + ";" +
          (here ? "outline:3px solid " + bg + ";outline-offset:-3px;font-weight:800;" : "");
        return '<td class="hcell" style="' + style + '">' + esc(rag || "—") +
          (here ? '<br><span style="font-size:var(--size-xxs)">YOU</span>' : "") + "</td>";
      }).join("");
      return "<tr><th>" + esc(m) + "</th>" + cells + "</tr>";
    }).join("");
    // Axis titles live outside the table so they can't stretch the row-label
    // column: materiality runs vertically down the left, complexity across
    // above the column headers.
    return tierCaption + '<div class="heatmap-wrap">' +
      '<div class="hm-y-axis">' + esc(labels.materiality) + "</div>" +
      "<div>" +
      '<div class="hm-x-axis">' + esc(labels.complexity) + " &rarr;</div>" +
      '<table class="heatmap"><thead><tr><th></th>' +
      cols.map((c) => "<th>" + esc(c) + "</th>").join("") +
      "</tr></thead><tbody>" + table + "</tbody></table>" +
      "</div></div>" +
      '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-1)">' +
      esc(labels.materiality) + " and " + esc(labels.complexity) +
      " are set above; this table is the division's policy, not a per-model setting.</div>";
  },

  // W4c — chronological table of approved sign-offs on this model. Rendered
  // as a supporting section on the Risk Rating
  // tab. Empty when no sign-offs have been recorded yet.
  signoffHistory(history, division) {
    const items = history || [];
    if (!items.length) return "";
    const rows = items.map(function (s) {
      const outcome = s.outcome || "Approved";
      const oColor = outcome === "Rejected" ? Theme.value("red") : Theme.value("green");
      return "<tr><td>" + fieldDisplay(s.date) + '</td><td style="color:' + oColor +
        ';font-weight:600">' + esc(outcome) + "</td><td>" +
        (s.from_rating ? ragBadge(s.from_rating, division) : '<span class="muted">—</span>') +
        "</td><td>" + ragBadge(s.to_rating, division) + "</td><td>" +
        fieldDisplay(s.meeting_id) + "</td><td>" + fieldDisplay(s.next_review_date) + "</td><td>" +
        fieldDisplay(s.note) + "</td></tr>";
    }).join("");
    return '<div class="section-header">Sign-off history</div>' +
      '<table class="signoff-history"><thead><tr><th>Date</th><th>Outcome</th><th>From</th><th>To</th>' +
      "<th>Meeting</th><th>Next review</th><th>Note</th></tr></thead><tbody>" + rows +
      "</tbody></table>";
  },

  risk(rating, showEvents = true, division) {
    const hm = rating.heatmap || {};
    const labels = this.axisLabels(hm);
    const subject = showEvents ? "product" : "model";
    const hmRag = hm.rag;
    // The rating's colour is the division's, from the policy on the envelope — a renamed
    // or re-coloured rating shaded this banner with the built-in palette before.
    const hmColor = (hm.rating_colours || {})[hmRag] || Theme.hex("rag", hmRag) ||
      Theme.value("grey");
    const headline = hmRag
      ? '<div class="riskbanner" style="border-color:' + hmColor + ";background:" + hmColor + '14">' +
        '<div class="muted" style="text-align:center">HEATMAP RATING</div>' +
        '<div style="text-align:center;font-size:28px;font-weight:800;color:' + hmColor + '">' +
        esc(hmRag) + "</div>" +
        '<div style="text-align:center" class="muted">' + esc(labels.materiality) + ": <b>" +
        esc(hm.materiality) + "</b> &middot; " + esc(labels.complexity) + ": <b>" +
        esc(hm.complexity) + "</b></div></div>"
      : '<div class="riskbanner" style="border-color:var(--grey);background:' + Theme.value("grey") + '14">' +
        '<div class="muted" style="text-align:center">HEATMAP RATING</div>' +
        '<div style="text-align:center;font-size:var(--size-lg)" class="muted">Set ' +
        esc(labels.materiality) + " and " + esc(labels.complexity) + " above to place this " +
        subject + " on the heatmap.</div>" +
        "</div>";
    // Events are a product-level (production) concern, so the count shows only on
    // products, not models.
    const events = showEvents ? '<div class="row" style="gap:var(--space-8);margin:var(--space-6) 0"><div class="scard" ' +
      'style="border-left-color:var(--accent)"><div class="lbl">Events (past ' + rating.events_window_days +
      ' days)</div><div class="val">' + rating.events_in_window + "</div></div></div>" : "";
    const signoff = this._signoffPanel(rating);
    // A prior sign-off made under an older categorisation is no longer valid: the owner
    // must re-confirm the classification and re-request MRC sign-off.
    const reclassify = rating.needs_reclassification
      ? '<div class="riskbanner" style="border-color:var(--amber);background:var(--warn-bg)">' +
        '<div style="font-weight:700;color:var(--warn-ink-alt)">Re-classification needed</div>' +
        '<div class="muted" style="font-size:var(--size-sm)">The division\'s risk categorisation has ' +
        "changed since this " + subject + " was signed off. Re-confirm " +
        esc(labels.materiality) + ", " + esc(labels.complexity) + " and " +
        esc(labels.mission_criticality) +
        " above, then request MRC sign-off again.</div></div>"
      : "";
    return '<p class="muted">Risk rating is set by the owner via ' + esc(labels.materiality) +
      " and " + esc(labels.complexity) +
      " (the heatmap), and takes effect once the MRC signs that cell off.</p>" +
      reclassify + headline + signoff + this.heatmap(hm) + events +
      this.signoffHistory(rating.signoff_history, division);
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
      return '<div class="dz-row" style="border:1px solid var(--amber);background:var(--warn-bg);padding:var(--space-5) var(--space-7);border-radius:var(--radius-md);margin:var(--space-4) 0">' +
        '<div class="dz-text"><b>Pending MRC sign-off</b>' +
        '<p class="muted">Proposed <b>' + esc(pending.proposed_rag) + "</b> " + detail + ".</p></div></div>";
    }
    // A signed-off rating states its position and offers nothing to undo. There is
    // no unsigning a committee decision: a rating changes by re-classifying the
    // model, which moves the heatmap, which asks the MRC to sign off the new cell —
    // and that request appears below on its own.
    if (rating.signed_off) {
      return '<div class="dz-row" style="border:1px solid var(--green);background:var(--ok-bg);padding:var(--space-5) var(--space-7);border-radius:var(--radius-md);margin:var(--space-4) 0">' +
        '<div class="dz-text"><b>MRC signed off — ' + esc(proposed) + "</b>" +
        '<p class="muted">This rating has current MRC sign-off. To change it, revise the ' +
        "classification above; the heatmap moves and the new cell is sent to the MRC for " +
        "sign-off.</p></div></div>";
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
    return '<div class="dz-row" style="border:1px solid var(--line);padding:var(--space-5) var(--space-7);border-radius:var(--radius-md);margin:var(--space-4) 0">' +
      '<div class="dz-text"><b>' + headline + "</b>" +
      '<p class="muted">' + sub + "</p></div>" +
      '<div class="dz-action"><button class="btn small primary" id="req-signoff" data-proposed="' +
      esc(proposed) + '">Request MRC sign-off&hellip;</button></div></div>';
  },

  versions(data, spec, retired) {
    const items = data.version_history || [];
    const banner = '<div class="vbanner"><span class="muted">CURRENT VERSION</span> <b style="color:var(--accent)">v' +
      fieldDisplay(data.version) + "</b></div>";
    const timeline = items.length ? items.map(function (v) {
      const rm = retired ? "" : ' <button class="btn small danger" data-rm="version_history|' + esc(v.item_id) + '">Remove</button>';
      return '<div class="vitem"><div><b>' + fieldDisplay(v.version) + "</b>" + lifecycleBadge(v.lifecycle) +
        '<span class="muted" style="float:right">' + fieldDisplay(v.date) + "</span></div><div>" +
        fieldDisplay(v.description) + '</div><div class="muted">Author: ' + fieldDisplay(v.author) +
        (v.ref_document ? " · Ref: " + esc(v.ref_document) : "") + "</div>" + rm + "</div>";
    }).join("") : '<div class="empty">No version history yet.</div>';
    const add = retired ? "" : '<div class="row" style="margin-top:var(--space-5)">' +
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
