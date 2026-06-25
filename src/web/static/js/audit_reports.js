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

// Audit Reports tab: lists the generated PDF reports with View/Download, and a
// button to (re)generate them.
const AuditReports = {
  async render() {
    const reports = await App.get("/api/audit-reports");
    const cards = reports.length ? reports.map((r) =>
      '<div class="rcard"><div class="rlabel">' + esc(r.label) + "</div>" +
      '<div class="rmeta">' + esc(r.filename) + " &middot; " + fmtSize(r.size) +
      " &middot; " + esc((r.modified || "").slice(0, 10)) + "</div>" +
      '<div class="row" style="margin-top:10px">' +
      '<a class="btn small primary" href="/api/audit-reports/' + esc(r.filename) +
      '" target="_blank">View</a>' +
      '<a class="btn small" href="/api/audit-reports/' + esc(r.filename) +
      '" download>Download</a></div></div>').join("") :
      '<div class="empty">No reports generated yet. Click “Generate reports”.</div>';
    document.getElementById("tab-reports").innerHTML =
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">Audit reports</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="ar-generate">Generate reports</button></div>' +
      '<p class="muted">Generated PDFs: the coding-rule audit (R1&ndash;R6) and the Model Risk ' +
      "Report. Files are written to output/audit/ (gitignored).</p>" +
      '<div class="rgrid" style="margin-top:12px">' + cards + "</div></div>";
    document.getElementById("ar-generate").onclick = () => this._generate();
  },

  _generate() {
    const btn = document.getElementById("ar-generate");
    btn.disabled = true;
    btn.textContent = "Generating…";
    fetch("/api/audit-reports/generate", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() },
    }).then(async (res) => {
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.error || "generation failed");
      }
      App.toast("Reports generated", "ok");
      this.render();
    }).catch((e) => {
      App.toast(e.message, "error");
      btn.disabled = false;
      btn.textContent = "Generate reports";
    });
  },
};
