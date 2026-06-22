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
// Participants — with Add / Edit / Delete
// ================================================================
function renderMrcParticipants(m) {
    var items = m.participants || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div style="font-size:12px;color:#666;">' + items.length + ' participant' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showParticipantForm()" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">+ Add Participant</button>';
    html += '</div>';

    html += '<div id="mrc-participant-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:#888;font-size:12px;padding:20px;text-align:center;">No participants yet. Click "+ Add Participant" to add one.</div>';
        return html;
    }

    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Name', 'Role', 'Organisation', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    items.forEach(function(p) {
        var sc = p.status === 'Attended' ? '#388e3c' : p.status === 'Invited' ? '#1976d2' : p.status === 'Apologies' ? '#f57c00' : '#888';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;">' + p.name + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (p.role || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (p.organisation || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(p.status, sc) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">';
        html += '<button onclick="window.MG.showParticipantForm(\'' + p.id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;margin-right:4px;">Edit</button>';
        html += '<button onclick="window.MG.deleteParticipant(\'' + p.id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #d32f2f;border-radius:3px;cursor:pointer;background:white;color:#d32f2f;">Del</button>';
        html += '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showParticipantForm(editId) {
    var area = document.getElementById('mrc-participant-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editId) {
        existing = (m.participants || []).find(function(p) { return p.id === editId; });
    }

    var html = '<div style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-bottom:12px;">';
    html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">' + (existing ? 'Edit Participant ' + editId : 'New Participant') + '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Name</label>';
    html += '<input type="text" id="mrc-pf-name" value="' + (existing ? existing.name : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Role</label>';
    html += '<input type="text" id="mrc-pf-role" value="' + (existing ? (existing.role || '') : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Organisation</label>';
    html += '<input type="text" id="mrc-pf-org" value="' + (existing ? (existing.organisation || '') : 'MKM Research Labs') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Status</label>';
    html += '<select id="mrc-pf-status" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;">';
    ['Invited', 'Attended', 'Apologies', 'Declined'].forEach(function(s) {
        html += '<option value="' + s + '"' + (existing && existing.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div></div>';
    html += '<div style="display:flex;gap:8px;margin-top:8px;">';
    html += '<button onclick="window.MG.saveParticipant(\'' + (editId || '') + '\')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-participant-form-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveParticipant(editId) {
    var m = window._mrcMeeting;
    var name = document.getElementById('mrc-pf-name').value.trim();
    if (!name) { alert('Name is required'); return; }
    var body = {
        name: name,
        role: document.getElementById('mrc-pf-role').value.trim(),
        organisation: document.getElementById('mrc-pf-org').value.trim(),
        status: document.getElementById('mrc-pf-status').value,
    };
    if (editId) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/participants/' + editId + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/participants', body, m.id);
    }
}

function deleteParticipant(participantId) {
    if (!confirm('Remove participant ' + participantId + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/participants/' + participantId + '/delete', {}, m.id);
}

// ================================================================
// Models in scope (read-only)
// ================================================================
function renderMrcModelsInScope(m) {
    var ids = m.models_in_scope || [];
    if (ids.length === 0) return '<div style="color:#888;font-size:12px;">No models in scope.</div>';

    var allModels = (mgData && mgData.models) ? mgData.models : [];
    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Model ID', 'Name', 'Tier', 'RAG', 'Status'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    ids.forEach(function(mid) {
        var info = allModels.find(function(x) { return x.model_id === mid; });
        html += '<tr style="cursor:pointer;" onmouseenter="this.style.background=\'#f5f5f5\'" onmouseleave="this.style.background=\'\'" onclick="window.MG.showDetail(\'' + mid + '\')">';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1976d2;">' + mid + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (info ? info.short_name : mid) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (info ? tierBadge(info.tier) : '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (info ? ragBadge(info.rag_rating) : '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (info ? reviewBadge(info.review_status) : '\u2014') + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

// ================================================================
// Decisions — with Add / Edit / Delete
// ================================================================
function renderMrcDecisions(m) {
    var items = m.decisions || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div style="font-size:12px;color:#666;">' + items.length + ' decision' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showDecisionForm()" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">+ Add Decision</button>';
    html += '</div>';

    html += '<div id="mrc-decision-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:#888;font-size:12px;padding:20px;text-align:center;">No decisions recorded yet.</div>';
        return html;
    }

    html += '<div style="display:flex;flex-direction:column;gap:8px;">';
    items.forEach(function(d) {
        html += '<div style="padding:10px 14px;border:1px solid #e0e0e0;border-radius:6px;background:#f9f9f9;border-left:3px solid #1976d2;">';
        html += '<div style="display:flex;align-items:center;justify-content:space-between;">';
        html += '<div style="display:flex;align-items:center;gap:8px;">';
        html += '<span style="font-size:10px;font-weight:700;color:#1976d2;background:#e3f2fd;padding:1px 6px;border-radius:3px;">' + d.id + '</span>';
        html += '<span style="font-size:10px;color:#888;">' + d.date + '</span>';
        html += '</div>';
        html += '<div>';
        html += '<button onclick="window.MG.showDecisionForm(\'' + d.id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;margin-right:4px;">Edit</button>';
        html += '<button onclick="window.MG.deleteDecision(\'' + d.id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #d32f2f;border-radius:3px;cursor:pointer;background:white;color:#d32f2f;">Del</button>';
        html += '</div></div>';
        html += '<div style="font-size:12px;color:#333;margin-top:6px;">' + d.description + '</div>';
        html += '</div>';
    });
    html += '</div>';
    return html;
}

function showDecisionForm(editId) {
    var area = document.getElementById('mrc-decision-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editId) {
        existing = (m.decisions || []).find(function(d) { return d.id === editId; });
    }

    var html = '<div style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-bottom:12px;">';
    html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">' + (existing ? 'Edit Decision ' + editId : 'New Decision') + '</div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Description</label>';
    html += '<textarea id="mrc-df-desc" rows="3" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;">' + (existing ? existing.description : '') + '</textarea></div>';
    html += '<div style="display:flex;gap:8px;margin-top:8px;align-items:flex-end;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Date</label>';
    html += '<input type="date" id="mrc-df-date" value="' + (existing ? existing.date : m.date) + '" style="font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;"></div>';
    html += '<button onclick="window.MG.saveDecision(\'' + (editId || '') + '\')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-decision-form-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveDecision(editId) {
    var m = window._mrcMeeting;
    var desc = document.getElementById('mrc-df-desc').value.trim();
    if (!desc) { alert('Description is required'); return; }
    var body = {
        description: desc,
        date: document.getElementById('mrc-df-date').value,
    };
    if (editId) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/decisions/' + editId + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/decisions', body, m.id);
    }
}

function deleteDecision(decisionId) {
    if (!confirm('Delete decision ' + decisionId + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/decisions/' + decisionId + '/delete', {}, m.id);
}

// ================================================================
// Actions — with Add / Edit / Delete
// ================================================================
function renderMrcActions(m) {
    var items = m.actions || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div style="font-size:12px;color:#666;">' + items.length + ' action' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showActionForm()" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">+ Add Action</button>';
    html += '</div>';

    html += '<div id="mrc-action-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:#888;font-size:12px;padding:20px;text-align:center;">No actions recorded yet.</div>';
        return html;
    }

    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Action', 'Owner', 'Target Date', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    items.forEach(function(a) {
        var sc = a.status === 'Open' ? '#f57c00' : a.status === 'Closed' ? '#388e3c' : '#1976d2';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1976d2;">' + a.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + a.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + a.owner + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + a.target_date + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(a.status, sc) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">';
        html += '<button onclick="window.MG.showActionForm(\'' + a.id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;margin-right:4px;">Edit</button>';
        html += '<button onclick="window.MG.deleteAction(\'' + a.id + '\')" style="padding:2px 8px;font-size:10px;border:1px solid #d32f2f;border-radius:3px;cursor:pointer;background:white;color:#d32f2f;">Del</button>';
        html += '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showActionForm(editId) {
    var area = document.getElementById('mrc-action-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editId) {
        existing = (m.actions || []).find(function(a) { return a.id === editId; });
    }

    var html = '<div style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-bottom:12px;">';
    html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">' + (existing ? 'Edit Action ' + editId : 'New Action') + '</div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Description</label>';
    html += '<textarea id="mrc-actf-desc" rows="2" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;">' + (existing ? existing.description : '') + '</textarea></div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Owner</label>';
    html += '<input type="text" id="mrc-actf-owner" value="' + (existing ? existing.owner : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Target Date</label>';
    html += '<input type="date" id="mrc-actf-date" value="' + (existing ? existing.target_date : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Status</label>';
    html += '<select id="mrc-actf-status" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;">';
    ['Open', 'In Progress', 'Closed'].forEach(function(s) {
        html += '<option value="' + s + '"' + (existing && existing.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div></div>';
    html += '<div style="display:flex;gap:8px;margin-top:8px;">';
    html += '<button onclick="window.MG.saveAction(\'' + (editId || '') + '\')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-action-form-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveAction(editId) {
    var m = window._mrcMeeting;
    var desc = document.getElementById('mrc-actf-desc').value.trim();
    if (!desc) { alert('Description is required'); return; }
    var body = {
        description: desc,
        owner: document.getElementById('mrc-actf-owner').value.trim(),
        target_date: document.getElementById('mrc-actf-date').value,
        status: document.getElementById('mrc-actf-status').value,
    };
    if (editId) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/actions/' + editId + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/actions', body, m.id);
    }
}

function deleteAction(actionId) {
    if (!confirm('Delete action ' + actionId + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/actions/' + actionId + '/delete', {}, m.id);
}

