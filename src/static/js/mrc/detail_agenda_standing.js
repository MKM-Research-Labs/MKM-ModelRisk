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
      const body = '<div style="margin-top:8px;font-size:12px">' + this._agendaDoc(item) + "</div>";
      return this._agendaShell(item, idx, body, actions);
    }
    if (kind === "review_signoff") return this._agendaShell(item, idx, this._signoffStatusList(), "");
    if (kind === "review_analysis") return this._agendaShell(item, idx, this._analysisStatusList(), "");
    return this._agendaShell(item, idx,   // aob
      '<div class="muted" style="margin-top:8px;font-size:12px">Any other business raised by members.</div>', "");
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
  },

  // Confirming a rollcall / minutes item records a minute, then marks the agenda
  // item Completed (the status update is pre-confirmed, so no second modal).
  _confirmStanding(kind, id) {
    const d = this._meeting.data || {};
    const self = this;
    let title, text;
    if (kind === "rollcall") {
      title = "Meeting opened";
      text = "Meeting called to order by the chair" + (d.chair ? " (" + d.chair + ")" : "") +
        "; quorum confirmed by the secretary" + (d.secretary ? " (" + d.secretary + ")" : "") + ".";
    } else {
      title = "Previous minutes signed off";
      text = "The minutes of the previous MRM were reviewed and signed off.";
    }
    App.amend("Confirm — " + title + ".", "POST",
      "/api/meetings/" + this._id + "/collections/minutes",
      { fields: { title: title, text: text, agenda_item_id: id } },
      () => {
        App.send("POST", "/api/meetings/" + self._id + "/collections/agenda/" + id,
          { fields: { status: "Completed" }, confirmed: true })
          .then(() => self.show(self._id, "agenda"))
          .catch(() => self.show(self._id, "agenda"));
      });
  },
});
