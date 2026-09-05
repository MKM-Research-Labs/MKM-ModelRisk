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
// A Product's position with its committee.
//
// Which MRC covers it, what that committee has decided, and the link through to the
// meeting where it was decided. Split from detail_core.js so the record and its
// governance position are read separately.
//
// Assigns onto ProductDetail; loads after detail_core.js.

Object.assign(ProductDetail, {

  // The MRC responsible for this product, derived from its Division/Line of Business
  // (Line of Business-level → Division-level → Company). Flags red when none covers it.
  _mrcRow(d) {
    const m = this._mrc || {};
    const head = '<div class="section-header">MRC</div>';
    if (m.mrc) {
      const c = m.mrc;
      return head + '<div class="inforow"><div class="k">Committee</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:var(--size-xs)">' + esc(m.level || "") + "-level</div></div>";
    }
    const org = [d.division, d.line_of_business].filter(Boolean).join(" / ") || "no division / line of business set";
    return head + '<div class="inforow"><div class="v" style="color:var(--red)">&#9888; ' +
      "No committee covers this product (" + esc(org) + "). Set its Division/Line of Business, " +
      "or configure an MRC under Admin &rarr; MRC.</div></div>";
  },

  // MRC status: a one-line summary of the product's MRC linkage — its latest
  // sign-off decision (or a pending request), linking through to the full record.
  _mrcStatusRow(d) {
    const hist = d.signoff_history || [];
    const latest = hist.length ? hist[hist.length - 1] : null;
    const pending = (this._risk || {}).pending_signoff;
    let value;
    if (latest) {
      const outcome = latest.outcome || "Approved";
      const color = outcome === "Rejected" ? "var(--red)" : Theme.value("green");
      value = '<span style="color:' + color + ';font-weight:600">' + esc(outcome) + "</span> at " +
        '<span class="code">' + esc(latest.meeting_id) + "</span>" +
        (latest.date ? " (" + esc(latest.date) + ")" : "");
    } else if (pending) {
      value = pending.status === "Attached"
        ? 'Pending — on the agenda of <span class="code">' + esc(pending.meeting_id) + "</span>"
        : "Pending — queued for " + esc(pending.target_mrc || "its MRC");
    } else {
      value = '<span class="muted">No MRC decision yet</span>';
    }
    return '<div class="inforow"><div class="k">MRC status</div><div class="v">' + value +
      '</div><span class="edit-btn" data-open-linkage="1">view</span></div>';
  },

  // The MRC linkage tab: granted sign-offs plus decisions linked from meetings
  // (read-only). Actions are now first-class on the product (the Actions tab).
  _mrcLinkage(d) {
    const signoffs = d.signoff_history || [];
    const soSection = signoffs.length
      ? DetailTabs.signoffHistory(signoffs, d.division)
      : '<div class="section-header">Sign-off history</div>' +
        '<div class="empty">No MRC sign-offs granted yet.</div>';
    return '<p class="muted">The product&rsquo;s MRC record — granted rating sign-offs, plus ' +
      "decisions linked from meetings (read-only, sourced from the meeting log).</p>" +
      soSection +
      '<div class="section-header">Decisions</div>' +
      DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]);
  },

  // Wire the MRC-status "view" link (rendered inside the overview) to the
  // linkage tab — the overview content is injected after the tabbar handlers
  // bind, so this link needs its own binding.
  _bindLinkageLink() {
    const link = document.querySelector('[data-open-linkage]');
    if (link) link.onclick = () => { this._tab = "linkage"; this._render(); };
  },
});
