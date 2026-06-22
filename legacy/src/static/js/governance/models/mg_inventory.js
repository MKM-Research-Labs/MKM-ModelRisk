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

function renderSummaryCards() {
    if (!mgData) return '';
    var d = mgData;
    var assessedCount = (d.models || []).filter(function(m) { return m.risk_rating && m.risk_rating !== 'Not Rated'; }).length;
    var cards = [
        {label: 'Total Models', value: d.total_models, color: '#1976d2'},
        {label: 'Tier 1', value: d.tier_distribution['1'] || 0, color: '#d32f2f'},
        {label: 'Tier 2', value: d.tier_distribution['2'] || 0, color: '#f57c00'},
        {label: 'Tier 3', value: d.tier_distribution['3'] || 0, color: '#1976d2'},
        {label: 'Overdue', value: d.review_status_distribution['Overdue'] || 0, color: (d.review_status_distribution['Overdue'] || 0) > 0 ? '#d32f2f' : '#388e3c'},
        {label: 'Due Soon', value: d.review_status_distribution['Due Soon'] || 0, color: (d.review_status_distribution['Due Soon'] || 0) > 0 ? '#f57c00' : '#388e3c'},
        {label: 'Assessed', value: assessedCount + '/' + d.total_models, color: '#4527a0'},
    ];
    var html = '<div style="display:flex;gap:10px;padding:12px 16px;border-bottom:1px solid #eee;flex-wrap:wrap;">';
    cards.forEach(function(c) {
        html += '<div style="flex:1;min-width:100px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';">' +
            '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
            '<div style="font-size:18px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div></div>';
    });
    html += '</div>';
    return html;
}

// ================================================================
// Column definitions for inventory table
// ================================================================
var mgColumns = [
    {key: 'model_id', label: 'ID', sortable: true},
    {key: 'short_name', label: 'Model', sortable: true},
    {key: 'tier', label: 'Tier', sortable: true, filter: 'select'},
    {key: 'rag_rating', label: 'RAG', sortable: true, filter: 'select'},
    {key: 'owner', label: 'Owner', sortable: true, filter: 'select'},
    {key: 'last_review_date', label: 'Last Review', sortable: true, filter: 'date'},
    {key: 'mrc_signoff_date', label: 'MRC Signoff', sortable: true, filter: 'date'},
    {key: 'next_review_date', label: 'Next Review', sortable: true, filter: 'date'},
    {key: 'review_status', label: 'Status', sortable: true, filter: 'select'},
    {key: 'risk_rating', label: 'Risk', sortable: true, filter: 'select'},
    {key: 'open_remediations', label: 'Actions', sortable: true},
];

function mgGetFilteredSorted() {
    var models = (mgData && mgData.models) ? mgData.models.slice() : [];

    // Apply filters
    Object.keys(mgFilters).forEach(function(key) {
        var val = mgFilters[key];
        if (!val || val === '') return;
        var col = mgColumns.find(function(c) { return c.key === key; });
        if (!col) return;

        if (col.filter === 'date') {
            // val is {from: 'YYYY-MM-DD', to: 'YYYY-MM-DD'}
            if (val.from || val.to) {
                models = models.filter(function(m) {
                    var d = m[key];
                    if (!d) return false;
                    if (val.from && d < val.from) return false;
                    if (val.to && d > val.to) return false;
                    return true;
                });
            }
        } else {
            models = models.filter(function(m) {
                return String(m[key]) === String(val);
            });
        }
    });

    // Apply sort
    if (mgSortCol) {
        var asc = mgSortAsc;
        models.sort(function(a, b) {
            var va = a[mgSortCol], vb = b[mgSortCol];
            if (va == null) va = '';
            if (vb == null) vb = '';
            if (typeof va === 'number' && typeof vb === 'number') return asc ? va - vb : vb - va;
            va = String(va); vb = String(vb);
            return asc ? va.localeCompare(vb) : vb.localeCompare(va);
        });
    }

    return models;
}

function mgToggleSort(key) {
    if (mgSortCol === key) {
        mgSortAsc = !mgSortAsc;
    } else {
        mgSortCol = key;
        mgSortAsc = true;
    }
    renderInventory();
}

function mgSetFilter(key, value) {
    if (value === '' || value === null || value === undefined) {
        delete mgFilters[key];
    } else {
        mgFilters[key] = value;
    }
    renderInventory();
}

function mgSetDateFilter(key, which, value) {
    if (!mgFilters[key] || typeof mgFilters[key] !== 'object') {
        mgFilters[key] = {};
    }
    mgFilters[key][which] = value;
    if (!mgFilters[key].from && !mgFilters[key].to) delete mgFilters[key];
    renderInventory();
}

function mgClearFilters() {
    mgFilters = {};
    mgSortCol = null;
    mgSortAsc = true;
    renderInventory();
}

function mgSortArrow(key) {
    if (mgSortCol !== key) return '<span style="color:#ccc;margin-left:3px;">&#x21C5;</span>';
    return mgSortAsc ? '<span style="color:#1976d2;margin-left:3px;">&#x25B2;</span>' : '<span style="color:#1976d2;margin-left:3px;">&#x25BC;</span>';
}

// ================================================================
// Inventory table
// ================================================================
function renderInventory() {
    if (!mgData) return;
    var content = document.getElementById('mg-content');
    var models = mgGetFilteredSorted();

    var html = renderSummaryCards();

    // Active filter indicator
    var filterCount = Object.keys(mgFilters).length;
    if (filterCount > 0 || mgSortCol) {
        html += '<div style="display:flex;align-items:center;gap:8px;padding:6px 16px;background:#e3f2fd;border-bottom:1px solid #bbdefb;">';
        html += '<span style="font-size:10px;color:#1565c0;">Showing ' + models.length + ' of ' + mgData.models.length + ' models</span>';
        if (filterCount > 0) {
            html += '<span style="font-size:10px;color:#1565c0;font-weight:600;">' + filterCount + ' filter' + (filterCount > 1 ? 's' : '') + ' active</span>';
        }
        if (mgSortCol) {
            var sortLabel = mgColumns.find(function(c) { return c.key === mgSortCol; });
            html += '<span style="font-size:10px;color:#1565c0;">Sorted by ' + (sortLabel ? sortLabel.label : mgSortCol) + (mgSortAsc ? ' &#x25B2;' : ' &#x25BC;') + '</span>';
        }
        html += '<button onclick="window.MG.clearFilters()" style="margin-left:auto;padding:2px 10px;font-size:10px;border:1px solid #90caf9;border-radius:3px;cursor:pointer;background:white;color:#1565c0;">Clear All</button>';
        html += '</div>';
    }

    // Collect distinct values for select filters
    var distinctVals = {};
    mgColumns.forEach(function(col) {
        if (col.filter === 'select') {
            var vals = {};
            mgData.models.forEach(function(m) {
                var v = m[col.key];
                if (v != null && v !== '') vals[String(v)] = true;
            });
            distinctVals[col.key] = Object.keys(vals).sort();
        }
    });

    // Table
    html += '<div style="padding:0;">';
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';

    // Header row with sort controls
    html += '<thead>';
    html += '<tr style="background:#fafafa;">';
    mgColumns.forEach(function(col) {
        var thStyle = 'padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;white-space:nowrap;position:sticky;top:0;background:#fafafa;';
        if (col.sortable) thStyle += 'cursor:pointer;user-select:none;';
        html += '<th style="' + thStyle + '"';
        if (col.sortable) html += ' onclick="window.MG.toggleSort(\'' + col.key + '\')"';
        html += '>' + col.label;
        if (col.sortable) html += mgSortArrow(col.key);
        html += '</th>';
    });
    html += '</tr>';

    // Filter row
    html += '<tr style="background:#f5f5f5;">';
    mgColumns.forEach(function(col) {
        html += '<td style="padding:4px 6px;border-bottom:1px solid #ddd;">';
        if (col.filter === 'select') {
            var curVal = mgFilters[col.key] || '';
            html += '<select onchange="window.MG.setFilter(\'' + col.key + '\', this.value)" style="width:100%;font-size:10px;padding:3px 4px;border:1px solid #ddd;border-radius:3px;background:white;">';
            html += '<option value="">All</option>';
            (distinctVals[col.key] || []).forEach(function(v) {
                html += '<option value="' + v + '"' + (v === String(curVal) ? ' selected' : '') + '>' + v + '</option>';
            });
            html += '</select>';
        } else if (col.filter === 'date') {
            var df = mgFilters[col.key] || {};
            html += '<div style="display:flex;flex-direction:column;gap:2px;">';
            html += '<input type="date" value="' + (df.from || '') + '" onchange="window.MG.setDateFilter(\'' + col.key + '\', \'from\', this.value)" style="font-size:9px;padding:2px;border:1px solid #ddd;border-radius:3px;width:100%;" placeholder="From" title="From date">';
            html += '<input type="date" value="' + (df.to || '') + '" onchange="window.MG.setDateFilter(\'' + col.key + '\', \'to\', this.value)" style="font-size:9px;padding:2px;border:1px solid #ddd;border-radius:3px;width:100%;" placeholder="To" title="To date">';
            html += '</div>';
        } else {
            html += '';
        }
        html += '</td>';
    });
    html += '</tr>';
    html += '</thead><tbody>';

    models.forEach(function(m) {
        var rowBg = '';
        if (m.review_status === 'Overdue') rowBg = 'background:#ffebee;';
        else if (m.review_status === 'Due Soon') rowBg = 'background:#fff3e0;';

        html += '<tr style="cursor:pointer;' + rowBg + '" onmouseenter="this.style.opacity=\'0.8\'" onmouseleave="this.style.opacity=\'1\'" onclick="window.MG.showDetail(\'' + m.model_id + '\')">';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1976d2;white-space:nowrap;">' + m.model_id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (catIcons[m.category] || '') + ' ' + m.short_name + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + tierBadge(m.tier) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + ragBadge(m.rag_rating) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + m.owner + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (m.last_review_date || '—') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (m.mrc_signoff_date || '—') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (m.next_review_date || '—') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + reviewBadge(m.review_status) + '</td>';
        var rrVal = m.risk_rating || 'Not Rated';
        var rrColors = {'Acceptable':'#388e3c','Conditional':'#f57c00','Unacceptable':'#d32f2f','Not Rated':'#9e9e9e'};
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(rrVal, rrColors[rrVal] || '#9e9e9e') + '</td>';
        var remCount = m.open_remediations || 0;
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + (remCount > 0 ? '<span style="background:#fff3e0;color:#e65100;padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;">' + remCount + ' open</span>' : '<span style="color:#388e3c;font-size:10px;">Clear</span>') + '</td>';
        html += '</tr>';
    });

    if (models.length === 0) {
        html += '<tr><td colspan="11" style="padding:20px;text-align:center;color:#888;font-size:12px;">No models match the current filters</td></tr>';
    }

    html += '</tbody></table></div>';
    content.innerHTML = html;

    var statsBar = document.getElementById('mg-stats-bar');
    statsBar.innerHTML =
        '<span>Framework: <b>' + mgData.metadata.framework + '</b></span>' +
        '<span>Handbook: <b>' + mgData.metadata.handbook_reference + '</b></span>' +
        '<span>As of: <b>' + mgData.as_of + '</b></span>';
}

