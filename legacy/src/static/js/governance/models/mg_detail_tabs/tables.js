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

function renderRemediationTab(m) {
    var steps = m.remediation_steps || [];
    if (steps.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No remediation steps recorded</div>';

    var openCount = steps.filter(function(r) { return r.status === 'Open'; }).length;
    var closedCount = steps.filter(function(r) { return r.status === 'Closed'; }).length;

    var html = '<div style="padding:12px;">';

    // Summary bar
    html += '<div style="display:flex;gap:16px;margin-bottom:12px;">';
    html += '<div style="padding:8px 14px;border-radius:6px;background:#fff3e0;border-left:3px solid #f57c00;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Open</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#e65100;margin-left:8px;">' + openCount + '</span></div>';
    html += '<div style="padding:8px 14px;border-radius:6px;background:#e8f5e9;border-left:3px solid #388e3c;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Closed</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#388e3c;margin-left:8px;">' + closedCount + '</span></div>';
    html += '<div style="padding:8px 14px;border-radius:6px;background:#f5f5f5;border-left:3px solid #666;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Total</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#333;margin-left:8px;">' + steps.length + '</span></div>';
    html += '</div>';

    // Table
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Description', 'Owner', 'Priority', 'Due Date', 'Status'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    var priorityColors = {'High': '#d32f2f', 'Medium': '#f57c00', 'Low': '#1976d2'};
    var statusColors = {'Open': '#e65100', 'In Progress': '#1976d2', 'Closed': '#388e3c'};

    steps.forEach(function(r) {
        var isOverdue = r.status === 'Open' && r.due_date && new Date(r.due_date) < new Date();
        var rowStyle = isOverdue ? 'background:#fff8e1;' : '';
        html += '<tr style="' + rowStyle + '">';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + r.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + r.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + r.owner + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(r.priority, priorityColors[r.priority] || '#999') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (r.due_date || '\u2014') + (isOverdue ? ' <span style="color:#d32f2f;font-size:9px;font-weight:600;">OVERDUE</span>' : '') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(r.status, statusColors[r.status] || '#999') + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    return html;
}

function renderLimitationsTab(m) {
    var lims = m.limitations || [];
    if (lims.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No limitations documented</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Description', 'Impact', 'Monitoring Trigger', 'Compensating Control'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    lims.forEach(function(l) {
        var impactColor = l.impact === 'High' ? '#d32f2f' : l.impact === 'Medium' ? '#f57c00' : '#388e3c';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + l.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + l.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(l.impact, impactColor) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + (l.monitoring_trigger || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#333;">' + (l.compensating_control || '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderAssumptionsTab(m) {
    var assumptions = m.assumptions || [];
    if (assumptions.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No assumptions documented</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Assumption', 'Impact', 'Monitoring', 'Mitigation'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    assumptions.forEach(function(a) {
        var impactColor = a.impact === 'High' ? '#d32f2f' : a.impact === 'Medium' ? '#f57c00' : '#388e3c';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + a.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + a.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(a.impact, impactColor) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + (a.monitoring || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#333;">' + (a.mitigation || '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderChangesTab(m) {
    var changes = m.change_history || [];
    if (changes.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No change history</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Version', 'Date', 'Author', 'Type', 'Description'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    changes.forEach(function(c) {
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;">' + c.version + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + c.date + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + c.author + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(c.type, '#1976d2') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + c.description + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderAuditTab(entries) {
    if (!entries || entries.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No audit entries for this model</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Timestamp', 'Event', 'User', 'Action', 'Source'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    entries.slice().reverse().forEach(function(e) {
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;font-size:10px;">' + e.timestamp + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(e.event_type, '#1976d2') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + e.user + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + e.action + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + e.source + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}
