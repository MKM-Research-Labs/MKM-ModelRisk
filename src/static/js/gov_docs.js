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

// Governance-wide Documents tab: upload, list, download and delete documents.
const GovDocs = {
  async render() {
    const docs = await App.get("/api/documents");
    const rows = docs.length ? docs.map((d) =>
      "<tr><td>" + esc(d.original_name) + "</td><td>" + fieldDisplay(d.description) + "</td><td>" +
      esc((d.uploaded_at || "").slice(0, 10)) + "</td><td>" + fmtSize(d.size) +
      '</td><td class="rowact"><a href="/api/documents/' + esc(d.item_id) + '/download">Download</a>' +
      ' <button class="btn small danger" data-rmgd="' + esc(d.item_id) + '">Delete</button></td></tr>').join("") :
      '<tr><td colspan="5" class="empty">No documents uploaded yet.</td></tr>';
    document.getElementById("tab-documents").innerHTML =
      '<div class="card"><h3>Documents (' + docs.length + ")</h3>" +
      '<div class="row" style="align-items:center;margin-bottom:10px"><input type="file" id="gd-file">' +
      '<input id="gd-desc" placeholder="Description (optional)" style="flex:1">' +
      '<button class="btn small primary" id="gd-upload">Upload</button></div>' +
      "<table><thead><tr><th>Name</th><th>Description</th><th>Date Added</th><th>Size</th><th>Actions</th></tr></thead><tbody>" +
      rows + "</tbody></table></div>";
    this._bind();
  },

  _bind() {
    const self = this;
    document.getElementById("gd-upload").onclick = function () { self._upload(); };
    document.querySelectorAll("[data-rmgd]").forEach(function (el) {
      const iid = el.getAttribute("data-rmgd");
      el.onclick = function () {
        App.amend("Delete document " + iid + "?", "POST", "/api/documents/" + iid + "/delete",
          {}, () => self.render());
      };
    });
  },

  _upload() {
    const fileInput = document.getElementById("gd-file");
    if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    form.append("description", document.getElementById("gd-desc").value);
    fetch("/api/documents", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json(); throw new Error(e.error || "upload failed"); }
      App.toast("Document uploaded", "ok");
      this.render();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
