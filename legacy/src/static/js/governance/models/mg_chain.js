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
// Model chain (string of pearls)
// ================================================================
function renderModelChain() {
    if (!mgData || !mgData.model_chain) return;
    console.log('[Governance] Rendering model chain (' + mgData.model_chain.links.length + ' links)');
    var content = document.getElementById('mg-content');
    var chain = mgData.model_chain;
    var models = mgData.models;

    var html = '<div style="padding:16px;">';
    html += '<div style="font-size:13px;font-weight:700;color:#333;margin-bottom:12px;">Model Dependency Chain (String of Pearls)</div>';
    html += '<div style="font-size:11px;color:#666;margin-bottom:16px;">' + chain.description + '</div>';

    // Helper: render a chain node circle
    function chainNode(mid) {
        var m = models.find(function(x) { return x.model_id === mid; });
        if (!m) return '';
        var h = '<div style="text-align:center;cursor:pointer;" onclick="window.MG.showDetail(\'' + mid + '\')">';
        h += '<div style="width:100px;height:100px;border-radius:50%;background:linear-gradient(135deg, ' + tierColors[m.tier] + '22, ' + tierColors[m.tier] + '44);border:3px solid ' + tierColors[m.tier] + ';display:flex;align-items:center;justify-content:center;margin:0 auto;">';
        h += '<div style="text-align:center;">';
        h += '<div style="font-size:18px;">' + (catIcons[m.category] || '') + '</div>';
        h += '<div style="font-size:9px;font-weight:700;color:' + tierColors[m.tier] + ';margin-top:2px;">T' + m.tier + '</div>';
        h += '</div></div>';
        h += '<div style="font-size:10px;font-weight:600;color:#333;margin-top:6px;">' + m.short_name + '</div>';
        h += '<div style="font-size:9px;color:#888;">' + m.model_id + '</div>';
        h += '</div>';
        return h;
    }
    function chainArrow(label) {
        var h = '<div style="display:flex;flex-direction:column;align-items:center;padding:0 8px;">';
        h += '<div style="font-size:18px;color:#999;">→</div>';
        h += '<div style="font-size:8px;color:#888;max-width:80px;text-align:center;">' + label + '</div>';
        h += '</div>';
        return h;
    }

    // Pricing chain: SI -> SG -> GH -> PR
    var chainOrder = ['MKM-SI-001', 'MKM-SG-001', 'MKM-GH-001', 'MKM-PR-001'];
    html += '<div style="font-size:10px;font-weight:600;color:#888;margin-bottom:4px;">Pricing Chain</div>';
    html += '<div style="display:flex;align-items:center;justify-content:center;gap:0;padding:12px 0;flex-wrap:wrap;">';
    chainOrder.forEach(function(mid, idx) {
        html += chainNode(mid);
        if (idx < chainOrder.length - 1) {
            var link = chain.links.find(function(l) { return l.from === mid && l.to === chainOrder[idx + 1]; });
            html += chainArrow(link ? link.data_handoff : '');
        }
    });
    html += '</div>';

    // Stress branch: SG -> FC -> DE
    var stressBranch = ['MKM-SG-001', 'MKM-FC-001', 'MKM-DE-001'];
    var hasBranch = stressBranch.every(function(mid) {
        return models.find(function(x) { return x.model_id === mid; });
    });
    if (hasBranch) {
        html += '<div style="display:flex;align-items:flex-start;margin-top:4px;margin-bottom:8px;">';
        // Spacer to align under SG node
        html += '<div style="flex:1;"></div>';
        html += '<div style="display:flex;flex-direction:column;align-items:center;">';
        html += '<div style="width:2px;height:20px;background:#ccc;"></div>';
        html += '<div style="font-size:8px;color:#888;margin:2px 0;">stress branch</div>';
        html += '<div style="width:2px;height:8px;background:#ccc;"></div>';
        html += '<div style="display:flex;align-items:center;gap:0;">';
        stressBranch.forEach(function(mid, idx) {
            html += chainNode(mid);
            if (idx < stressBranch.length - 1) {
                var link = chain.links.find(function(l) { return l.from === mid && l.to === stressBranch[idx + 1]; });
                html += chainArrow(link ? link.data_handoff : '');
            }
        });
        html += '</div>';
        html += '</div>';
        html += '<div style="flex:1;"></div>';
        html += '</div>';
    }

    // Supporting models
    html += '<div style="margin-top:24px;padding-top:16px;border-top:1px solid #eee;">';
    html += '<div style="font-size:12px;font-weight:700;color:#333;margin-bottom:12px;">Supporting Models</div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap;">';

    var diagramModels = chainOrder.concat(stressBranch || []);
    var supportModels = models.filter(function(m) {
        return diagramModels.indexOf(m.model_id) === -1;
    });
    supportModels.forEach(function(m) {
        html += '<div style="padding:10px 14px;border:1px solid #e0e0e0;border-radius:6px;cursor:pointer;min-width:180px;border-left:3px solid ' + tierColors[m.tier] + ';" onclick="window.MG.showDetail(\'' + m.model_id + '\')">';
        html += '<div style="font-size:11px;font-weight:600;color:#333;">' + (catIcons[m.category] || '') + ' ' + m.short_name + '</div>';
        html += '<div style="font-size:9px;color:#888;margin-top:2px;">' + m.model_id + ' &middot; ' + tierBadge(m.tier) + '</div>';
        html += '</div>';
    });
    html += '</div></div>';

    // Link detail table with expandable fields
    html += '<div style="margin-top:24px;padding-top:16px;border-top:1px solid #eee;">';
    html += '<div style="font-size:12px;font-weight:700;color:#333;margin-bottom:8px;">Data Handoffs</div>';
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['From', 'To', 'Data Handoff', 'Granularity', 'Fields'].forEach(function(h) {
        html += '<th style="padding:6px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';
    chain.links.forEach(function(l, li) {
        var fields = l.fields || [];
        var rowId = 'mg-chain-fields-' + li;
        html += '<tr style="cursor:pointer;" onclick="var el=document.getElementById(\'' + rowId + '\');el.style.display=el.style.display===\'none\'?\'table-row\':\'none\';">';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1976d2;">' + l.from + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1976d2;">' + l.to + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">' + l.data_handoff + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + l.granularity + '</td>';
        html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">';
        if (fields.length > 0) {
            html += '<span style="color:#1976d2;font-size:10px;">▶ ' + fields.length + ' fields</span>';
        }
        html += '</td>';
        html += '</tr>';

        // Expandable field detail row
        if (fields.length > 0) {
            html += '<tr id="' + rowId + '" style="display:none;">';
            html += '<td colspan="5" style="padding:0 10px 10px 24px;background:#f8fafc;border-bottom:2px solid #e3f2fd;">';
            html += '<table style="width:100%;border-collapse:collapse;font-size:10px;margin-top:4px;">';
            html += '<tr style="background:#e3f2fd;"><th style="padding:4px 8px;text-align:left;color:#1565c0;">Field</th><th style="padding:4px 8px;text-align:left;color:#1565c0;">Type</th><th style="padding:4px 8px;text-align:left;color:#1565c0;">Description</th></tr>';
            fields.forEach(function(f) {
                html += '<tr>';
                html += '<td style="padding:3px 8px;border-bottom:1px solid #e8eaf6;font-family:monospace;font-weight:600;color:#333;white-space:nowrap;">' + f.name + '</td>';
                html += '<td style="padding:3px 8px;border-bottom:1px solid #e8eaf6;color:#888;white-space:nowrap;">' + f.type + '</td>';
                html += '<td style="padding:3px 8px;border-bottom:1px solid #e8eaf6;color:#555;">' + f.description + '</td>';
                html += '</tr>';
            });
            html += '</table></td></tr>';
        }
    });
    html += '</tbody></table></div>';

    html += '</div>';
    content.innerHTML = html;
}

// ================================================================

