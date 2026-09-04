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

// The Danger tab: asking the MRC to hibernate a record, or to bring one back.
//
// Retiring is hibernation and it is the committee's decision, not the owner's. The
// screen therefore has three states rather than one button -- ask, wait for the
// committee, ask to come back -- and every record type that can be retired has all
// three.
//
// Written once here because the alternative was demonstrated: the model screen had
// this flow, and the AI System and ML Application screens each grew their own Danger
// tab with a plain Retire button posting straight to a retire endpoint. Two screens,
// two ways past the committee that is the point of the record. What differs between
// them is the noun and the API root; nothing else, so nothing else is a parameter.
const DangerZone = {
  // The retire/reactivate request already queued with the MRC, if any. While one is
  // outstanding the record must not be able to raise another.
  pending(d) {
    const open = (d.signoff_requests || []).filter(
      (r) => (r.kind === "retire" || r.kind === "reactivate") &&
        (r.status === "Pending" || r.status === "Attached"));
    return open.length ? open[open.length - 1] : null;
  },

  _card(body) {
    return '<div class="danger-zone"><div class="dz-header">Danger Zone</div>' +
      '<div class="dz-row">' + body + "</div></div>";
  },

  // ``noun`` is how the record type reads in a sentence -- "model", "AI System",
  // "ML Application". ``record`` is the fetched record ({data, retired, ...}).
  content(noun, record) {
    const d = record.data || {};
    const pending = this.pending(d);
    if (pending) {
      const where = pending.meeting_id
        ? " at " + esc(pending.meeting_id)
        : ", awaiting that committee's next meeting";
      return this._card(
        '<div class="dz-text"><b>' +
        (pending.kind === "retire" ? "Retirement" : "Reactivation") +
        " awaiting MRC ratification</b>" +
        '<p class="muted">Queued with ' + esc(pending.target_mrc || "the MRC") + where +
        ". Nothing changes until the committee approves it.</p></div>");
    }
    if (record.retired) {
      return this._card(
        '<div class="dz-text"><b>Reactivate this ' + esc(noun) + "</b>" +
        '<p class="muted">This ' + esc(noun) + " is hibernated: it is out of the active " +
        "estate and read-only. Bringing it back is the committee's decision, so this " +
        "asks the MRC to ratify it.</p></div>" +
        '<div class="dz-action"><button class="btn small" id="d-reactivate">' +
        "Request reactivate&hellip;</button></div>");
    }
    return this._card(
      '<div class="dz-text"><b>Retire this ' + esc(noun) + "</b>" +
      '<p class="muted">Retiring hibernates the ' + esc(noun) + ": it drops out of the " +
      "active estate and becomes read-only, though its data and audit trail are kept " +
      "and it can be brought back later. The MRC must ratify it, so the " + esc(noun) +
      " stays active until the committee approves.</p></div>" +
      '<div class="dz-action"><button class="btn danger small" id="d-retire">' +
      "Request retire&hellip;</button></div>");
  },

  // Both buttons raise a request for the MRC rather than changing the record:
  // whichever is on screen depends on where the record currently sits.
  //
  // ``opts`` is {api, id, onDone} -- ``api`` the record type's API root, e.g.
  // "/api/ai-systems". No noun: the summary names the record by its id, and the
  // server's own refusals name the type.
  bind(opts) {
    const ask = function (id, path, summary) {
      const button = document.getElementById(id);
      if (button) button.onclick = function () {
        App.amend(summary, "POST",
          opts.api + "/" + encodeURIComponent(opts.id) + path, {}, opts.onDone);
      };
    };
    ask("d-retire", "/request-retire",
      "Ask the MRC to ratify retiring " + opts.id +
      ". It stays active until the committee approves.");
    ask("d-reactivate", "/request-reactivate",
      "Ask the MRC to ratify reactivating " + opts.id +
      ". It stays hibernated until the committee approves.");
  },
};
