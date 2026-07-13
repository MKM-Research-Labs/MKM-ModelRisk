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

// MeetingDetail — minutes. Bespoke single-add form (title, presenter from the
// participants, a related model/product picker, and an expandable text box),
// plus the minute list, card and inline edit.
Object.assign(MeetingDetail, {
  // A minute may reference the model or product it concerns: in-scope models and
  // all products, grouped, with values tagged m:<id> / p:<id>.
  _relatedOptions(selected) {
    const nameById = {};
    this._inventory.forEach((m) => { nameById[m.model_id] = (m.data || {}).name; });
    const opt = (v, label) =>
      '<option value="' + esc(v) + '"' + (v === selected ? " selected" : "") + ">" + esc(label) + "</option>";
    let html = '<option value=""></option>';
    const modelIds = this._models.map((r) => r.model_id);
    if (modelIds.length) {
      html += '<optgroup label="Models">' + modelIds.map((id) =>
        opt("m:" + id, id + (nameById[id] ? " — " + nameById[id] : ""))).join("") + "</optgroup>";
    }
    const products = this._products || [];
    if (products.length) {
      html += '<optgroup label="Products">' + products.map((p) =>
        opt("p:" + p.product_id, p.product_id +
          ((p.data || {}).product ? " — " + p.data.product : ""))).join("") + "</optgroup>";
    }
    return html;
  },

  // The add/edit form: Title, Presenter (participants), Related model/product,
  // and an expandable Minutes text box.
  _minuteForm(prefix, item) {
    item = item || {};
    const names = this._participantNames(this._meeting.data || {});
    const presenterOpts = ['<option value=""></option>'].concat(names.map((n) =>
      "<option" + (n === item.presenter ? " selected" : "") + ">" + esc(n) + "</option>")).join("");
    const related = item.model_id ? "m:" + item.model_id : (item.product_id ? "p:" + item.product_id : "");
    return '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
      '<div class="field"><label>Title *</label><input id="' + prefix + '-title" value="' +
      esc(item.title || "") + '"></div>' +
      '<div class="field"><label>Presenter</label><select id="' + prefix + '-presenter">' +
      presenterOpts + "</select></div>" +
      '<div class="field"><label>Related model / product</label><select id="' + prefix + '-related">' +
      this._relatedOptions(related) + "</select></div></div>" +
      '<div class="field" style="margin-top:8px"><label>Minutes</label>' +
      '<textarea id="' + prefix + '-text" rows="5" style="width:100%;box-sizing:border-box">' +
      esc(item.text || "") + "</textarea></div>";
  },

  // Minutes read as a walk-through of the agenda: one section per agenda item (in
  // order), its filed minutes underneath, then a General section for anything
  // unfiled. The add form picks which agenda item a new minute belongs to.
  _minutesContent() {
    const minutes = (this._meeting.data || {}).minutes || [];
    const agenda = this._orderedAgenda();
    const byAgenda = {};
    minutes.forEach((m) => {
      const k = m.agenda_item_id || "";
      (byAgenda[k] = byAgenda[k] || []).push(m);
    });
    let num = 0;
    const self = this;
    const section = (heading, list) =>
      '<div class="section-header" style="margin-top:14px">' + heading + "</div>" +
      (list.length ? list.map((it) => self._minuteCard(it, num++)).join("")
        : '<div class="muted" style="font-size:12px;margin:4px 0 10px">— no minutes recorded —</div>');
    let html = '<div id="minutes-list">';
    agenda.forEach((a) => { html += section(esc(a.title || ""), byAgenda[a.item_id] || []); delete byAgenda[a.item_id]; });
    const general = Object.keys(byAgenda).reduce((acc, k) => acc.concat(byAgenda[k]), []);
    if (general.length) html += section("General notes", general);
    html += "</div>";
    const agendaOpts = ['<option value="">— General —</option>'].concat(agenda.map((a) =>
      '<option value="' + esc(a.item_id) + '">' + esc(a.title || a.item_id) + "</option>")).join("");
    return html +
      '<div class="section-header" style="margin-top:16px">Add minute</div>' +
      '<div class="field"><label>Agenda item</label><select id="madd-agenda">' + agendaOpts + "</select></div>" +
      this._minuteForm("madd", null) +
      '<div class="row" style="margin-top:8px"><button class="btn small primary" id="madd-btn">Add&hellip;</button></div>';
  },

  _minuteCard(item, idx) {
    const related = item.model_id || item.product_id;
    const meta = [];
    if (item.presenter) meta.push("Presenter: <b>" + esc(item.presenter) + "</b>");
    meta.push("Related: " + (related ? this._subjectLabelHtml(related) : '<span class="muted">—</span>'));
    // A sign-off approval minute is the record of a granted decision — it can be
    // edited but not removed; the sign-off is revoked on the model, not by
    // deleting its minute.
    const signoff = (item.title || "").indexOf("Sign-off approved") === 0;
    const remove = signoff ? "" :
      ' <button class="btn small danger" data-minrm="' + esc(item.item_id) + '">Remove</button>';
    return '<div class="card" style="margin-bottom:8px" id="minrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b></div>" +
      '<div class="rowact"><button class="btn small" data-mined="' + esc(item.item_id) + '">Edit</button>' +
      remove + "</div></div>" +
      '<div class="muted" style="margin-top:6px">' + meta.join(" &nbsp;·&nbsp; ") + "</div>" +
      (item.text ? '<div style="margin-top:6px;white-space:pre-wrap">' + esc(item.text) + "</div>" : "") +
      "</div>";
  },

  // Split the tagged related-item value back into its model_id / product_id.
  _relatedFields(value) {
    return {
      model_id: value && value.slice(0, 2) === "m:" ? value.slice(2) : "",
      product_id: value && value.slice(0, 2) === "p:" ? value.slice(2) : "",
    };
  },

  _minuteEdit(item) {
    const card = document.getElementById("minrow-" + item.item_id);
    card.innerHTML = this._minuteForm("med", item) +
      '<div class="row" style="margin-top:8px">' +
      '<button class="btn small primary" id="med-save">Save&hellip;</button> ' +
      '<button class="btn small" id="med-cancel">Cancel</button></div>';
    document.getElementById("med-cancel").onclick = () => this.show(this._id, "minutes");
    document.getElementById("med-save").onclick = () => {
      const fields = { title: val("med-title") || item.title, presenter: val("med-presenter"),
        text: val("med-text") };
      Object.assign(fields, this._relatedFields(val("med-related")));
      App.amend("Update minute " + item.item_id + ".", "POST",
        "/api/meetings/" + this._id + "/collections/minutes/" + item.item_id, { fields: fields },
        () => this.show(this._id, "minutes"));
    };
  },

  _bindMinutes() {
    const self = this;
    document.getElementById("madd-btn").onclick = function () {
      const fields = {};
      const t = val("madd-title"); if (t) fields.title = t;
      const p = val("madd-presenter"); if (p) fields.presenter = p;
      const x = val("madd-text"); if (x) fields.text = x;
      const rel = self._relatedFields(val("madd-related"));
      if (rel.model_id) fields.model_id = rel.model_id;
      if (rel.product_id) fields.product_id = rel.product_id;
      const ag = val("madd-agenda"); if (ag) fields.agenda_item_id = ag;
      if (!fields.title) { App.toast("Title is required", "error"); return; }
      App.amend("Add a minute.", "POST",
        "/api/meetings/" + self._id + "/collections/minutes", { fields: fields },
        () => self.show(self._id, "minutes"));
    };
    const items = (self._meeting.data || {}).minutes || [];
    document.querySelectorAll("[data-mined]").forEach(function (btn) {
      const item = items.find((m) => m.item_id === btn.getAttribute("data-mined"));
      btn.onclick = () => self._minuteEdit(item);
    });
    document.querySelectorAll("[data-minrm]").forEach(function (btn) {
      const id = btn.getAttribute("data-minrm");
      btn.onclick = () => App.amend("Remove minute " + id + ".", "POST",
        "/api/meetings/" + self._id + "/collections/minutes/" + id + "/delete", {},
        () => self.show(self._id, "minutes"));
    });
  },
});
