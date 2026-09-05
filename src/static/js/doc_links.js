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
// Documents, and what is still outstanding.
//
// Every uploaded document is stored, but the console lists each one once and only
// where a reader can do something with it. Defaults mirror config/files.py;
// configure() makes the server's configuration authoritative once specs load.
//
// The counts sit here beside DocLinks because they answer the same kind of question a
// tab badge asks: how much is left to do, not how many were ever raised. A closed
// remediation step or action stops counting — the tab still lists every one, because
// closing something is history, not deletion.
//
// Loads after helpers.js.

// Every uploaded document is stored, but the console lists each one once and only
// where a reader can do something with it. Defaults mirror config/files.py;
// configure() makes the server's configuration authoritative once specs load.
const DocLinks = {
  _hidden: ["tex"],
  _inline: ["pdf", "png", "jpg", "jpeg", "txt"],

  configure(specs) {
    if (!specs) return;
    if (specs.hidden_doc_extensions) this._hidden = specs.hidden_doc_extensions;
    if (specs.inline_view_extensions) this._inline = specs.inline_view_extensions;
  },

  _ext(name) {
    const parts = String(name || "").split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  },

  // The documents of one category that the console shows. A hidden extension (the
  // LaTeX source filed beside its PDF) stays stored and can still be replaced by
  // re-uploading it — it is simply not listed as a second row saying the same thing.
  visible(docs, category) {
    const self = this;
    return (docs || []).filter((d) =>
      d.category === category && self._hidden.indexOf(self._ext(d.original_name)) < 0);
  },

  // How many documents a panel actually lists, for its tab badge — counting the
  // stored total instead would promise rows the tab does not show.
  countIn(docs, categories) {
    const self = this;
    return (categories || []).reduce((total, c) => total + self.visible(docs, c).length, 0);
  },

  // "View" opens the document in a new tab, for the formats a browser renders;
  // anything else is download-only.
  actions(base, id, doc) {
    const url = base + esc(id) + "/documents/" + esc(doc.item_id) + "/download";
    const view = this._inline.indexOf(this._ext(doc.original_name)) < 0 ? "" :
      '<a href="' + url + '?inline=1" target="_blank" rel="noopener">View</a> ';
    return view + '<a href="' + url + '">Download</a>';
  },
};

// Mirrors config CLOSED_REMEDIATION_STATUS.
const CLOSED_REMEDIATION_STATUS = "Closed";

// How many remediation steps are still outstanding. The tab badge answers "how much
// is left to do?", not "how many were ever raised", so a closed step stops counting.
// The tab itself still lists every step — closing one is history, not deletion.
function openRemediationCount(steps) {
  return (steps || []).filter((s) => s.status !== CLOSED_REMEDIATION_STATUS).length;
}

// Mirrors config CLOSED_ACTION_STATUS and REQUESTED_CLOSURE_ACTION_STATUS.
const CLOSED_ACTION_STATUS = "Closed";
const REQUESTED_CLOSURE_ACTION_STATUS = "Closure requested";

// The MRC actions still owed on a model. An action closed at a later meeting stops
// counting as outstanding, but stays on the meeting that agreed it — the committee's
// record is the meeting, and this view only answers "what is still owed?".
// A requested closure is still outstanding: the owner has asked, and until the
// committee ratifies it the obligation stands.
function outstandingActions(actions) {
  return (actions || []).filter((a) => a.status !== CLOSED_ACTION_STATUS);
}

// Those an owner has asked the committee to close. Listed beside the outstanding ones
// at the meeting, because ratifying them is the decision the committee actually takes.
function closureRequestedActions(actions) {
  return (actions || []).filter((a) => a.status === REQUESTED_CLOSURE_ACTION_STATUS);
}
