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

// ================================================================
// Data Lineage tab
// ================================================================
function renderDataLineage() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading data lineage...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/data-lineage', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + (data.message || 'Unknown') + '</div>';
                return;
            }
            window._lineageData = data;
            _drawLineagePanel(data);
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load data lineage.</div>';
            console.error('[Governance] Lineage load error:', err);
        });
}

function _lineageStatusBadge(status) {
    var colors = {fresh: '#4caf50', stale: '#ff9800', missing: '#f44336'};
    var labels = {fresh: 'Fresh', stale: 'Stale', missing: 'Missing'};
    var bg = colors[status] || '#999';
    var label = labels[status] || status;
    return '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:9px;font-weight:700;color:white;background:' + bg + ';">' + label + '</span>';
}

function _lineageHealthBadge(health) {
    var colors = {healthy: '#4caf50', degraded: '#ff9800', unhealthy: '#f44336'};
    var bg = colors[health] || '#999';
    return '<span style="display:inline-block;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;color:white;background:' + bg + ';text-transform:uppercase;">' + health + '</span>';
}

function _drawLineagePanel(data) {
    var content = document.getElementById('mg-content');
    var steps = data.pipeline_steps || [];
    var summary = data.summary || {};
    var html = '<div style="padding:16px;">';

    // Header with health badge
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">';
    html += '<div>';
    html += '<div style="font-size:13px;font-weight:700;color:#333;">Data Pipeline Lineage</div>';
    html += '<div style="font-size:11px;color:#666;margin-top:2px;">Pipeline health and data provenance tracking</div>';
    html += '</div>';
    html += '<div style="text-align:right;">';
    html += _lineageHealthBadge(summary.health || 'unknown');
    html += '<div style="font-size:10px;color:#888;margin-top:4px;">' + (summary.fresh || 0) + '/' + (summary.total || 0) + ' steps fresh</div>';
    html += '</div></div>';

    // Pipeline DAG
    html += '<div style="font-size:11px;font-weight:600;color:#555;margin-bottom:8px;">Pipeline DAG</div>';
    html += '<div style="display:flex;align-items:center;gap:0;padding:12px 0;overflow-x:auto;flex-wrap:wrap;justify-content:center;">';
    steps.forEach(function(s, idx) {
        var borderColor = s.status === 'fresh' ? '#4caf50' : s.status === 'stale' ? '#ff9800' : '#f44336';
        var bgColor = s.status === 'fresh' ? '#e8f5e9' : s.status === 'stale' ? '#fff3e0' : '#ffebee';
        html += '<div style="text-align:center;min-width:90px;padding:10px 8px;border:2px solid ' + borderColor + ';border-radius:8px;background:' + bgColor + ';margin:4px 0;">';
        html += '<div style="font-size:10px;font-weight:700;color:#333;">' + s.step + '</div>';
        if (s.last_run) {
            var d = s.last_run.substring(0, 16).replace('T', ' ');
            html += '<div style="font-size:8px;color:#666;margin-top:4px;">' + d + '</div>';
        } else {
            html += '<div style="font-size:8px;color:#f44336;margin-top:4px;font-weight:600;">Not run</div>';
        }
        html += '<div style="margin-top:4px;">' + _lineageStatusBadge(s.status) + '</div>';
        html += '</div>';
        if (idx < steps.length - 1) {
            html += '<div style="font-size:16px;color:#999;padding:0 4px;">\u2192</div>';
        }
    });
    html += '</div>';

    // Staleness table
    html += '<div style="font-size:11px;font-weight:600;color:#555;margin:20px 0 8px;">Staleness Detail</div>';
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Step', 'Generator', 'Last Run', 'Status', 'Issues'].forEach(function(h) {
        html += '<th style="padding:6px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';
    steps.forEach(function(s) {
        html += '<tr>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#333;">' + s.step + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-family:monospace;font-size:10px;color:#666;">' + s.generator + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">';
        if (s.last_run) {
            html += s.last_run.substring(0, 19).replace('T', ' ');
        } else {
            html += '<span style="color:#f44336;">\u2014</span>';
        }
        html += '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">' + _lineageStatusBadge(s.status) + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#888;">' + (s.issues.length > 0 ? s.issues.join('; ') : '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';

    // Trace search
    html += '<div style="font-size:11px;font-weight:600;color:#555;margin:24px 0 8px;">Provenance Trace</div>';
    html += '<div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;">';
    html += '<select id="lineage-trace-type" onchange="window._lineagePopulateIds()" style="padding:5px 8px;font-size:11px;border:1px solid #ddd;border-radius:4px;">';
    html += '<option value="gauge">Gauge</option>';
    html += '<option value="property">Property</option>';
    html += '<option value="trade">Trade (PRS)</option>';
    html += '<option value="counterparty">Counterparty</option>';
    html += '</select>';
    html += '<select id="lineage-trace-id" style="flex:1;padding:5px 8px;font-size:11px;border:1px solid #ddd;border-radius:4px;">';
    html += '<option value="">Loading...</option>';
    html += '</select>';
    html += '<button onclick="window._lineageTrace()" style="padding:5px 14px;font-size:11px;font-weight:600;border:1px solid #1976d2;border-radius:4px;background:#1976d2;color:white;cursor:pointer;">Trace</button>';
    html += '</div>';
    html += '<div id="lineage-trace-result"></div>';

    // Populate the ID dropdown on first render
    setTimeout(function() { window._lineagePopulateIds(); }, 100);

    html += '</div>';
    content.innerHTML = html;
}

// Cache for entity ID lists (avoid re-fetching on each type switch)
var _lineageIdCache = {};

window._lineagePopulateIds = function() {
    var typeSelect = document.getElementById('lineage-trace-type');
    var idSelect = document.getElementById('lineage-trace-id');
    if (!typeSelect || !idSelect) return;
    var dataType = typeSelect.value;

    // Return cached if available
    if (_lineageIdCache[dataType]) {
        _lineageRenderIdOptions(idSelect, _lineageIdCache[dataType]);
        return;
    }

    idSelect.innerHTML = '<option value="">Loading...</option>';
    var baseUrl = getBaseUrl();

    // Fetch entity list based on type
    var url;
    if (dataType === 'gauge') url = baseUrl + '/api/v1/gauges';
    else if (dataType === 'property') url = baseUrl + '/api/v1/properties';
    else if (dataType === 'trade') url = baseUrl + '/api/v1/trading/blotter';
    else if (dataType === 'counterparty') url = baseUrl + '/api/v1/counterparties';
    else { idSelect.innerHTML = '<option value="">Select type first</option>'; return; }

    fetch(url, {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var items = [];
            if (dataType === 'gauge') {
                (data.gauges || data.flood_gauges || []).forEach(function(g) {
                    var fg = g.FloodGauge || g;
                    var hdr = (fg.Header || fg.header || g);
                    var id = hdr.GaugeID || hdr.gauge_id || g.gaugeId || g.gauge_id || '';
                    var name = hdr.GaugeName || hdr.gauge_name || g.name || hdr.name || '';
                    if (id) items.push({id: id, label: name ? id + ' — ' + name : id});
                });
            } else if (dataType === 'property') {
                (data.properties || []).forEach(function(p) {
                    var hdr = (p.PropertyHeader || {}).Header || p.Header || p;
                    var id = hdr.PropertyID || hdr.property_id || p.propertyId || '';
                    var addr = (p.PropertyHeader || {}).Location || p;
                    var label = addr.Street || addr.AddressLine1 || addr.address || addr.county || '';
                    if (id) items.push({id: id, label: label ? id + ' — ' + label : id});
                });
            } else if (dataType === 'trade') {
                (data.trades || []).forEach(function(t) {
                    var id = t.swap_id || t.SwapID || '';
                    var gauge = t.gauge_name || t.gauge_id || '';
                    if (id) items.push({id: id, label: gauge ? id + ' — ' + gauge : id});
                });
            } else if (dataType === 'counterparty') {
                (data.counterparties || []).forEach(function(c) {
                    var id = c.counterparty_id || '';
                    var name = c.short_name || c.name || '';
                    if (id) items.push({id: id, label: name ? id + ' — ' + name : id});
                });
            }
            items.sort(function(a, b) { return a.label.localeCompare(b.label); });
            _lineageIdCache[dataType] = items;
            _lineageRenderIdOptions(idSelect, items);
        })
        .catch(function() {
            idSelect.innerHTML = '<option value="">Failed to load</option>';
        });
};

function _lineageRenderIdOptions(selectEl, items) {
    var html = '<option value="">— Select (' + items.length + ') —</option>';
    items.forEach(function(item) {
        html += '<option value="' + item.id + '">' + item.label + '</option>';
    });
    selectEl.innerHTML = html;
}

window._lineageTrace = function() {
    var dataType = document.getElementById('lineage-trace-type').value;
    var idSelect = document.getElementById('lineage-trace-id');
    var dataId = idSelect ? idSelect.value : '';
    var resultDiv = document.getElementById('lineage-trace-result');
    if (!dataId) {
        resultDiv.innerHTML = '<div style="font-size:11px;color:#f44336;">Please select an entity to trace.</div>';
        return;
    }
    resultDiv.innerHTML = '<div style="font-size:11px;color:#888;">Tracing...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/data-lineage/trace?data_type=' + encodeURIComponent(dataType) + '&data_id=' + encodeURIComponent(dataId), {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                resultDiv.innerHTML = '<div style="font-size:11px;color:#f44336;">Error: ' + (data.message || 'Unknown') + '</div>';
                return;
            }
            if (!data.found || data.trace.length === 0) {
                resultDiv.innerHTML = '<div style="font-size:11px;color:#888;">No provenance records found for <b>' + dataType + '/' + dataId + '</b>.</div>';
                return;
            }
            // Render visual provenance trail
            var roleColors = {origin: '#1565c0', derived: '#2e7d32', consumed: '#e65100', found: '#616161'};
            var roleIcons = {origin: '\u25cf', derived: '\u2192', consumed: '\u25b6', found: '\u2605'};
            var html = '<div style="padding:8px 0;">';
            html += '<div style="font-size:11px;color:#333;margin-bottom:8px;font-weight:600;">' +
                data.trace.length + ' provenance step' + (data.trace.length > 1 ? 's' : '') +
                ' for <span style="font-family:monospace;color:#1565c0;">' + dataId + '</span></div>';

            // Breadcrumb arrows
            html += '<div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;margin-bottom:12px;">';
            data.trace.forEach(function(t, i) {
                var col = roleColors[t.role] || '#616161';
                html += '<div style="padding:3px 10px;border-radius:12px;background:' + col + ';color:white;font-size:10px;font-weight:600;">' + t.step + '</div>';
                if (i < data.trace.length - 1) html += '<span style="color:#bbb;font-size:14px;">\u25b8</span>';
            });
            html += '</div>';

            // Detail table
            html += '<table style="width:100%;font-size:10px;border-collapse:collapse;">';
            html += '<thead><tr style="background:#eceff1;">';
            html += '<th style="padding:5px 8px;text-align:left;">Step</th>';
            html += '<th style="padding:5px 8px;text-align:left;">Role</th>';
            html += '<th style="padding:5px 8px;text-align:left;">File</th>';
            html += '<th style="padding:5px 8px;text-align:left;">Context</th>';
            html += '</tr></thead><tbody>';
            data.trace.forEach(function(t, i) {
                var col = roleColors[t.role] || '#616161';
                var bg = i % 2 === 0 ? '#fff' : '#f8f9fa';
                html += '<tr style="background:' + bg + ';border-bottom:1px solid #eee;">';
                html += '<td style="padding:5px 8px;font-weight:600;color:' + col + ';">' + (roleIcons[t.role] || '') + ' ' + t.step + '</td>';
                html += '<td style="padding:5px 8px;color:#666;">' + t.role + '</td>';
                html += '<td style="padding:5px 8px;font-family:monospace;font-size:9px;color:#555;">' + (t.file || '') + '</td>';
                html += '<td style="padding:5px 8px;color:#888;">' + (t.context || '') + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table></div>';
            resultDiv.innerHTML = html;
        })
        .catch(function(err) {
            resultDiv.innerHTML = '<div style="font-size:11px;color:#f44336;">Trace request failed.</div>';
            console.error('[Governance] Trace error:', err);
        });
};

// ================================================================

