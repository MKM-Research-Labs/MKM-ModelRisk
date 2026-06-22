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
// Field Lineage tab — BCBS 239 Principle 3
// ================================================================
function renderFieldLineage() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading field lineage registry...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/field-lineage', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + (data.message || 'Unknown') + '</div>';
                return;
            }
            window._fieldLineageData = data;
            _drawFieldLineagePanel(data);
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load field lineage registry.</div>';
            console.error('[Governance] Field lineage load error:', err);
        });
}

function _flSourceBadge(source) {
    if (!source || source === 'computed at runtime' || source === 'hardcoded') {
        return '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;color:white;background:#9c27b0;">COMPUTED</span>';
    }
    return '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;color:white;background:#1976d2;">FILE</span>';
}

function _flStepBadge(step) {
    if (!step) return '<span style="font-size:9px;color:#999;">\u2014</span>';
    var colors = {
        gauges: '#4caf50', properties: '#2196f3', mortgages: '#ff9800',
        gaugehd: '#009688', stressm: '#e91e63', hazard: '#f44336',
        propertyts: '#795548', propertyhc: '#607d8b', counterparties: '#9c27b0',
        blotter: '#ff5722'
    };
    var bg = colors[step] || '#999';
    return '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;color:white;background:' + bg + ';">' + step + '</span>';
}

function _drawFieldLineagePanel(data) {
    var content = document.getElementById('mg-content');
    var reports = data.reports || {};
    var summary = data.summary || [];
    var html = '<div style="padding:16px;">';

    // Header
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">';
    html += '<div>';
    html += '<div style="font-size:13px;font-weight:700;color:#333;">Field-Level Data Lineage</div>';
    html += '<div style="font-size:11px;color:#666;margin-top:2px;">BCBS 239 Principle 3 \u2014 every field traceable to its source</div>';
    html += '</div>';
    html += '<div style="text-align:right;">';
    html += '<span style="font-size:22px;font-weight:700;color:#1976d2;">' + data.total_fields + '</span>';
    html += '<div style="font-size:10px;color:#888;">fields mapped across ' + data.total_reports + ' reports</div>';
    html += '</div></div>';

    // Search bar
    html += '<div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">';
    html += '<input id="fl-search" type="text" placeholder="Search fields (e.g. fair_spread, notional, GEV...)" style="flex:1;padding:6px 10px;font-size:11px;border:1px solid #ddd;border-radius:4px;" />';
    html += '<button onclick="window._flSearch()" style="padding:6px 14px;font-size:11px;font-weight:600;border:1px solid #1976d2;border-radius:4px;background:#1976d2;color:white;cursor:pointer;">Search</button>';
    html += '</div>';
    html += '<div id="fl-search-result"></div>';

    // Report cards
    html += '<div style="font-size:11px;font-weight:600;color:#555;margin:8px 0;">Reports & Screens</div>';
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-bottom:16px;">';
    summary.forEach(function(r) {
        html += '<div onclick="window._flExpandReport(\'' + r.report + '\')" style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;cursor:pointer;transition:box-shadow 0.15s;" onmouseover="this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.1)\'" onmouseout="this.style.boxShadow=\'none\'">';
        html += '<div style="font-size:11px;font-weight:700;color:#333;">' + r.label + '</div>';
        html += '<div style="font-size:9px;color:#888;margin-top:2px;font-family:monospace;">' + r.generator + '</div>';
        html += '<div style="margin-top:6px;display:flex;gap:12px;">';
        html += '<span style="font-size:10px;color:#666;">' + r.section_count + ' sections</span>';
        html += '<span style="font-size:10px;color:#1976d2;font-weight:600;">' + r.field_count + ' fields</span>';
        html += '</div></div>';
    });
    html += '</div>';

    // Expanded report detail area
    html += '<div id="fl-report-detail"></div>';

    html += '</div>';
    content.innerHTML = html;

    // Enter key triggers search
    var searchInput = document.getElementById('fl-search');
    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') window._flSearch();
        });
    }
}

window._flSearch = function() {
    var query = document.getElementById('fl-search').value.trim();
    var resultDiv = document.getElementById('fl-search-result');
    if (!query) {
        resultDiv.innerHTML = '';
        return;
    }
    resultDiv.innerHTML = '<div style="font-size:11px;color:#888;">Searching...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/field-lineage/lookup?search=' + encodeURIComponent(query), {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success' || data.count === 0) {
                resultDiv.innerHTML = '<div style="font-size:11px;color:#888;padding:8px 0;">No fields matched "<b>' + query + '</b>".</div>';
                return;
            }
            var html = '<div style="margin-bottom:12px;font-size:10px;color:#666;">' + data.count + ' field(s) matched</div>';
            html += '<table style="width:100%;border-collapse:collapse;font-size:10px;margin-bottom:16px;">';
            html += '<thead><tr style="background:#f5f5f5;">';
            ['Report', 'Field', 'Label', 'Source', 'Pipeline Step', 'CDM Path'].forEach(function(h) {
                html += '<th style="padding:5px 8px;text-align:left;border-bottom:2px solid #ddd;font-size:9px;color:#555;">' + h + '</th>';
            });
            html += '</tr></thead><tbody>';
            data.results.forEach(function(r) {
                var l = r.lineage;
                html += '<tr>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid #f0f0f0;color:#333;font-weight:500;">' + r.report_label + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid #f0f0f0;font-family:monospace;color:#1976d2;">' + r.field + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid #f0f0f0;">' + (l.label || '') + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid #f0f0f0;">' + _flSourceBadge(l.source_field) + ' <span style="font-family:monospace;font-size:9px;color:#666;">' + (l.source_file || 'runtime') + '</span></td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid #f0f0f0;">' + _flStepBadge(l.pipeline_step) + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid #f0f0f0;font-family:monospace;font-size:9px;color:#888;">' + (l.cdm_path || '\u2014') + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';
            resultDiv.innerHTML = html;
        })
        .catch(function(err) {
            resultDiv.innerHTML = '<div style="font-size:11px;color:#f44336;">Search failed.</div>';
        });
};

window._flExpandReport = function(reportKey) {
    var detailDiv = document.getElementById('fl-report-detail');
    var data = window._fieldLineageData;
    if (!data || !data.reports[reportKey]) return;

    var report = data.reports[reportKey];
    var html = '<div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px;margin-top:4px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">';
    html += '<div style="font-size:12px;font-weight:700;color:#333;">' + report.label + '</div>';
    html += '<button onclick="document.getElementById(\'fl-report-detail\').innerHTML=\'\'" style="border:none;background:none;font-size:16px;cursor:pointer;color:#999;">&times;</button>';
    html += '</div>';

    var sections = report.sections || {};
    Object.keys(sections).forEach(function(skey) {
        var sec = sections[skey];
        var fields = sec.fields || {};
        html += '<div style="margin-bottom:14px;">';
        html += '<div style="font-size:10px;font-weight:600;color:#555;padding:4px 0;border-bottom:1px solid #eee;margin-bottom:6px;">' + sec.label + '</div>';
        html += '<table style="width:100%;border-collapse:collapse;font-size:10px;">';
        html += '<thead><tr style="background:#fafafa;">';
        ['Field', 'Label', 'Source File', 'Source Field', 'Step', 'CDM Path', 'Computation'].forEach(function(h) {
            html += '<th style="padding:4px 6px;text-align:left;font-size:9px;color:#777;border-bottom:1px solid #eee;">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';
        Object.keys(fields).forEach(function(fkey) {
            var f = fields[fkey];
            html += '<tr>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;font-family:monospace;color:#1976d2;font-weight:500;">' + fkey + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;">' + (f.label || '') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;font-family:monospace;font-size:9px;color:#666;">' + (f.source_file || '\u2014') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;font-family:monospace;font-size:9px;color:#666;">' + (f.source_field || '\u2014') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;">' + _flStepBadge(f.pipeline_step) + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;font-family:monospace;font-size:9px;color:#888;">' + (f.cdm_path || '\u2014') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid #f5f5f5;font-size:9px;color:#555;max-width:200px;">' + (f.computation || '\u2014') + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div>';
    });

    html += '</div>';
    detailDiv.innerHTML = html;
    detailDiv.scrollIntoView({behavior: 'smooth', block: 'nearest'});
};

// ================================================================

