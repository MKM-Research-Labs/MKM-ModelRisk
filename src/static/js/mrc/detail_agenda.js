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

// MeetingDetail — agenda. Each item on two rows (Title + Description up top, the
// rest below) with an add form and per-item edit/remove/document. Sign-off items
// are filtered out here (they render in the Models tab); escalation lives here.
Object.assign(MeetingDetail, {
  _agendaVisible() {
    return this.collSpec("agenda").fields.filter((f) => !f.hidden);
  },

  _agendaContent() {
    const items = ((this._meeting.data || {}).agenda || []).filter(
      (it) => !(it.subject_model_id || it.subject_product_id));
    const cards = items.length
      ? items.map((it, i) => this._agendaCard(it, i)).join("")
      : '<div class="empty">No agenda items yet.</div>';
    const addInputs = this._agendaVisible().map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("ag-add-" + f.key, f) + "</div>").join("");
    return '<div id="agenda-list">' + cards + "</div>" +
      '<div class="section-header" style="margin-top:14px">Add agenda item</div>' +
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' + addInputs +
      '<button class="btn small primary" id="ag-add">Add&hellip;</button></div>';
  },

  _agendaCard(item, idx) {
    const subjectId = item.subject_model_id || item.subject_product_id;
    const signoff = subjectId && item.proposed_rag;
    const meta = [];
    if (item.presenter) meta.push("Presenter: <b>" + esc(item.presenter) + "</b>");
    meta.push("Status: " + statusBadge(item.status));
    if (signoff) {
      meta.push('Sign-off: <span class="code">' + esc(subjectId) + "</span> &rarr; " +
        ragBadge(item.proposed_rag));
    }
    const pending = signoff && item.status === "Pending";
    // A sign-off item carries only the committee's decision — Sign off / Reject —
    // and the next review date it sets; both are reflected back to the subject.
    // Regular (non-sign-off) agenda items keep Edit / Remove.
    const actions = signoff
      ? (pending
          ? '<span class="muted" style="font-size:11px">Next review</span> ' +
            '<input type="date" id="ag-nextreview-' + esc(item.item_id) +
            '" value="' + oneYearAhead() +
            '" style="padding:3px 6px;font-size:11px"> ' +
            '<button class="btn small primary" data-agapprove="' + esc(item.item_id) +
            '">Sign off</button> ' +
            '<button class="btn small danger" data-agreject="' + esc(item.item_id) +
            '">Reject</button>'
          : "")
      : '<button class="btn small" data-aged="' + esc(item.item_id) + '">Edit</button> ' +
        '<button class="btn small danger" data-agrm="' + esc(item.item_id) + '">Remove</button>';
    const doc = '<input type="file" id="agdoc-file-' + esc(item.item_id) + '" style="display:none">' +
      (item.document_original_name
        ? '<a href="/api/meetings/' + esc(this._id) + "/agenda/" + esc(item.item_id) +
          '/document" target="_blank">' + esc(item.document_original_name) + "</a> "
        : '<span class="muted">No document. </span>') +
      '<button class="btn small" data-agdoc="' + esc(item.item_id) + '">' +
      (item.document_original_name ? "Replace" : "Attach") + " document&hellip;</button>";
    return '<div class="card" style="margin-bottom:8px" id="agrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b>" +
      (item.description ? '<div class="muted" style="margin-top:2px">' + esc(item.description) + "</div>" : "") +
      '</div><div class="rowact">' + actions + "</div></div>" +
      '<div class="muted" style="margin-top:8px">' + meta.join(" &nbsp;·&nbsp; ") + "</div>" +
      '<div style="margin-top:6px;font-size:12px">' + doc + "</div></div>";
  },

  _bindAgenda() {
    const self = this;
    const visible = this._agendaVisible();
    const items = (this._meeting.data || {}).agenda || [];
    const byId = (attr, el) => items.find((i) => i.item_id === el.getAttribute(attr));
    document.getElementById("ag-add").onclick = function () {
      const fields = {};
      visible.forEach((f) => { const v = val("ag-add-" + f.key); if (v !== "") fields[f.key] = v; });
      if (!fields.title) { App.toast("Title is required", "error"); return; }
      App.amend("Add an agenda item.", "POST",
        "/api/meetings/" + self._id + "/collections/agenda", { fields: fields },
        () => self.show(self._id, "agenda"));
    };
    document.querySelectorAll("[data-agrm]").forEach(function (btn) {
      const id = btn.getAttribute("data-agrm");
      btn.onclick = () => App.amend("Remove agenda item " + id + ".", "POST",
        "/api/meetings/" + self._id + "/collections/agenda/" + id + "/delete", {},
        () => self.show(self._id, "agenda"));
    });
    document.querySelectorAll("[data-aged]").forEach(function (btn) {
      btn.onclick = () => self._agendaEdit(byId("data-aged", btn), visible);
    });
    document.querySelectorAll("[data-agdoc]").forEach(function (btn) {
      const id = btn.getAttribute("data-agdoc");
      const fileInput = document.getElementById("agdoc-file-" + id);
      btn.onclick = function () { fileInput.click(); };
      fileInput.onchange = function () {
        if (!fileInput.files.length) return;
        const form = new FormData();
        form.append("file", fileInput.files[0]);
        fetch("/api/meetings/" + self._id + "/agenda/" + id + "/document", {
          method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
        }).then(async (res) => {
          if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
          App.toast("Document attached", "ok");
          self.show(self._id, "agenda");
        }).catch((e) => App.toast(e.message, "error"));
      };
    });
  },

  _agendaEdit(item, visible) {
    const card = document.getElementById("agrow-" + item.item_id);
    card.innerHTML =
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
      visible.map((f) => '<div class="field"><label>' + esc(f.label) + "</label>" +
        inputControl("ag-ed-" + f.key, f) + "</div>").join("") +
      '<button class="btn small primary" id="ag-save">Save&hellip;</button>' +
      '<button class="btn small" id="ag-cancel">Cancel</button></div>';
    visible.forEach((f) => {
      const el = document.getElementById("ag-ed-" + f.key);
      if (item[f.key] !== null && item[f.key] !== undefined) el.value = item[f.key];
    });
    document.getElementById("ag-cancel").onclick = () => this.show(this._id, "agenda");
    document.getElementById("ag-save").onclick = () => {
      const fields = {};
      visible.forEach((f) => { const v = val("ag-ed-" + f.key); if (v !== "") fields[f.key] = v; });
      App.amend("Update agenda item " + item.item_id + ".", "POST",
        "/api/meetings/" + this._id + "/collections/agenda/" + item.item_id, { fields: fields },
        () => this.show(this._id, "agenda"));
    };
  },

  // Phase MRC-4: reuse the sign-off picker overlay to choose which MRC the
  // escalation goes to. You pick a committee, not a specific meeting — it lands
  // on that MRC's soonest Scheduled meeting.
  async _openEscalatePicker(item) {
    const meetings = (await App.get("/api/meetings")).filter(
      (m) => m.status === "Scheduled" && m.meeting_id !== this._id && (m.data || {}).mrc,
    );
    // Group Scheduled meetings by their MRC; each committee routes to its
    // earliest-dated meeting (the option value the backend attaches to).
    const byMrc = {};
    meetings.forEach((m) => {
      const cur = byMrc[m.data.mrc];
      if (!cur || (m.data.date || "9999-99-99") < (cur.data.date || "9999-99-99")) {
        byMrc[m.data.mrc] = m;
      }
    });
    const mrcs = Object.keys(byMrc).sort();
    if (!mrcs.length) {
      App.toast("No other MRC has a Scheduled meeting to escalate to.", "error");
      return;
    }
    const pick = document.getElementById("signoff-meeting-pick");
    pick.innerHTML = mrcs.map((mrc) => {
      const m = byMrc[mrc];
      return "<option value=\"" + esc(m.meeting_id) + "\">" + esc(mrc) + " · " +
        esc(m.data.title || m.meeting_id) +
        (m.data.date ? " (" + esc(m.data.date) + ")" : "") + "</option>";
    }).join("");
    document.getElementById("signoff-summary").innerHTML =
      "Escalate sign-off for <b>" + esc(item.subject_model_id || item.subject_product_id) +
      "</b> → proposed <b>" + esc(item.proposed_rag) +
      "</b> to another MRC. It lands on that committee's next Scheduled meeting.";
    const overlay = document.getElementById("signoff-overlay");
    overlay.classList.remove("hidden");
    const self = this;
    document.getElementById("signoff-cancel").onclick = () => overlay.classList.add("hidden");
    document.getElementById("signoff-submit").onclick = () => {
      const parentMeetingId = pick.value;
      overlay.classList.add("hidden");
      App.amend("Escalate sign-off to " + parentMeetingId + ".", "POST",
        "/api/meetings/" + self._id + "/agenda/" + item.item_id + "/escalate-signoff",
        { parent_meeting_id: parentMeetingId }, () => self.show(self._id, self._tab));
    };
  },
});
