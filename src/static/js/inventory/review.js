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

// Detail — the Review tab: a model review run as a workflow, one stage at a time.
//
// A review is five pieces of work in a fixed order — read the pack, answer the
// nine questions, agree the weaknesses, agree the limitations of use, agree how
// the model will be monitored — ending in a reviewer sign-off. They used to be
// scattered across three tabs and the Overview, which left nobody able to say how
// far through a review actually was. The rail below is that answer.
//
// Built so far: the rail, the stages, the owner's brief, the reviewer's interim
// approval of each stage, both sides of the nine questions, and the record of
// challenge under each stage. The sign-off that files the report follows
// (see docs/design/review-workflow.md).
const REVIEW_STAGES = [
  { key: "documents", n: 0, label: "Preliminary documents" },
  { key: "assumptions", n: 1, label: "Assumptions" },
  { key: "questions", n: 2, label: "The nine questions" },
  { key: "weaknesses", n: 3, label: "Model weaknesses" },
  { key: "limitations", n: 4, label: "Limitations of use" },
  { key: "monitoring", n: 5, label: "Monitoring approach" },
  // Remediation is part of the review, not a parallel tab: what the review found and what
  // is being done about it belong together, and the committee should see the open steps
  // before it signs anything off — which is why this sits immediately before Sign-off.
  { key: "remediation", n: 6, label: "Remediation" },
  { key: "signoff", n: 7, label: "Sign-off" },
];
const REVIEW_DOC_CATEGORY = "Review";
// The brief the owner writes before the review starts, and who is to do it by when.
const REVIEW_BRIEF_FIELDS = ["review_trigger", "review_scope", "peer_reviewer",
  "review_due_date"];
// Shown only for a new version: the three documents that go stale together.
const NEW_VERSION_CHECKLIST = ["review_docs_updated", "review_sensitivities_updated",
  "review_test_docs_updated"];
const NEW_VERSION_TRIGGER = "New version";
// Mirrors config VALID_REVIEWER_VERDICTS (config/governance/_review.py).
const REVIEWER_VERDICTS = ["Not reviewed", "Accepted", "Challenged"];
// Why a review is being run comes from the server's specs (VALID_REVIEW_TRIGGERS in
// config/governance/_review.py), which is also what the start-cycle endpoint validates
// against. Copying the list here meant an adopter adding a trigger got it refused by a
// console still offering the old four. The fallback covers a spec that has not loaded.
const REVIEW_TRIGGERS_FALLBACK = ["Periodic", "New version", "Owner change", "MRC directed"];

Object.assign(Detail, {
  // Which stage is open. Held on Detail (not in the URL) so switching model tabs
  // and coming back leaves the reviewer where they were.
  _reviewStage: "documents",

  _reviewTab(d) {
    const rail = REVIEW_STAGES.map((s) =>
      '<button class="dtab' + (s.key === this._reviewStage ? " active" : "") +
      '" data-rstage="' + s.key + '">' + s.n + ". " + esc(s.label) +
      this._stageBadge(s.key, d) + "</button>").join("");
    return '<p class="muted" style="font-size:12px;margin:0 0 8px">The review, in the order it ' +
      "runs. Each stage is agreed between the model owner and the reviewer before the review " +
      "moves on; the reviewer signs off at the end and the report goes to the MRC with the " +
      "risk rating.</p>" +
      '<div class="dtabs">' + rail + "</div>" +
      '<div id="review-stage" style="margin-top:12px"></div>';
  },

  // What the stage has to show for itself: a tick once agreed, else a count of
  // the work in it — or nothing, where a count would mean nothing.
  _stageBadge(key, d) {
    const n = (k) => (d[k] || []).length;
    // An agreed stage says so, in place of its count: once the reviewer has
    // approved it, how many rows it holds is no longer the interesting fact.
    if ((d.review_progress || []).some((r) => r.stage === key)) return " ✓";
    if (key === "documents") {
      return " (" + DocLinks.countIn(d.documents, [REVIEW_DOC_CATEGORY]) + ")";
    }
    if (key === "questions") {
      const vq = d.validation_questions || [];
      return " (" + vq.filter((q) => q.status === "Addressed").length + "/" + vq.length + ")";
    }
    if (key === "assumptions") return " (" + n("assumptions") + ")";
    if (key === "weaknesses") return " (" + n("model_weaknesses") + ")";
    if (key === "limitations") return " (" + n("limitations") + ")";
    return "";
  },

  _renderReviewStage() {
    const d = this._model.data || {};
    const box = document.getElementById("review-stage");
    const docOpts = {
      category: REVIEW_DOC_CATEGORY, docs: d.documents || [], base: "/api/models/",
      id: this._id, retired: this._model.retired,
      refresh: () => this.show(this._id, "review", { scroll: false }),
    };
    if (this._reviewStage === "documents") {
      box.innerHTML = '<div class="section-header">The brief</div>' +
        '<p class="muted" style="font-size:12px">What this review is for, who is doing it, and ' +
        "by when. A reviewer handed a model and no brief writes the review they imagine is " +
        "wanted.</p>" +
        REVIEW_BRIEF_FIELDS.map((k) => this._row(k, d)).join("") +
        this._newVersionChecklist(d) +
        '<div class="section-header" style="margin-top:16px">Preliminary documents</div>' +
        '<p class="muted" style="font-size:12px">The pack the reviewer works from. These are ' +
        "the review's own working papers — the model's documentation lives on the Docs tab.</p>" +
        DocPanel.html(docOpts) + this._thread("documents", d) + this._stageApproval("documents", d);
      DocPanel.bind(docOpts);
      this._bindEdits();
      this._bindThread("documents");
      this._bindStageApproval("documents");
      return;
    }
    if (this._reviewStage === "assumptions") {
      box.innerHTML = '<p class="muted" style="font-size:12px">What the model takes to be true ' +
        "for its results to hold &mdash; and what is watched, or done, if one stops holding. " +
        "The sixth of the nine questions asks whether these are documented and justified, which " +
        "is why they are agreed before the questions rather than after.</p>" +
        this._collSection("assumptions", d) + this._thread("assumptions", d) +
        this._stageApproval("assumptions", d);
      this._bindCollections(["assumptions"]);
      this._bindThread("assumptions");
      this._bindStageApproval("assumptions");
      return;
    }
    if (this._reviewStage === "questions") {
      box.innerHTML = this._questionsTable(d) + this._thread("questions", d) + this._stageApproval("questions", d);
      this._bindValidationSaves();
      this._bindVerdictSaves();
      this._bindThread("questions");
      this._bindStageApproval("questions");
      return;
    }
    if (this._reviewStage === "weaknesses") {
      box.innerHTML = '<p class="muted" style="font-size:12px">What the model does badly, or ' +
        "not at all &mdash; proposed by the owner, agreed with the reviewer.</p>" +
        this._collSection("model_weaknesses", d) + this._thread("weaknesses", d) + this._stageApproval("weaknesses", d);
      this._bindCollections(["model_weaknesses"]);
      this._bindThread("weaknesses");
      this._bindStageApproval("weaknesses");
      return;
    }
    if (this._reviewStage === "limitations") {
      box.innerHTML = '<p class="muted" style="font-size:12px">Where the model may and may not ' +
        "be used, with the trigger that would surface a breach and the control that compensates.</p>" +
        this._collSection("limitations", d) + this._thread("limitations", d) + this._stageApproval("limitations", d);
      this._bindCollections(["limitations"]);
      this._bindThread("limitations");
      this._bindStageApproval("limitations");
      return;
    }
    if (this._reviewStage === "monitoring") {
      box.innerHTML = '<div class="section-header">Monitoring approach</div>' +
        '<p class="muted" style="font-size:12px">How this model will be watched once it is in ' +
        "use, in your own words &mdash; what would be looked at, how often, and what would " +
        "prompt a second look.</p>" + this._row("monitoring_approach", d) +
        this._thread("monitoring", d) + this._stageApproval("monitoring", d);
      this._bindEdits();
      this._bindThread("monitoring");
      this._bindStageApproval("monitoring");
      return;
    }
    if (this._reviewStage === "remediation") {
      box.innerHTML = '<div class="section-header">Remediation</div>' +
        '<p class="muted" style="font-size:12px">What the review found that has to be put ' +
        "right, and where each step has got to. The committee sees these before it signs the " +
        "review off.</p>" +
        this._collSection("remediation_steps", d) +
        this._thread("remediation", d) + this._stageApproval("remediation", d);
      this._bindCollections(["remediation_steps"]);
      this._bindThread("remediation");
      this._bindStageApproval("remediation");
      return;
    }
    box.innerHTML = this._signoffPanel(d);
    this._bindThread("signoff");
    this._bindSignoff();
    this._bindCycle();
  },

  // What stands between this review and its sign-off. Computed here from the same
  // facts the endpoint uses, so the button says exactly why it is disabled and the
  // server refuses for exactly those reasons.
  _signoffBlockers(d) {
    const agreed = new Set((d.review_progress || []).map((r) => r.stage));
    const out = REVIEW_STAGES.filter((s) => s.key !== "signoff" && !agreed.has(s.key))
      .map((s) => s.label + " not agreed");
    const notes = d.review_notes || [];
    const answered = new Set(notes.map((n) => n.resolves).filter(Boolean));
    const open = notes.filter((n) => n.kind === "Challenge" && !answered.has(n.item_id));
    if (open.length) {
      out.push(open.length + " open challenge" + (open.length === 1 ? "" : "s") +
        " (" + open.map((n) => n.item_id).join(", ") + ")");
    }
    return out;
  },

  // The filed report is served by document item, not by filename, so the link is
  // built from the document this sign-off produced.
  _reportLink(d, signoff) {
    const doc = (d.documents || []).find((x) => x.filename === signoff.report_filename);
    if (!doc) return "";
    return '<a class="btn small" style="margin-top:6px" target="_blank" rel="noopener" href="/api/models/' +
      esc(this._id) + "/documents/" + esc(doc.item_id) +
      '/download">&darr; Model Review Report</a>';
  },

  _signoffPanel(d) {
    const signed = (d.review_signoffs || []);
    const history = signed.map((s) =>
      '<div class="inforow"><div class="k">' + esc((s.signed_at || "").slice(0, 10)) +
      '</div><div class="v"><b>' + esc(s.signed_by || "") + "</b>" +
      '<div style="white-space:pre-wrap;margin-top:4px">' + esc(s.commentary || "") + "</div>" +
      this._reportLink(d, s) + "</div></div>").join("");
    const blockers = this._signoffBlockers(d);
    const gate = blockers.length
      ? '<div class="quorum-banner">The review is not finished: ' +
        esc(blockers.join("; ")) + ".</div>"
      : "";
    const form = this._model.retired ? "" :
      '<div class="field" style="margin-top:8px"><label for="rs-commentary">Final commentary</label>' +
      '<textarea id="rs-commentary" rows="4" placeholder="What the reviewer concludes, in ' +
      'their own words — this is printed in the report the committee reads"></textarea></div>' +
      '<button class="btn small primary" id="rs-signoff"' +
      (blockers.length ? " disabled" : "") + ">Sign off &amp; file the report&hellip;</button>";
    return this._nextCycle(d) + '<div class="section-header">Reviewer sign-off</div>' +
      '<p class="muted" style="font-size:12px">Signing off files the Model Review Report ' +
      "against this model &mdash; every stage, both sides of the nine questions, the registers " +
      "and the record of challenge. The MRC receives that report and signs off the risk " +
      "rating; it does not adjudicate the review.</p>" +
      (history ? '<div class="section-header" style="margin-top:12px">Signed</div>' + history : "") +
      gate + form + this._thread("signoff", d);
  },

  // Once a review is signed off, the tab's job is to start the next one — and to
  // say why it is happening, because what a reviewer should look at differs
  // between a periodic review, a new version, a change of owner and a direction
  // from the committee.
  _nextCycle(d) {
    const signed = (d.review_signoffs || []).length;
    const started = (d.review_progress || []).filter((r) => r.stage === "cycle-start").length;
    if (!signed || this._model.retired) return "";
    if (started > signed - 1 && d.review_status !== "Signed off") return "";
    return '<div class="section-header">Start the next review</div>' +
      '<p class="muted" style="font-size:12px">This review is signed off. Starting another ' +
      "clears the stages for the new one &mdash; nothing is erased: the approvals, the " +
      "record of challenge and the report just signed stay on the model.</p>" +
      '<div class="row" style="align-items:center">' +
      '<select id="rc-trigger">' +
      ((this._specs || {}).review_triggers || REVIEW_TRIGGERS_FALLBACK).map((x) =>
        "<option>" + esc(x) + "</option>").join("") + "</select>" +
      '<input id="rc-note" placeholder="Why now (optional)" style="flex:1">' +
      '<button class="btn small" id="rc-start">Start a review&hellip;</button></div>';
  },

  _bindCycle() {
    const btn = document.getElementById("rc-start");
    if (!btn) return;
    btn.onclick = () => {
      App.amend("Start a new review of " + this._id + ".", "POST",
        "/api/models/" + this._id + "/review/start-cycle",
        { trigger: val("rc-trigger"), note: val("rc-note") },
        () => { this._reviewStage = "documents"; this.show(this._id, "review", { scroll: false }); });
    };
  },

  _bindSignoff() {
    const btn = document.getElementById("rs-signoff");
    if (!btn || btn.disabled) return;
    btn.onclick = () => {
      const commentary = val("rs-commentary");
      if (!commentary) { App.toast("The sign-off needs your final commentary", "error"); return; }
      App.amend("Sign off the review of " + this._id + " and file the report.", "POST",
        "/api/models/" + this._id + "/review/sign-off", { commentary: commentary },
        () => this.show(this._id, "review", { scroll: false }));
    };
  },

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
        ? '<span class="muted" style="font-size:11px"> answering ' + esc(n.resolves) + "</span>" : "";
      return '<div style="padding:8px 0;border-bottom:1px solid var(--line)">' +
        '<div class="muted" style="font-size:11px">' + esc(n.author_role || "") + " &middot; " +
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
    const composer = this._model.retired ? "" :
      '<div class="row" style="margin-top:8px;align-items:flex-start">' +
      '<textarea id="rn-text-' + stage + '" rows="2" placeholder="Add a note, or raise a challenge" ' +
      'style="flex:1;resize:vertical"></textarea>' +
      '<select id="rn-kind-' + stage + '"><option>Note</option><option>Challenge</option></select>' +
      (answering ? '<select id="rn-resolves-' + stage + '"><option value="">&mdash;</option>' +
        answering + "</select>" : "") +
      '<button class="btn small primary" id="rn-post-' + stage + '">Post</button></div>';
    return '<div class="section-header" style="margin-top:16px">Record of challenge</div>' +
      '<p class="muted" style="font-size:12px">What the owner and the reviewer said to each ' +
      "other about this stage. Append-only, and printed in the report the MRC receives.</p>" +
      banner +
      (notes.length ? notes.map(line).join("") : '<div class="empty">Nothing said yet.</div>') +
      composer;
  },

  _bindThread(stage) {
    const btn = document.getElementById("rn-post-" + stage);
    if (!btn) return;
    btn.onclick = async () => {
      const text = val("rn-text-" + stage);
      if (!text) { App.toast("A note cannot be empty", "error"); return; }
      const resolves = document.getElementById("rn-resolves-" + stage);
      try {
        this._model = await App.send("POST", "/api/models/" + this._id + "/review/note",
          { stage: stage, text: text, kind: val("rn-kind-" + stage),
            resolves: resolves ? resolves.value : "" });
        App.toast("Note recorded", "ok");
        this._render();
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
    const questions = d.validation_questions || [];
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
    const ownerSelect = (q) => '<select data-vq-item="' + esc(q.item_id) + '" id="vq-' +
      esc(q.item_id) + '-status" style="width:100%">' + options(statuses, q.status) + "</select>";
    const verdictSelect = (q) => '<select data-vq-verdict="' + esc(q.item_id) + '" id="vq-verdict-' +
      esc(q.item_id) + '" style="width:100%">' +
      options(REVIEWER_VERDICTS, q.reviewer_verdict || REVIEWER_VERDICTS[0]) + "</select>";
    const rows = questions.map((q, i) => {
      const readOnly = this._model.retired;
      const owner = readOnly
        ? vqBadge(q.status) + '<div class="muted">' + fieldDisplay(q.rationale) + "</div>"
        : ownerSelect(q) +
          '<textarea data-vq-item="' + esc(q.item_id) + '" id="vq-' + esc(q.item_id) +
          '-rationale" rows="3" style="width:100%;resize:vertical;overflow-y:auto;margin-top:4px">' +
          esc(q.rationale || "") + "</textarea>";
      const stamp = q.reviewed_by
        ? '<div class="muted" style="font-size:11px">' + esc(q.reviewed_by) + " &middot; " +
          esc((q.reviewed_at || "").slice(0, 10)) + "</div>"
        : "";
      const reviewer = readOnly
        ? fieldDisplay(q.reviewer_verdict) + '<div class="muted">' +
          fieldDisplay(q.reviewer_comment) + "</div>" + stamp
        : verdictSelect(q) +
          '<textarea data-vq-verdict-item="' + esc(q.item_id) + '" id="vq-' + esc(q.item_id) +
          '-comment" rows="3" placeholder="Reviewer\'s comment" ' +
          'style="width:100%;resize:vertical;overflow-y:auto;margin-top:4px">' +
          esc(q.reviewer_comment || "") + "</textarea>" + stamp;
      return "<tr><td>" + (i + 1) + "</td><td><b>" + fieldDisplay(q.short_label) +
        '</b><br><span class="muted">' + fieldDisplay(q.question) + "</span></td><td>" +
        owner + "</td><td>" + reviewer + "</td></tr>";
    }).join("");
    return '<p class="muted">The nine SR 26-2 questions. The owner sets a status and a ' +
      "rationale; the reviewer accepts it or challenges it. Every change saves as you make " +
      "it, and who reviewed what is stamped from the signed-in identity.</p>" +
      '<div class="summary">' + card("Addressed", counts.Addressed, Theme.value("green")) +
      card("Partially", counts["Partially Addressed"], Theme.value("amber")) +
      card("Not Addressed", counts["Not Addressed"], Theme.value("red")) +
      card("Accepted", accepted, Theme.value("accent")) +
      card("Challenged", challenged, Theme.value("violet")) + "</div>" +
      '<div class="muted" style="margin-bottom:6px">Owner coverage: ' + counts.Addressed +
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
    if (this._model.retired) return;
    const self = this;
    const save = async (itemId) => {
      try {
        const updated = await App.send(
          "POST", "/api/models/" + self._id + "/review/question-verdict",
          { item_id: itemId, verdict: val("vq-verdict-" + itemId),
            comment: val("vq-" + itemId + "-comment") });
        self._model = updated;
        App.toast("Reviewer verdict recorded", "ok");
        self._render();
      } catch (e) {
        App.toast(e.message, "error");
      }
    };
    document.querySelectorAll("[data-vq-verdict], [data-vq-verdict-item]").forEach((el) => {
      el.onchange = () => save(el.getAttribute("data-vq-verdict") ||
        el.getAttribute("data-vq-verdict-item"));
    });
  },

  // The three documents that go stale together when a model is re-versioned. The
  // owner ticks each; alongside the tick we show what is actually on file, so the
  // confirmation is made against the record rather than from memory.
  _newVersionChecklist(d) {
    if (d.review_trigger !== NEW_VERSION_TRIGGER) return "";
    const held = {
      review_docs_updated: DocLinks.countIn(d.documents, ["Core Documentation"]),
      review_sensitivities_updated: DocLinks.countIn(d.documents, ["Sensitivity"]),
      review_test_docs_updated: DocLinks.countIn(d.documents, ["Test Results"]),
    };
    return '<div class="section-header" style="margin-top:16px">New version checklist</div>' +
      '<p class="muted" style="font-size:12px">This review follows a new version, so the ' +
      "model's own documents need to have caught up with it. The count beside each is what " +
      "is on file today.</p>" +
      NEW_VERSION_CHECKLIST.map((k) =>
        this._row(k, d).replace("</div><span class=\"edit-btn\"",
          '<span class="muted" style="font-size:11px;margin-left:10px">' +
          held[k] + " on file</span></div><span class=\"edit-btn\"")).join("");
  },

  // The reviewer's interim approval of a stage: the button, or the record of the
  // approval already given. Not a lock — the stage stays editable afterwards, and
  // approving again after a reopening simply adds another row.
  _stageApproval(stageKey, d) {
    const given = (d.review_progress || []).filter((r) => r.stage === stageKey).slice(-1)[0];
    const label = REVIEW_STAGES.find((s) => s.key === stageKey).label;
    const record = given
      ? '<div class="muted" style="font-size:12px">Interim approval by <b>' +
        esc(given.approved_by || "") + "</b> on " + esc((given.approved_at || "").slice(0, 10)) +
        (given.note ? ' &mdash; "' + esc(given.note) + '"' : "") + "</div>"
      : '<div class="muted" style="font-size:12px">Not yet agreed.</div>';
    if (this._model.retired) return '<div style="margin-top:16px">' + record + "</div>";
    return '<div class="section-header" style="margin-top:18px">Interim approval</div>' +
      '<p class="muted" style="font-size:12px">The reviewer agrees ' + esc(label.toLowerCase()) +
      " and the review moves on. This does not close the stage &mdash; it stays open if you " +
      "need to come back to it.</p>" + record +
      '<div class="row" style="margin-top:8px"><input id="rv-note" placeholder="Note (optional)" ' +
      'style="flex:1"><button class="btn small primary" data-rapprove="' + esc(stageKey) + '">' +
      (given ? "Approve again&hellip;" : "Interim approval&hellip;") + "</button></div>";
  },

  _bindStageApproval(stageKey) {
    const btn = document.querySelector('[data-rapprove="' + stageKey + '"]');
    if (!btn) return;
    btn.onclick = () => {
      const label = REVIEW_STAGES.find((s) => s.key === stageKey).label;
      const note = val("rv-note");
      App.amend('Interim approval of "' + label + '" for ' + this._id + ".", "POST",
        "/api/models/" + this._id + "/review/approve-stage", { stage: stageKey, note: note },
        () => {
          // Approving moves the review on: land the reviewer on the next stage.
          const i = REVIEW_STAGES.findIndex((s) => s.key === stageKey);
          this._reviewStage = REVIEW_STAGES[Math.min(i + 1, REVIEW_STAGES.length - 1)].key;
          this.show(this._id, "review", { scroll: false });
          Inventory.loadList();
        });
    };
  },

  _bindReviewRail() {
    document.querySelectorAll("[data-rstage]").forEach((btn) => {
      btn.onclick = () => {
        this._reviewStage = btn.getAttribute("data-rstage");
        this._renderContent();
      };
    });
    this._renderReviewStage();
  },
});
