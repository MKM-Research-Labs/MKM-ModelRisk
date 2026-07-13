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

// MeetingDetail — the standing agenda items. Each of the five seeded items has a
// focused purpose: rollcall (confirm the meeting is open + quorate), sign-off of
// the previous minutes (attach + confirm), and read-only status lists for model
// sign-off and analysis. Confirmations record a minute.
Object.assign(MeetingDetail, {
  // Resolve a standing item's kind: the stored `kind`, or a title fallback for
  // meetings seeded before the kind field existed.
  _agendaKind(item) {
    if (item.kind) return item.kind;
    const t = (item.title || "").toLowerCase();
    if (t.indexOf("rollcall") >= 0) return "rollcall";
    if (t.indexOf("previous") >= 0 && t.indexOf("minutes") >= 0) return "minutes_signoff";
    if (t.indexOf("model sign-off") >= 0 || t.indexOf("model signoff") >= 0) return "review_signoff";
    if (t.indexOf("model analysis") >= 0) return "review_analysis";
    if (t.indexOf("aob") >= 0 || t.indexOf("other business") >= 0) return "aob";
    return "";
  },

  _agendaShell(item, idx, body, actions) {
    return '<div class="card" style="margin-bottom:8px" id="agrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b>" +
      (item.description ? '<div class="muted" style="margin-top:2px">' + esc(item.description) + "</div>" : "") +
      '</div><div class="rowact">' + (actions || "") + "</div></div>" + (body || "") + "</div>";
  },

  _standingCard(item, idx) {
    const kind = this._agendaKind(item);
    const done = item.status === "Completed";
    if (kind === "rollcall") {
      const q = this._quorum(this._meeting.data || {});
      const actions = done ? statusBadge("Completed")
        : '<button class="btn small primary" data-ag-confirm="rollcall" data-ag-id="' + esc(item.item_id) + '"' +
          (q.met ? "" : ' disabled title="Quorum not met"') + ">Confirm meeting open</button>";
      const body = '<div class="muted" style="margin-top:8px;font-size:12px">Chair calls the meeting to order; ' +
        "secretary confirms quorum. " + (q.met ? "Quorate." : "Not yet quorate.") + "</div>";
      return this._agendaShell(item, idx, body, actions);
    }
    if (kind === "minutes_signoff") {
      const actions = done ? statusBadge("Completed")
        : '<button class="btn small primary" data-ag-confirm="minutes" data-ag-id="' + esc(item.item_id) + '">Sign off</button>';
      const body = '<div style="margin-top:8px;font-size:12px">' + this._prevMinutesPicker(item) +
        '<div style="margin-top:6px">' + this._agendaDoc(item) + "</div></div>";
      return this._agendaShell(item, idx, body, actions);
    }
    const complete = (label) => done ? statusBadge("Completed")
      : '<button class="btn small primary" data-ag-confirm="' + kind + '" data-ag-id="' +
        esc(item.item_id) + '">' + label + "</button>";
    if (kind === "review_signoff") return this._agendaShell(item, idx, this._signoffStatusList(), complete("Mark reviewed"));
    if (kind === "review_analysis") return this._agendaShell(item, idx, this._analysisStatusList(), complete("Mark reviewed"));
    return this._agendaShell(item, idx,   // aob
      '<div class="muted" style="margin-top:8px;font-size:12px">Any other business raised by members.</div>',
      complete("Complete"));
  },

  // The previous-minutes chooser on the minutes sign-off item: pick a prior
  // closed meeting (from /prior-minutes) whose saved minutes are under review,
  // then download them. Selecting stores the reference on the agenda item.
  _prevMinutesPicker(item) {
    const prior = this._priorMinutes || [];
    if (!prior.length) return '<span class="muted">No prior meeting minutes on file.</span>';
    const opts = ['<option value="">&mdash; select previous meeting &mdash;</option>'].concat(
      prior.map((p) => '<option value="' + esc(p.meeting_id) + '"' +
        (p.meeting_id === item.prev_minutes_meeting ? " selected" : "") + ">" +
        esc((p.title || p.meeting_id) + (p.date ? " (" + p.date + ")" : "")) + "</option>")).join("");
    const dl = item.prev_minutes_meeting
      ? ' <a href="/api/meetings/' + esc(item.prev_minutes_meeting) +
        '/minutes.pdf" target="_blank">&darr; Previous minutes</a>' : "";
    return '<select data-prevmin="' + esc(item.item_id) + '">' + opts + "</select>" + dl;
  },

  // Read-only list of the meeting's sign-offs and their status (decisions taken
  // in the Models tab).
  _signoffStatusList() {
    const items = this._signoffItems();
    if (!items.length) {
      return '<div class="muted" style="margin-top:8px;font-size:12px">No sign-offs routed to this meeting.</div>';
    }
    return '<div style="margin-top:8px">' + items.map((it) => {
      const subj = it.subject_model_id || it.subject_product_id;
      return '<div class="prow"><div style="font-size:12px"><span class="code">' + esc(subj) + "</span> &rarr; " +
        ragBadge(it.proposed_rag) + "</div>" + statusBadge(it.status) + "</div>";
    }).join("") +
      '</div><p class="muted" style="font-size:11px;margin-top:6px">Decisions are taken in the Models tab (Approvals).</p>';
  },

  // Read-only list of in-scope models and their analysis outcome.
  _analysisStatusList() {
    const models = this._models || [];
    if (!models.length) {
      return '<div class="muted" style="margin-top:8px;font-size:12px">No models in scope.</div>';
    }
    return '<div style="margin-top:8px">' + models.map((m) =>
      '<div class="prow"><div style="font-size:12px"><span class="code">' + esc(m.model_id) + "</span></div>" +
      statusBadge(m.analysis_status || "Pending") + "</div>").join("") +
      '</div><p class="muted" style="font-size:11px;margin-top:6px">Outcomes are recorded in the Models tab (Analysis).</p>';
  },

  _bindStandingAgenda() {
    const self = this;
    document.querySelectorAll("[data-ag-confirm]").forEach(function (btn) {
      if (btn.disabled) return;
      const kind = btn.getAttribute("data-ag-confirm");
      const id = btn.getAttribute("data-ag-id");
      btn.onclick = () => self._confirmStanding(kind, id);
    });
    document.querySelectorAll("[data-prevmin]").forEach(function (sel) {
      const id = sel.getAttribute("data-prevmin");
      sel.onchange = function () {
        App.amend("Reference the previous minutes under review.", "POST",
          "/api/meetings/" + self._id + "/collections/agenda/" + id,
          { fields: { prev_minutes_meeting: sel.value } },
          () => self.show(self._id, "agenda"));
      };
    });
  },

  // The minute recorded when a standing agenda item is confirmed complete.
  _standingMinute(kind, d) {
    if (kind === "rollcall") return { title: "Meeting opened",
      text: "Meeting called to order by the chair" + (d.chair ? " (" + d.chair + ")" : "") +
        "; quorum confirmed by the secretary" + (d.secretary ? " (" + d.secretary + ")" : "") + "." };
    if (kind === "minutes") return { title: "Previous minutes signed off",
      text: "The minutes of the previous MRM were reviewed and signed off." };
    if (kind === "review_signoff") return { title: "Model sign-offs reviewed",
      text: "The committee reviewed the model risk-rating sign-offs tabled at this meeting (see the Models tab, Approvals)." };
    if (kind === "review_analysis") return { title: "Model analyses reviewed",
      text: "The committee reviewed the model analyses tabled at this meeting and confirmed the outcomes (see the Models tab, Analysis)." };
    return { title: "Any other business", text: "Any other business was invited by the chair." };
  },

  // Confirming a rollcall / minutes item records a minute, then marks the agenda
  // item Completed (the status update is pre-confirmed, so no second modal).
  _confirmStanding(kind, id) {
    const d = this._meeting.data || {};
    const self = this;
    const minute = this._standingMinute(kind, d);
    App.amend("Confirm — " + minute.title + ".", "POST",
      "/api/meetings/" + this._id + "/collections/minutes",
      { fields: { title: minute.title, text: minute.text, agenda_item_id: id } },
      () => {
        App.send("POST", "/api/meetings/" + self._id + "/collections/agenda/" + id,
          { fields: { status: "Completed" }, confirmed: true })
          .then(() => self.show(self._id, "agenda"))
          .catch(() => self.show(self._id, "agenda"));
      });
  },
});
