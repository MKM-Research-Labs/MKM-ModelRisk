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

// The controls an action is described with: which model it concerns, who owns it, and
// where it has got to.
//
// Split from detail_actions.js, which draws the tab and writes to it. These are the
// pickers that both the add form and an open card build from, and they are together
// because they are one chain of reasoning rather than three widgets: the model
// decides which people are offered, the model's own owner is ticked by default, and
// what comes back out is a list of owners rather than a single name — an action
// agreed at a committee is frequently owed by more than one person.
//
// Every vocabulary here is read from the collection spec, never written in: the owner
// roles and the status words are the adopter's, and a status renamed under Admin has
// to display by its new name here like everywhere else.
//
// Assigns onto MeetingDetail; loads after detail_actions.js.

Object.assign(MeetingDetail, {

  _actionField(key) {
    const spec = this.collSpec("actions") || {};
    return (spec.fields || []).find((f) => f.key === key) || {};
  },

  // Owners as a list, tolerating what is already on record: an action minuted before
  // an action could have more than one owner holds a bare string.
  _actionOwners(action) {
    const owner = (action || {}).owner;
    if (!owner) return [];
    return Array.isArray(owner) ? owner : [owner];
  },

  // The registered owner of a model — what the tick-boxes start on once a model is picked.
  _modelOwner(modelId) {
    const model = (this._inventory || []).find((m) => m.model_id === modelId);
    return model ? (model.data || {}).owner || "" : "";
  },

  // Models in scope for this meeting first, then the rest of the inventory. An action
  // usually concerns something the committee is sitting on, but not always.
  _actionModelSelect(id, selected) {
    const inScope = (this._models || []).map((m) => m.model_id).filter(Boolean);
    const self = this;
    const option = function (modelId) {
      const name = self._subjectName(modelId);
      return '<option value="' + esc(modelId) + '"' +
        (modelId === selected ? " selected" : "") + ">" +
        esc(modelId + (name ? " — " + name : "")) + "</option>";
    };
    const others = (this._actionField("model_id").options || [])
      .filter((m) => inScope.indexOf(m) < 0);
    const group = (label, ids) => (ids.length
      ? '<optgroup label="' + esc(label) + '">' + ids.map(option).join("") + "</optgroup>" : "");
    return '<select id="' + id + '"><option value=""></option>' +
      group("In scope for this meeting", inScope) +
      group("Other registered models", others) + "</select>";
  },

  // Tick-boxes rather than a multi-select: the committee should be able to see every
  // candidate owner at once and tick several without a modifier key.
  _ownerBoxes(group, ticked) {
    const people = this._actionField("owner").options || [];
    if (!people.length) {
      return '<span class="muted" style="font-size:var(--size-xs)">No people in the directory — ' +
        "add them under Admin &rarr; People.</span>";
    }
    return people.map((person) =>
      '<label class="tickbox"><input type="checkbox" data-owner="' + esc(group) + '" value="' +
      esc(person) + '"' + (ticked.indexOf(person) >= 0 ? " checked" : "") + ">" +
      esc(person) + "</label>").join("");
  },

  _tickedOwners(group) {
    return Array.from(document.querySelectorAll('[data-owner="' + group + '"]'))
      .filter((box) => box.checked).map((box) => box.value);
  },

  // The status vocabulary and its opening value both come from the field spec, so the
  // screen never decides that an agreed action starts Open (coding rule R1). Closed is
  // withheld: an owner requests closure and the committee grants it, so offering the
  // closed status here would only produce a refusal from the domain.
  _actionStatusSelect(id, selected) {
    const spec = this._actionField("status");
    const chosen = selected || spec.default || "";
    const labels = spec.option_labels || {};
    const options = (spec.options || []).filter((s) => s !== CLOSED_ACTION_STATUS);
    return '<select id="' + esc(id) + '">' + options.map((s) =>
      '<option value="' + esc(s) + '"' + (s === chosen ? " selected" : "") + ">" +
      esc(labels[s] || s) + "</option>").join("") + "</select>";
  },
});
