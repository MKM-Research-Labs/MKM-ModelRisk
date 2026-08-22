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

// Committees — the committee detail: the Model-style card with inline field
// edits, the Membership and Quorum sections, and the Terms of Reference
// upload/download.
Object.assign(Committees, {
  _showDetail(itemId) {
    this._openId = itemId;
    const item = this._items.find((i) => i.item_id === itemId);
    if (!item) return;
    const rows = this._visible().map((f) =>
      '<div class="inforow" id="crow-' + f.key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + fieldDisplay(item[f.key]) +
      '</div><span class="edit-btn" data-ced="' + f.key + '">edit</span></div>').join("");
    const tor = item.tor_filename
      ? '<div class="row" style="align-items:center;margin-top:var(--space-4)">' +
        '<a href="/api/reference/collections/mrc/' + esc(itemId) + '/tor" target="_blank">&darr; ' +
        esc(item.tor_original_name || "Terms of Reference") + "</a>" +
        '<button class="btn small" id="ctor-replace" style="margin-left:auto">Replace&hellip;</button></div>'
      : '<div class="muted" style="margin-top:var(--space-4)">No Terms of Reference uploaded.</div>';
    const archived = this._isArchived(item);
    const archiveBtn = archived
      ? '<button class="btn small" id="carch">Unarchive committee</button>'
      : '<button class="btn small danger" id="carch">Archive committee</button>';
    document.getElementById("committee-detail").innerHTML =
      '<div class="card" style="margin-top:var(--space-7)"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">' + esc(item.name || item.value) + "</h3>" +
      '<span class="muted" style="margin-left:var(--space-4)">' + esc(item.value) + "</span>" +
      (archived ? ' <span class="badge" style="background:var(--muted);margin-left:var(--space-4)">Archived</span>' : "") +
      '<span style="flex:1"></span>' + archiveBtn + "</div>" + rows +
      this._membershipSection(item) +
      this._quorumSection(item) +
      '<div class="section-header" style="margin-top:var(--space-8)">Terms of Reference</div>' + tor +
      '<div class="row" style="margin-top:var(--space-3)"><input type="file" id="ctor-file">' +
      '<button class="btn small primary" id="ctor-upload">Upload ToR</button></div></div>';
    this._bindDetail(item);
  },

  // People eligible for this committee: those whose org unit matches its scope.
  // Line of Business-level → that line of business; Division-level → that division (any
  // line of business); Company-level (or unset) → everyone.
  _scopePeople(item) {
    const people = this._ref.people || [];
    if (item.level === "Line of Business" && item.scope_value) {
      return people.filter((p) => p.line_of_business === item.scope_value);
    }
    if (item.level === "Division" && item.scope_value) {
      return people.filter((p) => p.division === item.scope_value);
    }
    return people;
  },

  _membershipSection(item) {
    const single = (key, label) => {
      const cur = item[key];
      return '<div class="inforow" id="mrow-' + key + '"><div class="k">' + label +
        '</div><div class="v">' + (cur ? esc(cur) : '<span class="muted">—</span>') +
        '</div><span class="edit-btn" data-med="' + key + '">edit</span></div>';
    };
    const multi = (key, label) => {
      const cur = item[key] || [];
      const shown = cur.length ? esc(cur.join(", ")) : '<span class="muted">—</span>';
      return '<div class="inforow" id="mrow-' + key + '"><div class="k">' + label +
        '</div><div class="v">' + shown + '</div><span class="edit-btn" data-med="' + key + '">edit</span></div>';
    };
    const scope = item.level === "Company" || !item.level
      ? "the institution"
      : esc(item.level) + " (" + esc(item.scope_value || "—") + ")";
    return '<div class="section-header" style="margin-top:var(--space-8)">Membership</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">Members are people in ' + scope + ".</p>" +
      single("chair", "Chair") + single("secretary", "Secretary") +
      multi("voting_members", "Voting members") + multi("non_voting_members", "Non-voting members");
  },

  _editMember(item, key) {
    const row = document.getElementById("mrow-" + key);
    const people = this._scopePeople(item);
    const isMulti = key === "voting_members" || key === "non_voting_members";
    let control;
    if (!people.length) {
      control = '<span class="muted">No people in this committee\'s scope yet — add them under People.</span>';
    } else if (isMulti) {
      const cur = item[key] || [];
      control = '<div class="row" style="flex-wrap:wrap;gap:var(--space-5);flex:1">' +
        people.map((p) => '<label style="font-size:var(--size-sm);font-weight:400"><input type="checkbox" class="mem-chk" value="' +
          esc(p.name) + '"' + (cur.indexOf(p.name) >= 0 ? " checked" : "") + "> " + esc(p.name) + "</label>").join("") +
        "</div>";
    } else {
      const cur = item[key] || "";
      control = '<select id="med-input"><option value=""></option>' +
        people.map((p) => "<option" + (p.name === cur ? " selected" : "") + ">" + esc(p.name) + "</option>").join("") +
        "</select>";
    }
    const label = key.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
    row.innerHTML = '<div class="k">' + esc(label) + '</div><div class="editor" style="flex:1">' + control +
      (people.length ? '<button class="btn small primary" id="med-save">Save&hellip;</button>' : "") +
      '<button class="btn small" id="med-cancel">Cancel</button></div>';
    document.getElementById("med-cancel").onclick = () => this._showDetail(item.item_id);
    const save = document.getElementById("med-save");
    if (save) {
      save.onclick = () => {
        const value = isMulti
          ? [...document.querySelectorAll(".mem-chk:checked")].map((c) => c.value)
          : document.getElementById("med-input").value;
        App.amend("Set " + label + " on " + item.value + ".", "POST",
          "/api/reference/collections/mrc/" + item.item_id, { fields: { [key]: value } },
          () => Reference.render());
      };
    }
  },

  _bindDetail(item) {
    const self = this;
    const byKey = {};
    this._spec.fields.forEach((f) => { byKey[f.key] = f; });
    document.querySelectorAll("[data-ced]").forEach((btn) => {
      btn.onclick = () => self._editField(item, byKey[btn.getAttribute("data-ced")]);
    });
    document.querySelectorAll("[data-med]").forEach((btn) => {
      btn.onclick = () => self._editMember(item, btn.getAttribute("data-med"));
    });
    document.getElementById("carch").onclick = () => {
      const archived = self._isArchived(item);
      const verb = archived ? "Unarchive" : "Archive";
      App.amend(verb + " committee " + item.value + ".", "POST",
        "/api/reference/collections/mrc/" + item.item_id,
        { fields: { archived: archived ? "false" : "true" } }, () => Reference.render());
    };
    document.getElementById("ctor-upload").onclick = () => self._uploadTor(item.item_id);
    const replace = document.getElementById("ctor-replace");
    if (replace) replace.onclick = () => document.getElementById("ctor-file").click();
  },

  // The quorum rule: minimum attendance for a meeting of this committee to be
  // quorate. Each row reuses the generic field editor (data-ced) — the fields
  // live on the mrc spec. Unset values fall back to the sensible defaults
  // (Chair + Secretary + 2 voting), which is also what the meeting assumes.
  _quorumSection(item) {
    const row = (key, label, dflt) => {
      const set = item[key] !== undefined && item[key] !== null && item[key] !== "";
      const shown = set ? esc(String(item[key]))
        : esc(String(dflt)) + ' <span class="muted">(default)</span>';
      return '<div class="inforow" id="crow-' + key + '"><div class="k">' + label +
        '</div><div class="v">' + shown +
        '</div><span class="edit-btn" data-ced="' + key + '">edit</span></div>';
    };
    return '<div class="section-header" style="margin-top:var(--space-8)">Quorum</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">Minimum attendance for a meeting to be quorate and ' +
      'proceed. Default: Chair + Secretary + 2 voting members (non-voting members do not count).</p>' +
      row("quorum_require_chair", "Requires chair", "Yes") +
      row("quorum_require_secretary", "Requires secretary", "Yes") +
      row("quorum_min_voting", "Min voting members", "2");
  },

  _editField(item, f) {
    const row = document.getElementById("crow-" + f.key);
    // The scope picker is a Division/Line of Business list matching the committee's
    // current level (and disabled for a Company-level MRC).
    const control = f.key === "scope_value"
      ? this._scopeControl("ced-input", item.level, item.scope_value)
      : inputControl("ced-input", f);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      control + '<button class="btn small primary" id="ced-save">Save&hellip;</button>' +
      '<button class="btn small" id="ced-cancel">Cancel</button></div>';
    const input = document.getElementById("ced-input");
    if (f.key !== "scope_value" && item[f.key] !== null && item[f.key] !== undefined) input.value = item[f.key];
    document.getElementById("ced-cancel").onclick = () => this._showDetail(item.item_id);
    document.getElementById("ced-save").onclick = () => {
      const fields = {};
      fields[f.key] = input.value.trim();
      App.amend("Set " + f.label + ' on ' + item.value + ".", "POST",
        "/api/reference/collections/mrc/" + item.item_id, { fields: fields },
        () => Reference.render());
    };
  },

  _uploadTor(itemId) {
    const fileInput = document.getElementById("ctor-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    fetch("/api/reference/collections/mrc/" + itemId + "/tor", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Terms of Reference uploaded", "ok");
      Reference.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
});
