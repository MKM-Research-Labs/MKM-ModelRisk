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

// Admin -> ML Review Policy. Per division, the institution says which of the review
// catalogue it actually asks for, and which of that a review cannot be completed
// without. Two ticks per item, nothing else.
//
// Same journey as the risk policy editor beside it, deliberately: edits auto-save as a
// DRAFT proposed to the division's MRC, and ML Applications keep being reviewed against
// the last approved policy until the committee signs the draft off. An admin who has
// set one of these should not have to learn the other.
const MlReviewPolicyEditor = {
  _division: null, _divisions: [], _policy: null, _detail: null, _box: null,

  async render(container) {
    this._box = container;
    const reg = await App.get("/api/ml-review-policy");
    this._divisions = Object.keys(reg.divisions || {});
    if (!this._division || this._divisions.indexOf(this._division) < 0) {
      this._division = this._divisions[0] || null;
    }
    await this._load();
  },

  async _load() {
    if (!this._division) {
      this._box.innerHTML = '<div class="empty">No divisions defined yet — add one under ' +
        "the Division tab, then set what its ML reviews ask for here.</div>";
      return;
    }
    this._detail = await App.get("/api/ml-review-policy/" +
      encodeURIComponent(this._division));
    // Edit the pending draft if there is one, otherwise start from the live policy.
    this._policy = JSON.parse(JSON.stringify(this._detail.draft || this._detail.live || {}));
    this._draw();
  },

  // An item the institution has said nothing about: in use, not mandatory. The same
  // default the domain resolves to, so the tick a user sees is the tick that applies.
  _setting(id) {
    const stored = this._policy[id] || {};
    const inUse = stored.in_use !== undefined ? !!stored.in_use : true;
    return { in_use: inUse, mandatory: inUse && !!stored.mandatory };
  },

  // Ticking mandatory ticks in use; un-ticking in use clears mandatory. Enforced here
  // AND in the domain rules -- the UI keeps it coherent while you click, the rules keep
  // it true for anything that never went through this screen.
  _set(id, flag, on) {
    const now = this._setting(id);
    now[flag] = on;
    if (flag === "mandatory" && on) now.in_use = true;
    if (flag === "in_use" && !on) now.mandatory = false;
    // Store only what differs from the default, so a ratified policy is a short
    // document listing what the institution actually changed.
    if (now.in_use && !now.mandatory) delete this._policy[id];
    else this._policy[id] = now;
    this._save();
  },

  async _save() {
    const status = document.getElementById("mrp-status");
    if (status) status.innerHTML = '<span class="muted">Saving…</span>';
    try {
      this._detail = await App.send("POST", "/api/ml-review-policy/" +
        encodeURIComponent(this._division) + "/propose", { policy: this._policy });
      this._draw();
    } catch (e) {
      if (status) status.innerHTML = '<span class="badge" style="background:var(--red)">' +
        "Not saved</span>";
    }
  },

  _counts() {
    const items = this._detail.catalogue || [];
    let inUse = 0; let mandatory = 0;
    items.forEach((it) => {
      const s = this._setting(it.item_id);
      if (s.in_use) inUse += 1;
      if (s.mandatory) mandatory += 1;
    });
    return { total: items.length, inUse: inUse, mandatory: mandatory };
  },

  _draw() {
    const c = this._counts();
    this._box.innerHTML =
      PolicyEditor.header("mrp", this._divisions, this._division) +
      '<p class="lead muted" style="font-size:var(--size-sm);max-width:74ch">The review ' +
      "catalogue is what this platform can ask for; this is what <em>you</em> ask for. " +
      "Untick anything your reviews do not need, and mark as mandatory only what a review " +
      "cannot be completed without. Edits save as a draft and are proposed to the " +
      "division's MRC — ML Applications keep being reviewed against the last approved " +
      "policy until the committee signs it off.</p>" +
      '<p class="muted" style="font-size:var(--size-xs)"><strong>' + c.inUse + "</strong> of " +
      c.total + " in use · <strong>" + c.mandatory + "</strong> mandatory</p>" +
      '<div id="mrp-groups"></div>';
    this._drawStatus();
    this._drawGroups();
    PolicyEditor.bindDivision("mrp", (d) => { this._division = d; this._load(); });
  },

  _drawStatus() {
    PolicyEditor.status("mrp", this._detail.state,
      "Nothing ratified — everything is asked for, nothing is required. Edits start a " +
      "draft.");
  },

  _drawGroups() {
    const box = document.getElementById("mrp-groups");
    const groups = this._detail.groups || {};
    const items = this._detail.catalogue || [];
    const order = Object.keys(groups);
    const html = order.map((key) => {
      const mine = items.filter((it) => it.group === key);
      if (!mine.length) return "";
      const on = mine.filter((it) => this._setting(it.item_id).in_use).length;
      const req = mine.filter((it) => this._setting(it.item_id).mandatory).length;
      return '<section class="card" style="margin-bottom:var(--space-4)">' +
        '<h4 style="margin:0 0 var(--space-2)">' + esc(key) + ". " + esc(groups[key]) +
        '<span class="muted" style="font-weight:400;font-size:var(--size-xs);' +
        'margin-left:var(--space-3)">' + on + " of " + mine.length + " in use · " +
        req + " mandatory</span></h4>" +
        '<table class="grid"><thead><tr><th style="width:55%">Item</th>' +
        '<th style="width:12%">In use</th><th style="width:14%">Mandatory</th>' +
        "</tr></thead><tbody>" +
        mine.map((it) => this._row(it)).join("") + "</tbody></table></section>";
    }).join("");
    box.innerHTML = html || '<div class="empty">Nothing to configure.</div>';
    box.querySelectorAll("input[data-mrp-item]").forEach((el) => {
      el.onchange = () => this._set(el.getAttribute("data-mrp-item"),
        el.getAttribute("data-mrp-flag"), el.checked);
    });
  },

  _row(item) {
    const s = this._setting(item.item_id);
    const tick = (flag, on) => '<td style="text-align:center"><input type="checkbox"' +
      (on ? " checked" : "") + ' data-mrp-item="' + esc(item.item_id) +
      '" data-mrp-flag="' + flag + '"></td>';
    // The mandatory items carry the same red left rule the record screens use, so the
    // admin sees here exactly what a reviewer will see there.
    return '<tr' + (s.mandatory ? ' class="mandatory"' : "") + "><td>" +
      "<strong>" + esc(item.label) + "</strong>" +
      (item.note ? '<div class="muted" style="font-size:var(--size-xs)">' +
        esc(item.note) + "</div>" : "") +
      "</td>" + tick("in_use", s.in_use) + tick("mandatory", s.mandatory) + "</tr>";
  },
};
