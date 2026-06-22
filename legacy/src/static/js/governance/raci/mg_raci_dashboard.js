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
// RACI Operating Model Dashboard
// ================================================================

var raciData = null;
var raciExpandedActivity = null;
var raciSections = {roles: true, activities: true, escalation: true};

function raciCodeColor(code) {
    if (code === 'R') return '#1976d2';
    if (code === 'A') return '#d32f2f';
    if (code === 'C') return '#f57c00';
    if (code === 'I') return '#388e3c';
    return '#9e9e9e';
}

function raciRoleLabel(roleId) {
    if (!raciData || !raciData.roles) return roleId || '\u2014';
    var role = raciData.roles.find(function(r) { return r.role_id === roleId; });
    return role ? role.label : (roleId || '\u2014');
}

function raciRoleBadge(code, roleId) {
    if (!roleId) return '<span style="color:#ccc;">\u2014</span>';
    var color = raciCodeColor(code);
    return '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:9px;font-weight:600;background:' + color + '22;color:' + color + ';border:1px solid ' + color + '44;">' + code + '</span>';
}

function urgencyColor(text) {
    if (!text) return '#9e9e9e';
    var lower = text.toLowerCase();
    if (lower.indexOf('immediate') !== -1) return '#d32f2f';
    if (lower.indexOf('same day') !== -1 || lower.indexOf('within 24') !== -1) return '#f57c00';
    return '#388e3c';
}

function renderRACITab() {
    var content = document.getElementById('mg-content');
    content.style.overflowY = 'hidden';
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading RACI operating model...</div>';

    console.log('[RACI] Fetching RACI matrix');
    fetch(getBaseUrl() + '/api/v1/governance/raci', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">RACI matrix not found</div>';
                return;
            }
            raciData = data.raci;
            console.log('[RACI] Loaded', (raciData.roles || []).length, 'roles,', (raciData.activities || []).length, 'activities,', (raciData.escalation_triggers || []).length, 'triggers');
            renderRACIDashboard();
        })
        .catch(function(err) {
            console.error('[RACI] Load error:', err);
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + err.message + '</div>';
        });
}

function renderRACIDashboard() {
    var content = document.getElementById('mg-content');
    var roles = raciData.roles || [];
    var activities = raciData.activities || [];
    var triggers = raciData.escalation_triggers || [];

    var assignedCount = roles.filter(function(r) { return r.assigned_to && r.assigned_to !== 'TBD'; }).length;

    // Coverage: activities with at least R and A assigned
    var coveredCount = activities.filter(function(a) { return a.R && a.A; }).length;
    var coveragePct = activities.length > 0 ? Math.round(coveredCount / activities.length * 100) : 0;

    var html = '<div style="display:flex;flex-direction:column;height:100%;">';

    // ---- Header ----
    html += '<div style="padding:16px;flex-shrink:0;">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div>';
    html += '<div style="font-size:15px;font-weight:700;color:#333;">RACI Operating Model</div>';
    html += '<div style="font-size:11px;color:#888;">Chapter 10: Roles, Activities & Escalation Framework</div>';
    html += '</div>';
    html += '</div>';

    // Summary cards
    html += '<div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;">';
    var cards = [
        {label: 'Roles Assigned', value: assignedCount + '/' + roles.length, color: assignedCount === roles.length ? '#388e3c' : '#f57c00'},
        {label: 'Activities', value: activities.length, color: '#1976d2'},
        {label: 'Escalation Triggers', value: triggers.length, color: '#d32f2f'},
        {label: 'R/A Coverage', value: coveragePct + '%', color: coveragePct === 100 ? '#388e3c' : '#f57c00'},
    ];
    cards.forEach(function(c) {
        html += '<div style="flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';">';
        html += '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>';
        html += '<div style="font-size:18px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
        html += '</div>';
    });
    html += '</div>';
    html += '</div>';

    // ---- Scrollable content ----
    html += '<div style="flex:1;overflow-y:auto;padding:0 16px 16px 16px;min-height:0;">';

    // ================================================================
    // Section 1: Role Assignments
    // ================================================================
    html += renderRaciSectionHeader('roles', 'Role Assignments', roles.length + ' roles');

    if (raciSections.roles) {
        html += '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:20px;">';
        html += '<thead><tr style="background:#fafafa;">';
        ['RACI', 'Role', 'Description', 'Assigned To', 'Backup', ''].forEach(function(h) {
            html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#fafafa;">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';

        roles.forEach(function(r) {
            html += '<tr onmouseenter="this.style.background=\'#f5f5f5\'" onmouseleave="this.style.background=\'\';">';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">';
            html += '<span style="display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;border-radius:50%;font-size:12px;font-weight:700;color:white;background:' + raciCodeColor(r.raci_code) + ';">' + r.raci_code + '</span>';
            html += '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#333;">' + r.label + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;color:#666;font-size:10px;max-width:300px;">' + r.description + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:500;color:' + (r.assigned_to === 'TBD' ? '#f57c00' : '#333') + ';">' + (r.assigned_to || '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;color:#888;">' + (r.backup || '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">';
            html += '<button onclick="window.MG.showRaciEditRole(\'' + r.role_id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;">Edit</button>';
            html += '</td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        html += '<div id="raci-role-edit-area"></div>';
    }

    // ================================================================
    // Section 2: Activity Matrix
    // ================================================================
    html += renderRaciSectionHeader('activities', 'RACI Activity Matrix', activities.length + ' activities');

    if (raciSections.activities) {
        html += '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:20px;">';
        html += '<thead><tr style="background:#fafafa;">';
        ['Category', 'Activity', 'R', 'A', 'C', 'I', 'Tier Emphasis', ''].forEach(function(h) {
            html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#fafafa;">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';

        var lastCategory = '';
        activities.forEach(function(act) {
            // Category group header
            if (act.category !== lastCategory) {
                lastCategory = act.category;
                html += '<tr><td colspan="8" style="padding:8px 10px;background:#e8eaf6;font-size:10px;font-weight:700;color:#283593;letter-spacing:0.5px;text-transform:uppercase;border-bottom:1px solid #c5cae9;">' + act.category + '</td></tr>';
            }

            var isExpanded = raciExpandedActivity === act.activity_id;

            html += '<tr style="cursor:pointer;" onmouseenter="this.style.background=\'#f5f5f5\'" onmouseleave="this.style.background=\'\';" onclick="window.MG.toggleRaciActivity(\'' + act.activity_id + '\')">';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#888;">\u00A0</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;color:#333;">' + act.activity + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + raciRoleBadge('R', act.R) + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + raciRoleBadge('A', act.A) + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + raciRoleBadge('C', act.C) + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + raciRoleBadge('I', act.I) + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + (act.tier_emphasis || '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">';
            html += '<button onclick="event.stopPropagation();window.MG.showRaciEditActivity(\'' + act.activity_id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;">Edit</button>';
            html += '</td>';
            html += '</tr>';

            // Expanded notes row
            if (isExpanded && act.notes) {
                html += '<tr><td colspan="8" style="padding:0;border-bottom:1px solid #e0e0e0;">';
                html += '<div style="padding:8px 16px;background:#f8fafc;border-left:3px solid #1976d2;font-size:11px;color:#555;">';
                html += '<span style="font-size:10px;color:#888;font-weight:600;">NOTES: </span>' + act.notes;
                html += '</div></td></tr>';
            }
        });

        html += '</tbody></table>';
        html += '<div id="raci-activity-edit-area"></div>';
    }

    // ================================================================
    // Section 3: Escalation Triggers
    // ================================================================
    html += renderRaciSectionHeader('escalation', 'Escalation Triggers', triggers.length + ' triggers');

    if (raciSections.escalation) {
        html += '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:20px;">';
        html += '<thead><tr style="background:#fafafa;">';
        ['Trigger', 'From', 'To', 'Tier 1', 'Tier 2', 'Tier 3', 'Response Required', ''].forEach(function(h) {
            html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;background:#fafafa;">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';

        triggers.forEach(function(t) {
            var th = t.tier_threshold || {};
            html += '<tr onmouseenter="this.style.background=\'#f5f5f5\'" onmouseleave="this.style.background=\'\';">';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:500;color:#333;">' + t.trigger + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + raciRoleLabel(t.from_role) + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + raciRoleLabel(t.to_role) + '</td>';

            ['1', '2', '3'].forEach(function(tier) {
                var val = th[tier] || '\u2014';
                var uc = urgencyColor(val);
                html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">';
                html += '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:9px;font-weight:600;background:' + uc + '22;color:' + uc + ';border:1px solid ' + uc + '44;">' + val + '</span>';
                html += '</td>';
            });

            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#555;max-width:200px;">' + (t.response_required || '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">';
            html += '<button onclick="window.MG.showRaciEditEscalation(\'' + t.trigger_id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;">Edit</button>';
            html += '</td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        html += '<div id="raci-escalation-edit-area"></div>';
    }

    // Close scrollable area + outer flex
    html += '</div></div>';
    content.innerHTML = html;
}

function renderRaciSectionHeader(sectionKey, title, subtitle) {
    var isOpen = raciSections[sectionKey];
    var arrow = isOpen ? '\u25BC' : '\u25B6';
    var html = '<div onclick="raciSections.' + sectionKey + '=!raciSections.' + sectionKey + ';renderRACIDashboard();" ';
    html += 'style="cursor:pointer;display:flex;align-items:center;gap:8px;padding:10px 0 6px 0;border-bottom:2px solid #1976d2;margin-bottom:8px;">';
    html += '<span style="font-size:12px;color:#1976d2;">' + arrow + '</span>';
    html += '<span style="font-size:13px;font-weight:700;color:#1976d2;">' + title + '</span>';
    html += '<span style="font-size:10px;color:#888;">(' + subtitle + ')</span>';
    html += '</div>';
    return html;
}

