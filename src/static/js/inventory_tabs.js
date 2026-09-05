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
const DetailTabs = {

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
