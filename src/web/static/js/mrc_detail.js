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

// MRC meeting detail: header card + editable meeting fields + collections
// (agenda, decisions, actions, participants, minutes, models in scope).
const MeetingDetail = {
  async show(meetingId) {
    const specs = await MRC.specs();
    const m = await App.get("/api/meetings/" + meetingId);
    const d = m.data || {};
    let fieldRows = "";
    specs.fields.forEach(function (f) { fieldRows += MeetingDetail._row(f, d[f.key]); });
    document.getElementById("mt-detail").innerHTML =
      '<div class="card">' + this._header(m, d) +
      '<div class="section-header">Meeting details</div>' + fieldRows +
      Collections.render(d, specs, false) + "</div>";

    this._bindFields(meetingId, d);
    Collections.bind(
      "/api/meetings/" + meetingId + "/collections/", specs, false,
      () => this.show(meetingId),
    );
    document.getElementById("mt-detail").scrollIntoView({ behavior: "smooth", block: "start" });
  },

  _header(m, d) {
    const sub = esc(m.meeting_id) + (d.date ? " · " + esc(d.date) : "");
    return '<div class="detail-header"><div>' +
      '<div class="name">' + esc(d.title || m.meeting_id) + "</div>" +
      '<div class="sub">' + sub + "</div>" +
      '<div style="margin-top:8px">' + statusBadge(m.status) + "</div></div>" +
      '<div class="right"><div class="olabel">Chair</div>' +
      '<div class="oname">' + fieldDisplay(d.chair) + "</div></div></div>";
  },

  _row(f, value) {
    return '<div class="inforow" id="mrow-' + f.key + '">' +
      '<div class="k">' + esc(f.label) + '</div>' +
      '<div class="v">' + fieldDisplay(value) + "</div>" +
      '<span class="edit-btn" data-medit="' + f.key + '">edit</span></div>';
  },

  _bindFields(meetingId, d) {
    const self = this;
    document.querySelectorAll("[data-medit]").forEach(function (btn) {
      const key = btn.getAttribute("data-medit");
      btn.onclick = function () { self._edit(meetingId, MRC.specFieldByKey(key), d[key]); };
    });
  },

  _edit(meetingId, f, current) {
    const row = document.getElementById("mrow-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div>' +
      '<div class="editor">' + inputControl("med-input", f) +
      '<button class="btn small primary" id="med-save">Save…</button>' +
      '<button class="btn small" id="med-cancel">Cancel</button></div>';
    const input = document.getElementById("med-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("med-cancel").onclick = () => this.show(meetingId);
    document.getElementById("med-save").onclick = () => {
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + meetingId + ".",
        "POST", "/api/meetings/" + meetingId + "/field",
        { field: f.key, value: input.value.trim() },
        () => { this.show(meetingId); MRC.loadList(); });
    };
  },
};
