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

// The register, led by its functional groups rather than by one long list of records.
//
// A reader opens the Models screen and meets a handful of groups -- what the estate is
// FOR -- and opens the one they came for. The rows inside a group are the same rows the
// flat table draws, so nothing about a record reads differently for being grouped.
//
// Mixed onto InventoryList (as list_filters.js is), so Models, ML Applications and AI
// Systems all get it from setting one config key.

// Where records nobody has filed yet collect. Sorted last, because it is the bucket to
// empty rather than a group anybody chose.
// The one filter that is a free-text search rather than a chosen value. Named here
// because "which of these flattens the view" is a decision about the reader, not a
// detail of the filter bar.
const SEARCH_FILTER_KEY = "q";

const UNGROUPED_KEY = "ungrouped";

Object.assign(InventoryList, {
  // Which groups the reader has opened. Survives a re-render (sorting, a tile toggle)
  // and not a reload -- there is no precedent for persisting UI state here, and a reader
  // returning to the screen wants it as it opens rather than as they left it.
  _openGroups: null,

  // Only a typed SEARCH flattens, and only because somebody who has typed a name wants
  // the rows that match rather than three collapsed groups to open in turn.
  //
  // A dropdown filter does NOT flatten. "The models in Development" is still a question
  // about the estate's structure, and how that subset falls across the functional groups
  // is most of what the reader is asking; answering it with an ungrouped list throws
  // away the grouping at the moment it becomes most useful. This used to flatten on any
  // filter at all, so picking a lifecycle stage or an owner lost the grouping.
  //
  // Sorting does not flatten either -- it sorts WITHIN each group. Sorting is how a
  // reader browses structure, and throwing the structure away at the first header click
  // would make the grouped view something you leave by accident and cannot get back to.
  _grouped() {
    if (!this._cfg.groupBy) return false;
    return !String((this._filters || {})[SEARCH_FILTER_KEY] || "").trim();
  },

  // A group's identity is its division AND its id, never the id alone: ids are minted
  // per division, so PhysicalRisk's FG-001 and Analytics' FG-001 are different groups
  // that would otherwise be drawn as one. Encoded as JSON so no separator can collide
  // with a division name.
  _groupKey(m) {
    const id = String(m.d[this._cfg.groupBy] || "").trim();
    return id ? JSON.stringify([m.d.division || "", id]) : UNGROUPED_KEY;
  },

  // The groups present in ``rows``, in the order each division's committee ratified
  // them, with Ungrouped last. Built from the RECORDS rather than from the policy, so a
  // group nobody has filed anything under does not sit on the screen as an empty row.
  _groupsOf(rows) {
    const byKey = {};
    rows.forEach((m) => {
      const key = this._groupKey(m);
      if (!byKey[key]) byKey[key] = { key: key, division: m.d.division || "", members: [] };
      byKey[key].members.push(m);
    });
    const keys = Object.keys(byKey);
    const spans = new Set(keys.map((k) => byKey[k].division)).size > 1;
    const groups = keys.map((key) => {
      const g = byKey[key];
      const id = key === UNGROUPED_KEY ? "" : JSON.parse(key)[1];
      // Position in the division's ratified list. An id the division no longer defines
      // sorts after the groups still on the list and before Ungrouped, because it is a
      // record needing attention rather than one nobody has got to.
      const ratified = Groups.forDivision(g.division);
      const at = id ? ratified.findIndex((x) => x.id === id) : -1;
      g.id = id;
      g.label = id ? Groups.nameFor(id, g.division) : "Ungrouped";
      // Two divisions may both call a group "Pricing" and mean different things, so the
      // division is named whenever more than one is on screen.
      g.qualifier = spans && id ? g.division : "";
      g.rank = !id ? Number.MAX_SAFE_INTEGER
        : (at < 0 ? Number.MAX_SAFE_INTEGER - 1 : at);
      return g;
    });
    groups.sort((a, b) => (a.rank - b.rank) || a.label.localeCompare(b.label));
    return groups;
  },

  // What a collapsed group has to say for itself: how much is in it, how much of that
  // is overdue, and the worst rating inside. A count alone would make the reader open
  // every group to find the one that needs them, which is the long list again.
  _groupSummary(group) {
    const noun = this._cfg.noun;
    const overdue = group.members.filter(
      (m) => reviewStatus(m.d.next_review_date) === "Overdue").length;
    const worst = group.members.slice().sort((a, b) =>
      ragOrder(a.d.rag_rating, a.d.division) - ragOrder(b.d.rag_rating, b.d.division))[0];
    const parts = [group.members.length + " " +
      (group.members.length === 1 ? noun.replace(/s$/, "") : noun)];
    if (overdue) parts.push(overdue + " overdue");
    return {
      text: parts.join(" \u00b7 "),
      worst: worst && worst.d.rag_rating
        ? ragBadge(worst.d.rag_rating, worst.d.division) : "",
    };
  },

  _renderGrouped(rows, head) {
    const box = document.getElementById(this._cfg.tableId);
    const groups = this._groupsOf(rows);
    // Every record unfiled is not a grouped screen -- it is the flat list with an
    // explanation. Which explanation depends on whether there is anything to file under
    // yet, because "nobody has filed these" and "this division's committee has not
    // agreed any groups" are different problems with different next steps.
    if (groups.length === 1 && groups[0].key === UNGROUPED_KEY) {
      const anyRatified = Array.from(new Set(rows.map((m) => m.d.division || "")))
        .some((d) => Groups.forDivision(d).length);
      box.innerHTML = '<div class="empty" style="text-align:left">' +
        (anyRatified
          ? "No " + esc(this._cfg.noun) + " have been filed under a functional group yet."
          : "No functional groups have been agreed for this scope yet - an administrator " +
            "proposes them under Admin &rarr; Functional Groups and the division's MRC " +
            "signs them off.") + "</div>" + this._tableMarkup(rows, head);
      this._wireTable();
      return;
    }
    const body = groups.map((g) => this._groupRow(g) +
      (this._openGroups[g.key] ? g.members.map((m) => this._memberRow(m)).join("") : ""))
      .join("");
    box.innerHTML = "<table><thead><tr>" + head + "</tr></thead><tbody>" + body +
      "</tbody></table>";
    this._wireTable();
    this._wireGroups();
  },

  _groupRow(group) {
    const open = !!this._openGroups[group.key];
    const s = this._groupSummary(group);
    return '<tr class="grouprow"><td colspan="' + this._columns.length + '">' +
      '<span class="edit-btn" data-group-toggle="' + esc(group.key) + '">' +
      (open ? "Hide" : "Show") + "</span> " +
      "<b>" + esc(group.label) + "</b>" +
      (group.qualifier ? ' <span class="muted">' + esc(group.qualifier) + "</span>" : "") +
      ' <span class="muted">' + esc(s.text) + "</span>" +
      (s.worst ? ' <span style="margin-left:var(--space-4)">' + s.worst + "</span>" : "") +
      "</td></tr>";
  },

  _memberRow(m) {
    return '<tr class="clickable groupmember" data-id="' + esc(m.id) + '">' +
      this._columns.map((c) => "<td>" + c.cell(m) + "</td>").join("") + "</tr>";
  },

  _wireGroups() {
    const self = this;
    document.querySelectorAll("#" + this._cfg.tableId + " [data-group-toggle]")
      .forEach(function (el) {
        el.onclick = function () {
          const key = el.getAttribute("data-group-toggle");
          self._openGroups[key] = !self._openGroups[key];
          self._renderTable();
        };
      });
  },
});
