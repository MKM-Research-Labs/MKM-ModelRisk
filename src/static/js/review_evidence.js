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
// What a review actually recorded.
//
// The reviewer's answers to the questions, the verdict on each, the new-version
// checklist, and the thread of challenge that evidences them.
//
// The thread is append-only by design, not by accident: a challenge and its answer are
// the evidence that a review happened rather than was asserted, and evidence that can
// be edited afterwards is not evidence. See docs/design/review-workflow.md.
//
// Assigns onto ReviewPanel; loads after review_panel.js.

// How far through the questions the review is, as a colour. Lived in inventory_tabs.js,
// which never called it — this is its only caller.
function barColor(pct) {
  return pct >= 75 ? Theme.value("green") : pct >= 45 ? Theme.value("amber") : Theme.value("red");
}

Object.assign(ReviewPanel, {

  // The record of challenge: the exchange between owner and reviewer, under the
  // stage it happened on. It is not chat — it is the evidence that the model was
  // challenged, it is printed in the report the committee receives, and nothing
  // posted here can be edited or taken back. A correction is another note.
  _thread(stage, d) {
    const notes = (d.review_notes || []).filter((n) => n.stage === stage);
    const answered = new Set(notes.map((n) => n.resolves).filter(Boolean));
    const open = notes.filter((n) => n.kind === "Challenge" && !answered.has(n.item_id));
    const line = (n) => {
      const challenge = n.kind === "Challenge";
      const isOpen = challenge && !answered.has(n.item_id);
      const tag = challenge
        ? '<span class="pill" style="background:' + Theme.colour("review_thread", isOpen ? "open" : "answered") +
          ';color:var(--inverse)">' + (isOpen ? "Challenge — open" : "Challenge — answered") + "</span> "
        : "";
      const answers = n.resolves
        ? '<span class="muted" style="font-size:var(--size-xs)"> answering ' + esc(n.resolves) + "</span>" : "";
      return '<div style="padding:var(--space-4) 0;border-bottom:1px solid var(--line)">' +
        '<div class="muted" style="font-size:var(--size-xs)">' + esc(n.author_role || "") + " &middot; " +
        esc(n.author || "") + " &middot; " + esc((n.posted_at || "").replace("T", " ").slice(0, 16)) +
        " &middot; " + esc(n.item_id) + answers + "</div>" +
        tag + '<span style="white-space:pre-wrap">' + esc(n.text || "") + "</span></div>";
    };
    const banner = open.length
      ? '<div class="quorum-banner">' + open.length + " open challenge" +
        (open.length === 1 ? "" : "s") + " on this stage &mdash; a challenge is answered by " +
        "another note, never by deleting it.</div>"
      : "";
    const answering = open.map((n) =>
      '<option value="' + esc(n.item_id) + '">answers ' + esc(n.item_id) + " — " +
      esc((n.text || "").slice(0, 60)) + "</option>").join("");
    const composer = this._rvRetired() ? "" :
      '<div class="row" style="margin-top:var(--space-4);align-items:flex-start">' +
      '<textarea id="' + this._rvPfx() + 'rn-text-' + stage + '" rows="2" placeholder="Add a note, or raise a challenge" ' +
      'style="flex:1;resize:vertical"></textarea>' +
      '<select id="' + this._rvPfx() + 'rn-kind-' + stage + '"><option>Note</option><option>Challenge</option></select>' +
      (answering ? '<select id="' + this._rvPfx() + 'rn-resolves-' + stage + '"><option value="">&mdash;</option>' +
        answering + "</select>" : "") +
      '<button class="btn small primary" id="' + this._rvPfx() + 'rn-post-' + stage + '">Post</button></div>';
    return '<div class="section-header" style="margin-top:var(--space-8)">Record of challenge</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">What the owner and the reviewer said to each ' +
      "other about this stage. Append-only, and printed in the report the MRC receives.</p>" +
      banner +
      (notes.length ? notes.map(line).join("") : '<div class="empty">Nothing said yet.</div>') +
      composer;
  },

  _bindThread(stage) {
    const btn = this._rvEl("rn-post-" + stage);
    if (!btn) return;
    btn.onclick = async () => {
      const text = this._rvVal("rn-text-" + stage);
      if (!text) { App.toast("A note cannot be empty", "error"); return; }
      const resolves = this._rvEl("rn-resolves-" + stage);
      try {
        this._rvSet(await App.send("POST", this._rvApi() + this._rvId() + "/review/note",
          { stage: stage, text: text, kind: this._rvVal("rn-kind-" + stage),
            resolves: resolves ? resolves.value : "" }));
        App.toast("Note recorded", "ok");
        this._rvRerender();
      } catch (e) {
        App.toast(e.message, "error");
      }
    };
  },

  // The nine questions, both sides. The owner says what the model does; the
  // reviewer says whether that answer stands. They are shown on one row because
  // the disagreement between them is the point — a question can be Addressed by
  // its owner and Challenged by its reviewer, and a record that cannot hold that
  // is not recording a review.
  _questionsTable(d) {
    const questions = this._rvQuestions(d);
    const statuses = ["Addressed", "Partially Addressed", "Not Addressed", "Not Applicable"];
    const counts = { "Addressed": 0, "Partially Addressed": 0, "Not Addressed": 0, "Not Applicable": 0 };
    questions.forEach((q) => { if (counts[q.status] !== undefined) counts[q.status]++; });
    const challenged = questions.filter((q) => q.reviewer_verdict === "Challenged").length;
    const accepted = questions.filter((q) => q.reviewer_verdict === "Accepted").length;
    const total = questions.length;
    const pct = total ? Math.round((counts.Addressed / total) * 100) : 0;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    const options = (list, current) => list.map((o) =>
      "<option" + (o === current ? " selected" : "") + ">" + o + "</option>").join("");
    const ownerSelect = (q) => '<select data-vq-item="' + esc(q.item_id) + '" id="' + this._rvPfx() + 'vq-' +
      esc(q.item_id) + '-status" style="width:100%">' + options(statuses, q.status) + "</select>";
    const verdictSelect = (q) => '<select data-vq-verdict="' + esc(q.item_id) + '" id="' + this._rvPfx() + 'vq-verdict-' +
      esc(q.item_id) + '" style="width:100%">' +
      options(this._rvVerdicts(), q.reviewer_verdict || this._rvVerdicts()[0]) + "</select>";
    const rows = questions.map((q, i) => {
      const readOnly = this._rvRetired();
      const owner = readOnly
        ? vqBadge(q.status) + '<div class="muted">' + fieldDisplay(q.rationale) + "</div>"
        : ownerSelect(q) +
          '<textarea data-vq-item="' + esc(q.item_id) + '" id="' + this._rvPfx() + 'vq-' + esc(q.item_id) +
          '-rationale" rows="3" style="width:100%;resize:vertical;overflow-y:auto;margin-top:var(--space-2)">' +
          esc(q.rationale || "") + "</textarea>";
      const stamp = q.reviewed_by
        ? '<div class="muted" style="font-size:var(--size-xs)">' + esc(q.reviewed_by) + " &middot; " +
          esc((q.reviewed_at || "").slice(0, 10)) + "</div>"
        : "";
      const reviewer = readOnly
        ? fieldDisplay(q.reviewer_verdict) + '<div class="muted">' +
          fieldDisplay(q.reviewer_comment) + "</div>" + stamp
        : verdictSelect(q) +
          '<textarea data-vq-verdict-item="' + esc(q.item_id) + '" id="' + this._rvPfx() + 'vq-' + esc(q.item_id) +
          '-comment" rows="3" placeholder="Reviewer\'s comment" ' +
          'style="width:100%;resize:vertical;overflow-y:auto;margin-top:var(--space-2)">' +
          esc(q.reviewer_comment || "") + "</textarea>" + stamp;
      return "<tr><td>" + (i + 1) + "</td><td><b>" + fieldDisplay(q.short_label) +
        '</b><br><span class="muted">' + fieldDisplay(q.question) + "</span></td><td>" +
        owner + "</td><td>" + reviewer + "</td></tr>";
    }).join("");
    const stage = this._rvStages().find((x) => x.key === "questions") || {};
    return '<p class="muted">' + esc(stage.label || "The review questions") +
      ". The owner sets a status and a " +
      "rationale; the reviewer accepts it or challenges it. Every change saves as you make " +
      "it, and who reviewed what is stamped from the signed-in identity.</p>" +
      this._rvQuestionsLead() +
      '<div class="summary">' + card("Addressed", counts.Addressed, Theme.value("green")) +
      card("Partially", counts["Partially Addressed"], Theme.value("amber")) +
      card("Not Addressed", counts["Not Addressed"], Theme.value("red")) +
      card("Accepted", accepted, Theme.value("accent")) +
      card("Challenged", challenged, Theme.value("violet")) + "</div>" +
      '<div class="muted" style="margin-bottom:var(--space-3)">Owner coverage: ' + counts.Addressed +
      "/" + total + " (" + pct + "%)</div>" +
      '<div class="progress"><div class="bar" style="width:' + pct + "%;background:" +
      barColor(pct) + '"></div></div>' +
      '<table style="table-layout:fixed;width:100%"><colgroup><col style="width:4%">' +
      '<col style="width:28%"><col style="width:34%"><col style="width:34%"></colgroup>' +
      "<thead><tr><th>#</th><th>Question</th><th>Owner</th><th>Reviewer</th></tr>" +
      "</thead><tbody>" + rows + "</tbody></table>";
  },

  // The reviewer's verdict posts to its own endpoint, which stamps who and when.
  // Sending those from here would make the attribution the browser's word.
  _bindVerdictSaves() {
    if (this._rvRetired()) return;
    const self = this;
    const save = async (itemId) => {
      try {
        const updated = await App.send(
          "POST", self._rvApi() + self._rvId() + "/review/question-verdict",
          { item_id: itemId, verdict: self._rvVal("vq-verdict-" + itemId),
            comment: self._rvVal("vq-" + itemId + "-comment") });
        self._rvSet(updated);
        App.toast("Reviewer verdict recorded", "ok");
        self._render();
      } catch (e) {
        App.toast(e.message, "error");
      }
    };
    self._rvAll("[data-vq-verdict], [data-vq-verdict-item]").forEach((el) => {
      el.onchange = () => save(el.getAttribute("data-vq-verdict") ||
        el.getAttribute("data-vq-verdict-item"));
    });
  },

  // The three documents that go stale together when a model is re-versioned. The
  // owner ticks each; alongside the tick we show what is actually on file, so the
  // confirmation is made against the record rather than from memory.
  _newVersionChecklist(d) {
    if (d.review_trigger !== this._rvNewVersionTrigger()) return "";
    const held = {
      review_docs_updated: DocLinks.countIn(d.documents, ["Core Documentation"]),
      review_sensitivities_updated: DocLinks.countIn(d.documents, ["Sensitivity"]),
      review_test_docs_updated: DocLinks.countIn(d.documents, ["Test Results"]),
    };
    return '<div class="section-header" style="margin-top:var(--space-8)">New version checklist</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">This review follows a new version, so the ' +
      "model's own documents need to have caught up with it. The count beside each is what " +
      "is on file today.</p>" +
      this._rvChecklist().map((k) =>
        this._rvRow(k, d).replace("</div><span class=\"edit-btn\"",
          '<span class="muted" style="font-size:var(--size-xs);margin-left:var(--space-5)">' +
          held[k] + " on file</span></div><span class=\"edit-btn\"")).join("");
  },
});
