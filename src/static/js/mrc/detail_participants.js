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

// MeetingDetail — participants + quorum. The persistent left panel: the invitee
// roster with attendance, the live quorum badge, and the not-quorate lock that
// gates the meeting from proceeding.
Object.assign(MeetingDetail, {
  // The bound committee's roster, flattened to {name, role} rows.
  _rosterMembers(d) {
    const out = [];
    if (d.chair) out.push({ name: d.chair, role: "Chair" });
    if (d.secretary) out.push({ name: d.secretary, role: "Secretary" });
    (d.voting_members || []).forEach((n) => out.push({ name: n, role: "Voting" }));
    (d.non_voting_members || []).forEach((n) => out.push({ name: n, role: "Non-voting" }));
    return out;
  },

  // The meeting's invitees = the committee roster (Chair/Secretary/Voting/
  // Non-voting) plus any guests, each with an attendance status. Attendance is
  // recorded in the participants collection keyed by name: a roster member with
  // no record yet defaults to "Invited"; marking one adds/updates a record.
  // Guests are participant records with role "Guest".
  _invitees(d) {
    const byName = {};
    (d.participants || []).forEach((p) => { byName[p.name] = p; });
    const out = [];
    this._rosterMembers(d).forEach((m) => {
      const rec = byName[m.name];
      out.push({ name: m.name, role: m.role,
                 status: (rec && rec.status) || "Invited",
                 item_id: rec ? rec.item_id : null });
      delete byName[m.name];
    });
    Object.keys(byName).forEach((name) => {
      const p = byName[name];
      // Only genuine guests appear as extra invitees. A leftover record carrying a
      // roster role (Chair/Secretary/Voting/Non-voting) is a stale attendance
      // snapshot from a former committee line-up — that person has since been
      // taken off the committee, so they must no longer show here.
      const role = p.role || "Guest";
      if (role !== "Guest") return;
      out.push({ name: p.name, role: role,
                 status: p.status || "Invited", item_id: p.item_id });
    });
    return out;
  },

  // Is the meeting quorate? Evaluate who is marked "Attended" against the
  // committee's quorum rule (carried onto the meeting from the MRC). Defaults
  // when unset: require Chair + Secretary + 2 voting members (non-voting members
  // do not count towards quorum).
  _quorum(d) {
    d = d || {};
    const attended = this._invitees(d).filter((i) => i.status === "Attended");
    const has = (role) => attended.some((i) => i.role === role);
    const count = (role) => attended.filter((i) => i.role === role).length;
    const num = (v, dflt) => {
      if (v === undefined || v === null || v === "") return dflt;
      const n = parseInt(v, 10);
      return isNaN(n) ? dflt : n;
    };
    const reqChair = (d.quorum_require_chair || "Yes") !== "No";
    const reqSec = (d.quorum_require_secretary || "Yes") !== "No";
    const minVoting = num(d.quorum_min_voting, 2);
    const missing = [];
    if (reqChair && !has("Chair")) missing.push("Chair");
    if (reqSec && !has("Secretary")) missing.push("Secretary");
    const votingShort = minVoting - count("Voting");
    if (votingShort > 0) missing.push(votingShort + " more voting");
    return { met: missing.length === 0, missing };
  },

  // The persistent left panel: participant count, live quorum badge, and every
  // invitee with an attendance control. Guests can be added/removed here.
  _participantsPanel(d) {
    const inv = this._invitees(d);
    const q = this._quorum(d);
    const badge = q.met
      ? '<span class="badge" style="background:var(--green)">Quorum met</span>'
      : '<span class="badge" style="background:var(--red)">Quorum not met</span>' +
        (q.missing.length ? '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">Needs: ' +
          esc(q.missing.join(", ")) + "</div>" : "");
    const statusSel = (i) => {
      const opts = ["Invited", "Attended", "Apologies", "Declined"].map((s) =>
        "<option" + (s === i.status ? " selected" : "") + ">" + s + "</option>").join("");
      return '<select class="att-sel" data-att-name="' + esc(i.name) + '" data-att-role="' +
        esc(i.role) + '" data-att-id="' + esc(i.item_id || "") + '">' + opts + "</select>";
    };
    const rows = inv.length
      ? inv.map((i) => '<div class="prow"><div class="pwho"><b>' + esc(i.name) +
          '</b><span class="prole">' + esc(i.role) + "</span></div>" +
          '<div class="pact">' + statusSel(i) +
          (i.role === "Guest"
            ? ' <button class="btn small danger" data-guestrm="' + esc(i.item_id) +
              '" title="Remove guest">&times;</button>' : "") +
          "</div></div>").join("")
      : '<div class="empty" style="font-size:var(--size-sm)">No members yet — set them under Admin &rarr; MRC.</div>';
    // Guest candidates: people in the register who are neither invitees already.
    const present = {};
    inv.forEach((i) => { present[i.name] = true; });
    const candidates = (this._people || []).filter((p) => !present[p.name]);
    const options = ['<option value=""></option>'].concat(
      candidates.map((p) => "<option>" + esc(p.name) + "</option>")).join("");
    const picker = candidates.length
      ? '<div class="pguest"><select id="guest-pick">' + options + "</select>" +
        '<button class="btn small" id="guest-add">Add guest</button></div>'
      : '<p class="muted" style="font-size:var(--size-xs);margin-top:var(--space-4)">Everyone in the register is already an invitee.</p>';
    return '<div class="mtd-left"><div class="section-header">Participants (' + inv.length + ")</div>" +
      '<div style="margin:var(--space-3) 0">' + badge + "</div>" + rows +
      '<div class="section-header" style="margin-top:var(--space-6);font-size:var(--size-xs)">Add guest</div>' + picker + "</div>";
  },

  _bindParticipantsPanel(d) {
    const self = this;
    const base = "/api/meetings/" + self._id + "/collections/participants";
    document.querySelectorAll(".att-sel").forEach(function (sel) {
      sel.onchange = function () {
        const name = sel.getAttribute("data-att-name");
        const role = sel.getAttribute("data-att-role");
        const id = sel.getAttribute("data-att-id");
        const status = sel.value;
        if (id) {
          App.amend("Mark " + name + " " + status + " at " + self._id + ".", "POST",
            base + "/" + id, { fields: { status: status } },
            () => self.show(self._id, self._tab));
        } else {
          App.amend("Mark " + name + " " + status + " at " + self._id + ".", "POST",
            base, { fields: { name: name, role: role, status: status } },
            () => self.show(self._id, self._tab));
        }
      };
    });
    const add = document.getElementById("guest-add");
    if (add) {
      add.onclick = function () {
        const name = document.getElementById("guest-pick").value;
        if (!name) { App.toast("Pick a person to add as a guest", "error"); return; }
        App.amend("Add guest " + name + " to " + self._id + ".", "POST", base,
          { fields: { name: name, role: "Guest", status: "Invited" } },
          () => self.show(self._id, self._tab));
      };
    }
    document.querySelectorAll("[data-guestrm]").forEach(function (btn) {
      const id = btn.getAttribute("data-guestrm");
      btn.onclick = function () {
        App.amend("Remove guest from " + self._id + ".", "POST",
          base + "/" + id + "/delete", {}, () => self.show(self._id, self._tab));
      };
    });
  },

  // While not quorate, disable the actions that move the meeting forward: agenda
  // sign-off decisions and advancing the meeting Status.
  _applyQuorumLock() {
    document.querySelectorAll("#mtd-content [data-agapprove], #mtd-content [data-agreject]")
      .forEach(function (b) {
        b.disabled = true; b.style.opacity = "0.5"; b.style.pointerEvents = "none";
        b.title = "Quorum not met — confirm attendance first";
      });
    const st = document.querySelector('[data-minfo="status"]');
    if (st) { st.style.opacity = "0.5"; st.style.pointerEvents = "none"; st.title = "Quorum not met"; }
  },

  // The meeting's participants (roster + guests) — the presenter menu source.
  _participantNames(d) {
    const names = this._rosterMembers(d).map((m) => m.name);
    (d.participants || []).forEach((g) => { if (g.name) names.push(g.name); });
    return [...new Set(names)];
  },
});
