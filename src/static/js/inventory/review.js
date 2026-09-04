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

// The model's Review tab: the shared review panel, attached to the model's Detail.
//
// The panel is in review_panel.js and is identical for every governed record type. All
// that is here is the handful of accessors where the model's Detail — which predates
// RecordDetail — names things differently: its record is `_model`, not `_record`, and
// its field rows and collection sections are its own.
Object.assign(Detail, ReviewPanelContract, ReviewPanel, {
  // The model's Detail predates RecordDetail and has no _cfg, so the panel's element
  // scoping needs telling where this screen's content lives.
  _rvPfx() { return "dt-"; },
  _rvScope() { return document.getElementById("dt-content") || document; },

  _rvRecord() { return this._model; },
  _rvSet(record) { this._model = record; },
  _rvId() { return this._id; },
  _rvApi() { return "/api/models/"; },
  _rvRow(key) { return this._row(key, this._rvData()); },
  _rvColl(key, d) { return this._collSection(key, d); },
  _rvBindColls(keys) { this._bindCollections(keys); },
  // The inventory list shows each model's review status, so it is stale the moment a
  // stage is agreed.
  _rvAfterApprove() { Inventory.loadList(); },
});
