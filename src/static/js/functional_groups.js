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

// Admin -> Functional Groups. Per division, how it carves its estate up by function:
// "Storm Generation", "Flood Simulation", "Instrument Pricer". A different question from
// Type, which says what a record IS; this says what it is FOR.
//
// Same journey as the two policy editors beside it, deliberately: edits auto-save as a
// DRAFT proposed to the division's MRC, and records keep being filed against the last
// approved list until the committee signs the draft off. An admin who has set one of
// these should not have to learn the other.
//
// A record stores a group's ID and screens show its NAME, so renaming a group here moves
// nothing in the estate. Removing one WOULD strand whatever is filed under it, which is
// why the "Filed here" count sits beside each row and Remove is disabled while it is
// non-zero — the domain refuses the removal either way, but a count is an explanation
// and a refusal afterwards is a surprise.
const FunctionalGroupsEditor = {
  _division: null, _divisions: [], _groups: [], _detail: null, _box: null,

  async render(container) {
    this._box = container;
    const reg = await App.get("/api/functional-groups");
    this._divisions = Object.keys(reg.divisions || {});
    if (!this._division || this._divisions.indexOf(this._division) < 0) {
      this._division = this._divisions[0] || null;
    }
    await this._load();
  },

  async _load() {
    if (!this._division) {
      this._box.innerHTML = '<div class="empty">No divisions defined yet — add one under ' +
        "the Division tab, then say how it groups its estate here.</div>";
      return;
    }
    this._detail = await App.get("/api/functional-groups/" +
      encodeURIComponent(this._division));
    this._syncFromDetail();
    this._draw();
  },

  // Edit the pending draft if there is one, otherwise start from the live list. Copied
  // rather than referenced: the working list is edited in place, and mutating what the
  // response holds would leave the "live" it also carries reading as the draft.
  _syncFromDetail() {
    this._groups = JSON.parse(JSON.stringify(
      this._detail.draft || this._detail.live || []));
  },

  // How many live records are filed under a group. Absent for one that has not been
  // saved yet, which has no id to be filed under.
  _filed(group) {
    return (this._detail.in_use || {})[group.id] || 0;
  },

  // The server mints ids and is the authority on whether a list is legal, so a save
  // that succeeds replaces the working list with what was actually stored — that is how
  // a new group gets its FG-00n back.
  //
  // A save that fails reloads rather than leaving the screen ahead of the server. A
  // removal the domain refuses has already gone from the working list, and showing it
  // gone while it is still ratified is worse than making somebody retype a name.
  async _save() {
    const status = document.getElementById("fg-status");
    if (status) status.innerHTML = '<span class="muted">Saving…</span>';
    try {
      this._detail = await App.send("POST", "/api/functional-groups/" +
        encodeURIComponent(this._division) + "/propose", { groups: this._groups });
      this._syncFromDetail();
      this._draw();
    } catch (e) {
      App.toast(e.message || "Not saved", "error");
      await this._load();
    }
  },

  _draw() {
    this._box.innerHTML =
      PolicyEditor.header("fg", this._divisions, this._division) +
      '<p class="lead muted" style="font-size:var(--size-sm);max-width:74ch">A functional ' +
      "group says what a record is <em>for</em>, separately from what it is. Records are " +
      "filed under exactly one, and the registers lead with these groups rather than with " +
      "one long list. Edits save as a draft and are proposed to this division's MRC — " +
      "records keep being filed against the last approved list until the committee signs " +
      "it off.</p>" +
      '<div id="fg-list"></div>';
    this._drawStatus();
    this._drawList();
    PolicyEditor.bindDivision("fg", (d) => { this._division = d; this._load(); });
  },

  _drawStatus() {
    PolicyEditor.status("fg", this._detail.state,
      "Nothing ratified — this division has no groups yet, so no record can be filed " +
      "under one. Edits start a draft.");
  },

  _drawList() {
    const box = document.getElementById("fg-list");
    const rows = this._groups.length
      ? this._groups.map((g, i) => this._row(g, i)).join("")
      : '<tr><td colspan="5" class="empty">No groups yet. Add the first one below.</td></tr>';
    box.innerHTML =
      '<table class="grid"><thead><tr><th style="width:22%">Group</th>' +
      '<th style="width:44%">What it covers</th><th style="width:10%">ID</th>' +
      '<th style="width:10%">Filed here</th><th></th></tr></thead><tbody>' + rows +
      "</tbody></table>" +
      '<div class="add-form"><div class="field"><label>Group</label>' +
      '<input id="fg-new-name" placeholder="Storm Generation"></div>' +
      '<div class="field" style="flex:1;min-width:280px"><label>What it covers</label>' +
      '<input id="fg-new-desc"></div>' +
      '<div class="add-form-actions"><button class="btn small primary" id="fg-add">' +
      "Add group</button></div></div>";
    this._bind();
  },

  _row(group, i) {
    const filed = this._filed(group);
    // Removing a group strands whatever is filed under it, so the control is not
    // offered while anything is — the count beside it is the reason.
    const removable = filed === 0;
    return '<tr><td><input data-fg-f="name" data-fg-i="' + i + '" value="' +
      esc(group.name || "") + '"></td>' +
      '<td><input data-fg-f="description" data-fg-i="' + i + '" style="width:100%" value="' +
      esc(group.description || "") + '"></td>' +
      '<td><span class="code">' + esc(group.id || "—") + "</span></td>" +
      "<td>" + (filed
        ? esc(filed) + (filed === 1 ? " record" : " records")
        : '<span class="muted">none</span>') + "</td>" +
      '<td class="rowact">' +
      '<button class="edit-btn" data-fg-mv="up" data-fg-i="' + i + '" title="Move up"' +
      (i === 0 ? " disabled" : "") + ">↑</button>" +
      '<button class="edit-btn" data-fg-mv="down" data-fg-i="' + i + '" title="Move down"' +
      (i === this._groups.length - 1 ? " disabled" : "") + ">↓</button> " +
      '<button class="btn small danger" data-fg-rm="' + i + '"' +
      (removable ? "" : ' disabled title="' + esc(filed) +
        ' record(s) are filed here — refile them first"') +
      ">Remove</button></td></tr>";
  },

  _bind() {
    const self = this;
    this._box.querySelectorAll("[data-fg-f]").forEach((inp) => {
      inp.onchange = () => {
        self._groups[Number(inp.getAttribute("data-fg-i"))][inp.getAttribute("data-fg-f")] =
          inp.value;
        self._save();
      };
    });
    this._box.querySelectorAll("[data-fg-mv]").forEach((btn) => {
      btn.onclick = () => {
        const i = Number(btn.getAttribute("data-fg-i"));
        const j = btn.getAttribute("data-fg-mv") === "up" ? i - 1 : i + 1;
        if (j < 0 || j >= self._groups.length) return;
        const t = self._groups[i]; self._groups[i] = self._groups[j]; self._groups[j] = t;
        self._save();
      };
    });
    this._box.querySelectorAll("[data-fg-rm]").forEach((btn) => {
      btn.onclick = () => {
        self._groups.splice(Number(btn.getAttribute("data-fg-rm")), 1);
        self._save();
      };
    });
    const add = document.getElementById("fg-add");
    if (add) {
      add.onclick = () => {
        const name = (document.getElementById("fg-new-name").value || "").trim();
        if (!name) { App.toast("A group needs a name", "error"); return; }
        // No id: the server mints it, so two administrators drafting at once cannot
        // invent the same one.
        self._groups.push({ name: name,
                            description: document.getElementById("fg-new-desc").value || "" });
        self._save();
      };
    }
  },
};
