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
// RACI Inline edit forms
// ================================================================

function showRaciEditRole(roleId) {
    var area = document.getElementById('raci-role-edit-area');
    if (!area) return;
    var role = (raciData.roles || []).find(function(r) { return r.role_id === roleId; });
    if (!role) return;

    var html = '<div style="padding:16px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-top:8px;">';
    html += '<div style="font-size:12px;font-weight:600;color:#333;margin-bottom:10px;">Edit Role: ' + role.label + ' (' + role.raci_code + ')</div>';

    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Assigned To</label>';
    html += '<input type="text" id="raci-role-assigned" value="' + (role.assigned_to || '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Backup</label>';
    html += '<input type="text" id="raci-role-backup" value="' + (role.backup || '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '</div>';

    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.saveRaciRole(\'' + roleId + '\')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'raci-role-edit-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRaciRole(roleId) {
    console.log('[RACI] Saving role', roleId);
    var body = {
        assigned_to: document.getElementById('raci-role-assigned').value,
        backup: document.getElementById('raci-role-backup').value || null,
        user: 'Dashboard User',
    };

    fetch(getBaseUrl() + '/api/v1/governance/raci/roles/' + roleId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[RACI] Role', roleId, 'saved successfully');
            raciData = data.raci;
            renderRACIDashboard();
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function toggleRaciActivity(activityId) {
    if (raciExpandedActivity === activityId) {
        raciExpandedActivity = null;
    } else {
        raciExpandedActivity = activityId;
    }
    renderRACIDashboard();
}

function showRaciEditActivity(activityId) {
    var area = document.getElementById('raci-activity-edit-area');
    if (!area) return;
    var act = (raciData.activities || []).find(function(a) { return a.activity_id === activityId; });
    if (!act) return;

    var roles = raciData.roles || [];

    var html = '<div style="padding:16px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-top:8px;">';
    html += '<div style="font-size:12px;font-weight:600;color:#333;margin-bottom:10px;">Edit Activity: ' + act.activity + '</div>';

    html += '<div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:8px;margin-bottom:10px;">';
    ['R', 'A', 'C', 'I'].forEach(function(code) {
        var codeLabel = code === 'R' ? 'Responsible' : code === 'A' ? 'Accountable' : code === 'C' ? 'Consulted' : 'Informed';
        html += '<div><label style="font-size:10px;color:' + raciCodeColor(code) + ';font-weight:600;display:block;margin-bottom:2px;">' + code + ' \u2014 ' + codeLabel + '</label>';
        html += '<select id="raci-act-' + code + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;">';
        html += '<option value="">None</option>';
        roles.forEach(function(r) {
            html += '<option value="' + r.role_id + '"' + (act[code] === r.role_id ? ' selected' : '') + '>' + r.label + '</option>';
        });
        html += '</select></div>';
    });
    html += '</div>';

    html += '<div style="margin-bottom:8px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Tier Emphasis</label>';
    html += '<input type="text" id="raci-act-tier" value="' + (act.tier_emphasis || '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';

    html += '<div style="margin-bottom:10px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Notes</label>';
    html += '<textarea id="raci-act-notes" rows="2" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;line-height:1.5;">' + (act.notes || '') + '</textarea></div>';

    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.saveRaciActivity(\'' + activityId + '\')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'raci-activity-edit-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRaciActivity(activityId) {
    console.log('[RACI] Saving activity', activityId);
    var body = {
        R: document.getElementById('raci-act-R').value || null,
        A: document.getElementById('raci-act-A').value || null,
        C: document.getElementById('raci-act-C').value || null,
        I: document.getElementById('raci-act-I').value || null,
        tier_emphasis: document.getElementById('raci-act-tier').value || null,
        notes: document.getElementById('raci-act-notes').value,
        user: 'Dashboard User',
    };

    fetch(getBaseUrl() + '/api/v1/governance/raci/activities/' + activityId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[RACI] Activity', activityId, 'saved successfully');
            raciData = data.raci;
            renderRACIDashboard();
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function showRaciEditEscalation(triggerId) {
    var area = document.getElementById('raci-escalation-edit-area');
    if (!area) return;
    var trig = (raciData.escalation_triggers || []).find(function(t) { return t.trigger_id === triggerId; });
    if (!trig) return;

    var th = trig.tier_threshold || {};

    var html = '<div style="padding:16px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-top:8px;">';
    html += '<div style="font-size:12px;font-weight:600;color:#333;margin-bottom:10px;">Edit Escalation: ' + trig.trigger + '</div>';

    html += '<div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:8px;margin-bottom:10px;">';
    ['1', '2', '3'].forEach(function(tier) {
        html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Tier ' + tier + ' Threshold</label>';
        html += '<input type="text" id="raci-esc-t' + tier + '" value="' + (th[tier] || '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    });
    html += '</div>';

    html += '<div style="margin-bottom:10px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Response Required</label>';
    html += '<textarea id="raci-esc-response" rows="2" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;line-height:1.5;">' + (trig.response_required || '') + '</textarea></div>';

    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.saveRaciEscalation(\'' + triggerId + '\')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'raci-escalation-edit-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRaciEscalation(triggerId) {
    console.log('[RACI] Saving escalation trigger', triggerId);
    var body = {
        tier_threshold: {
            '1': document.getElementById('raci-esc-t1').value,
            '2': document.getElementById('raci-esc-t2').value,
            '3': document.getElementById('raci-esc-t3').value,
        },
        response_required: document.getElementById('raci-esc-response').value,
        user: 'Dashboard User',
    };

    fetch(getBaseUrl() + '/api/v1/governance/raci/escalation-triggers/' + triggerId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[RACI] Escalation trigger', triggerId, 'saved successfully');
            raciData = data.raci;
            renderRACIDashboard();
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

