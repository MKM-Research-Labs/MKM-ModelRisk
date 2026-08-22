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

// Tabbed MRC meeting detail (the MeetingDetail package). This core module owns
// the shell: state, the render loop, the header/info bar, tab routing, and the
// info-bar field editor. The participants/quorum, minutes, agenda, sign-off and
// models sections augment MeetingDetail from their own modules (loaded after).

// Sensible default for a sign-off's next review date: one year out. The
// committee can still change it before signing off.
// Mirrors config CLOSED_MEETING_STATUS.
const CLOSED_MEETING_STATUS = "Completed";

function oneYearAhead() {
  const d = new Date();
  d.setFullYear(d.getFullYear() + 1);
  return d.toISOString().slice(0, 10);
}

const MeetingDetail = {
  _id: null, _meeting: null, _specs: null, _models: [], _inventory: [], _products: [],
  _tab: "agenda", _showAll: false,

  async show(meetingId, tab) {
    this._id = meetingId;
    this._specs = await MRC.specs();
    this._meeting = await App.get("/api/meetings/" + meetingId);
    this._models = await App.get("/api/meetings/" + meetingId + "/models");
    this._meetingProducts = await App.get("/api/meetings/" + meetingId + "/products");
    this._inventory = await App.get("/api/models");
    this._products = await App.get("/api/products");
    this._people = (await App.get("/api/reference")).data.people || [];
    // Prior closed meetings (same MRC) with saved minutes — offered on the
    // previous-minutes sign-off item.
    this._priorMinutes = await App.get("/api/meetings/" + meetingId + "/prior-minutes");
    // The membership/role changes waiting on this committee, for the standing item.
    this._membership = (await App.get("/api/meetings/" + meetingId + "/membership")).proposals || [];
    // The division's risk-categorisation state, so a pending draft surfaces as an AOB
    // agenda item for this meeting to sign off.
    const division = (this._meeting.data || {}).division;
    this._categorisation = division
      ? await App.get("/api/risk-policy/" + encodeURIComponent(division)) : null;
    if (tab) this._tab = tab;
    this._render();
    document.getElementById("mt-detail").scrollIntoView({ block: "start" });
  },

  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  // The friendly name for a model/product id (resolved from the loaded inventory
  // / product lists), so the name shows against every bare id.
  _subjectName(id) {
    if (!id) return "";
    const m = (this._inventory || []).find((x) => x.model_id === id);
    if (m) return (m.data || {}).name || "";
    const p = (this._products || []).find((x) => x.product_id === id);
    return p ? (p.data || {}).product || "" : "";
  },

  // "<code>id</code> name" for display wherever a subject id appears.
  _subjectLabelHtml(id) {
    const n = this._subjectName(id);
    return '<span class="code">' + esc(id) + "</span>" + (n ? " " + esc(n) : "");
  },

  _render() {
    const m = this._meeting, d = m.data || {};
    // Participants live in a persistent left panel (with the live quorum badge)
    // beside the tabbed content. A meeting that is not quorate cannot proceed:
    // a banner shows, and the forward-moving actions are disabled below.
    const q = this._quorum(d);
    const banner = q.met ? "" :
      '<div class="quorum-banner">Quorum not met — this meeting cannot proceed until it is quorate' +
      (q.missing.length ? " (needs " + esc(q.missing.join(", ")) + ")" : "") + ".</div>";
    document.getElementById("mt-detail").innerHTML =
      '<div class="card">' + this._header(m, d) + this._info(d) +
      '<div class="mtd-cols">' + this._participantsPanel(d) +
      '<div class="mtd-main">' + banner + this._tabbar(d) +
      '<div id="mtd-content"></div></div></div></div>';
    document.querySelectorAll("[data-mtab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-mtab"); this._render(); };
    });
    this._bindInfo(d);
    this._bindParticipantsPanel(d);
    this._renderContent();
    if (!q.met) this._applyQuorumLock();
  },

  _header(m, d) {
    // Right-hand actions: the pack PDF is always available; once the meeting is
    // closed its saved minutes download; while Scheduled the chair can Close it
    // (gated until quorate + every agenda item is resolved).
    const right = ['<button class="btn small" id="mt-pdf">&darr; Meeting Pack PDF</button>'];
    if (d.minutes_filename) {
      right.push('<a class="btn small" href="/api/meetings/' + esc(m.meeting_id) +
        '/minutes.pdf" target="_blank">&darr; Minutes</a>');
    }
    if (m.status !== "Completed") {
      const block = this._closeBlockers(d);
      right.push('<button class="btn small primary" id="mt-close"' +
        (block ? ' disabled title="' + esc(block) + '"' : "") + ">Close meeting&hellip;</button>");
    }
    // The title is edited here, on the heading itself, rather than down in the
    // info bar: it is the thing you read to know which meeting you are in. It
    // goes through the same field editor as the logistics, so a rename is on the
    // audit trail — and a closed meeting withdraws the affordance, as the info
    // fields do, because the domain will not amend a finished record.
    const rename = m.status === CLOSED_MEETING_STATUS ? "" :
      ' <span class="edit-btn" data-minfo="title">rename</span>';
    return '<div class="detail-header"><div>' +
      '<button class="btn small" id="mt-back">&larr; Back</button> ' +
      '<span class="name" id="minfo-title" style="margin-left:8px">' +
      esc(d.title || m.meeting_id) + rename + "</span> " +
      statusBadge(m.status) + "</div>" +
      '<div class="right">' + right.join(" ") + "</div></div>";
  },

  // Why the meeting can't be closed yet, or "" when it can. Closing needs a
  // quorate meeting whose agenda has been fully worked through.
  _closeBlockers(d) {
    if (!this._quorum(d).met) return "Quorum not met";
    const open = (d.agenda || []).filter((a) => (a.status || "Pending") === "Pending");
    if (open.length) return "Agenda items still open: " +
      open.map((a) => a.title || a.item_id).join(", ");
    return "";
  },

  _info(d) {
    // mrc + org tier and chair are derived from the MRC binding, so they stay
    // read-only — they change by re-binding the meeting, not by typing here.
    // Date, time and location are the meeting's own logistics and do move: rooms
    // change and meetings get postponed, and a governance record that cannot
    // record that is a record people keep somewhere else. Status is the lifecycle
    // control (Scheduled → Completed). Every one of these goes through the same
    // confirm-to-amend path, so a rescheduling is on the audit trail.
    const readOnly = (label, key) => '<span class="datechip" id="minfo-' + key + '">' +
      '<span class="muted">' + label + ':</span> <b>' + fieldDisplay(d[key]) + "</b></span>";
    // A closed meeting is a finished record: the domain refuses to amend it, so
    // the console withdraws the edit affordance rather than offering an action
    // that can only fail.
    const closed = this._meeting.status === CLOSED_MEETING_STATUS;
    const editable = (label, key) => closed ? readOnly(label, key) :
      '<span class="datechip" id="minfo-' + key + '"><span class="muted">' +
      label + ':</span> <b>' + fieldDisplay(d[key]) + "</b> " +
      '<span class="edit-btn" data-minfo="' + key + '">edit</span></span>';
    return '<div class="dh-dates">' + readOnly("MRC", "mrc") + readOnly("Division", "division") +
      readOnly("Line of Business", "line_of_business") + readOnly("Chair", "chair") + "</div>" +
      '<div class="dh-dates">' + editable("Date", "date") + editable("Time", "time") +
      editable("Location", "location") + editable("Status", "status") + "</div>";
  },

  _tabbar(d) {
    // The agenda badge counts only what the tab shows — sign-off items render in
    // the Signoff tab, so they don't inflate the agenda count.
    const n = (k) => {
      const arr = d[k] || [];
      if (k === "agenda") return arr.filter((a) => !subjectOf(a)).length;
      if (k === "models_in_scope") {
        // Signoff tab: risk-rating sign-offs (Approvals) + in-scope analysis
        // items (models + products).
        const signoffs = (d.agenda || []).filter(subjectOf).length;
        return signoffs + arr.length + (d.products_in_scope || []).length;
      }
      return arr.length;
    };
    // Participants moved out to the persistent left panel — no longer a tab.
    const tabs = [
      ["agenda", "Agenda"], ["models_in_scope", "Signoff"], ["actions", "Actions"],
      ["minutes", "Minutes"],
    ];
    return '<div class="dtabs">' + tabs.map((t) =>
      '<button class="dtab' + (t[0] === this._tab ? " active" : "") + '" data-mtab="' + t[0] + '">' +
      esc(t[1]) + " (" + n(t[0]) + ")</button>").join("") + "</div>";
  },

  _renderContent() {
    const d = this._meeting.data || {};
    const box = document.getElementById("mtd-content");
    if (this._tab === "models_in_scope") { box.innerHTML = this._modelsTab(); this._bindModels(); return; }
    // Agenda has a bespoke two-row layout (Title + Description on top, the rest
    // below) with its own add/edit/remove + sign-off actions.
    if (this._tab === "agenda") { box.innerHTML = this._agendaContent(); this._bindAgenda(); return; }
    if (this._tab === "documents") {
      box.innerHTML = '<div class="empty">Document uploads are coming next.</div>'; return;
    }
    // Minutes has a bespoke form: presenter from the participants, a related
    // model/product picker, and an expandable text box.
    if (this._tab === "minutes") { box.innerHTML = this._minutesContent(); this._bindMinutes(); return; }
    // Actions are cards, not table rows: each carries owners and its own update history.
    if (this._tab === "actions") { box.innerHTML = this._actionsContent(); this._bindActions(); return; }
    const spec = this.collSpec(this._tab);
    // Decisions accept multiple new entries at once; participants, minutes and
    // actions have their own bespoke tabs.
    const bulk = this._tab === "decisions";
    box.innerHTML = Collections.render(d, { collections: [spec] }, false, bulk);
    Collections.bind("/api/meetings/" + this._id + "/collections/", { collections: [spec] },
      false, () => this.show(this._id, this._tab), d, bulk);
  },

  // The AOB agenda item's risk-categorisation sign-off block, shown when the meeting's
  // division has a pending draft and the meeting is still open — a one-off item raised
  // under Any Other Business for the committee to ratify. Empty otherwise.
  _categorisationAob() {
    const detail = this._categorisation;
    const division = (this._meeting.data || {}).division;
    if (!division || !detail || detail.state !== "draft") return "";
    if (this._meeting.status === CLOSED_MEETING_STATUS) return "";
    const draft = detail.draft;
    const ratings = (draft.risk_ratings || []).map((r) =>
      '<span class="ragdot"><span class="dot" style="background:' + esc(r.colour) +
      '"></span><span style="color:' + esc(r.colour) + '">' + esc(r.name) +
      "</span></span>").join(" &nbsp; ");
    const doc = detail.document
      ? '<a href="/api/risk-policy/' + encodeURIComponent(division) + '/document" target="_blank">↓ ' +
        esc(detail.document.original_name) + "</a>"
      : '<span class="muted">none uploaded</span>';
    return '<div style="margin-top:10px;padding:10px 12px;border:1px solid var(--amber);' +
      'border-radius:6px;background:var(--warn-bg)">' +
      '<b>Risk categorisation sign-off &mdash; ' + esc(division) + "</b>" +
      '<p class="muted" style="font-size:12px;margin:4px 0">' + esc(division) + " has proposed a " +
      "revised risk categorisation. Approving it makes it live for this division's models; the " +
      "current categorisation stays in force until then.</p>" +
      '<div style="font-size:12px">Ratings: ' + ratings + "</div>" +
      '<div style="font-size:12px;margin-top:4px">Risk Policy document: ' + doc + " &nbsp;|&nbsp; " +
      '<a href="/api/risk-policy/' + encodeURIComponent(division) +
      '/categorisation.pdf" target="_blank">↓ Proposed categorisation (PDF)</a></div>' +
      '<div class="row" style="margin-top:8px;gap:8px">' +
      '<button class="btn small primary" id="aob-cat-approve">Approve &amp; make live</button>' +
      '<button class="btn small danger" id="aob-cat-reject">Reject</button></div></div>';
  },

  async _decidePolicy(division, action) {
    try {
      await App.send("POST", "/api/risk-policy/" + encodeURIComponent(division) + "/" + action,
        { meeting_id: this._id, confirmed: true });
      App.toast("Risk categorisation " + (action === "approve" ? "approved and live" : "rejected"), "ok");
      this.show(this._id, this._tab);   // reload so the AOB item reflects the new state
    } catch (e) { App.toast(e.message || "failed", "error"); }
  },

  _bindInfo(d) {
    const self = this;
    document.getElementById("mt-back").onclick = function () {
      document.getElementById("mt-detail").innerHTML = ""; MRC.loadList();
    };
    document.getElementById("mt-pdf").onclick = function () {
      window.open("/api/meetings/" + self._id + "/pack.pdf", "_blank");
    };
    const closeBtn = document.getElementById("mt-close");
    if (closeBtn && !closeBtn.disabled) {
      closeBtn.onclick = function () {
        App.amend("Close " + self._id + " — this generates and files the minutes.",
          "POST", "/api/meetings/" + self._id + "/close", {},
          () => self.show(self._id, self._tab));
      };
    }
    document.querySelectorAll("[data-minfo]").forEach(function (btn) {
      const key = btn.getAttribute("data-minfo");
      btn.onclick = function () { self._editField(key, d[key]); };
    });
  },

  _editField(key, current) {
    const f = MRC.specFieldByKey(key);
    const chip = document.getElementById("minfo-" + key);
    chip.innerHTML = inputControl("mf-input", f) +
      '<button class="btn small primary" id="mf-save">Save</button>' +
      '<button class="btn small" id="mf-cancel">Cancel</button>';
    const input = document.getElementById("mf-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("mf-cancel").onclick = () => this.show(this._id, this._tab);
    document.getElementById("mf-save").onclick = () => {
      // A required field cannot be emptied — clearing the title would leave the
      // meeting headed by its bare id in every list, pack and minute.
      if (f.required && !input.value.trim()) {
        App.toast(f.label + " cannot be empty", "error");
        return;
      }
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/meetings/" + this._id + "/field", { field: key, value: input.value.trim() },
        () => { this.show(this._id, this._tab); MRC.loadList(); });
    };
  },
};
