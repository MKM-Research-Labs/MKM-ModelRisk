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
// Agenda — with Add / Edit / Delete
// ================================================================
function renderMrcAgenda(m) {
    var items = m.agenda || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div style="font-size:12px;color:#666;">' + items.length + ' agenda item' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showAgendaForm()" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">+ Add Item</button>';
    html += '</div>';

    html += '<div id="mrc-agenda-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:#888;font-size:12px;padding:20px;text-align:center;">No agenda items yet. Click "+ Add Item" to create one.</div>';
        return html;
    }

    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['#', 'Title', 'Presenter', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    items.forEach(function(item) {
        var sc = item.status === 'Completed' ? '#388e3c' : item.status === 'Pending' ? '#f57c00' : '#1976d2';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;width:30px;">' + item.item + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">';
        html += '<div style="font-weight:600;color:#333;">' + item.title + '</div>';
        if (item.description) html += '<div style="font-size:10px;color:#888;margin-top:2px;">' + item.description + '</div>';
        html += '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (item.presenter || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(item.status, sc) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">';
        html += '<button onclick="window.MG.showAgendaForm(' + item.item + ')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;margin-right:4px;">Edit</button>';
        html += '<button onclick="window.MG.deleteAgendaItem(' + item.item + ')" style="padding:2px 8px;font-size:10px;border:1px solid #d32f2f;border-radius:3px;cursor:pointer;background:white;color:#d32f2f;">Del</button>';
        html += '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showAgendaForm(editItemNum) {
    var area = document.getElementById('mrc-agenda-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editItemNum) {
        existing = (m.agenda || []).find(function(a) { return a.item === editItemNum; });
    }

    var html = '<div style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-bottom:12px;">';
    html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">' + (existing ? 'Edit Agenda Item #' + editItemNum : 'New Agenda Item') + '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Title</label>';
    html += '<input type="text" id="mrc-af-title" value="' + (existing ? existing.title : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Presenter</label>';
    html += '<input type="text" id="mrc-af-presenter" value="' + (existing ? (existing.presenter || '') : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '</div>';
    html += '<div style="margin-top:8px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Description</label>';
    html += '<input type="text" id="mrc-af-desc" value="' + (existing ? (existing.description || '') : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div style="display:flex;gap:8px;margin-top:8px;align-items:flex-end;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Duration</label>';
    html += '<input type="text" id="mrc-af-duration" value="' + (existing ? (existing.duration || '') : '') + '" placeholder="e.g. 15 min" style="width:100px;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Status</label>';
    html += '<select id="mrc-af-status" style="font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;">';
    ['Pending', 'In Progress', 'Completed'].forEach(function(s) {
        html += '<option value="' + s + '"' + (existing && existing.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div>';
    html += '<button onclick="window.MG.saveAgendaItem(' + (editItemNum || 0) + ')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-agenda-form-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveAgendaItem(editItemNum) {
    var m = window._mrcMeeting;
    var title = document.getElementById('mrc-af-title').value.trim();
    if (!title) { alert('Title is required'); return; }
    var body = {
        title: title,
        presenter: document.getElementById('mrc-af-presenter').value.trim(),
        description: document.getElementById('mrc-af-desc').value.trim(),
        duration: document.getElementById('mrc-af-duration').value.trim(),
        status: document.getElementById('mrc-af-status').value,
    };
    if (editItemNum) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/agenda/' + editItemNum + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/agenda', body, m.id);
    }
}

function deleteAgendaItem(itemNum) {
    if (!confirm('Delete agenda item #' + itemNum + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/agenda/' + itemNum + '/delete', {}, m.id);
}

// ================================================================
// Minutes — structured item list with Add / Edit / Delete
// ================================================================
function renderMrcMinutes(m) {
    var minutes = m.minutes;

    // Legacy string format: show as read-only markdown
    if (typeof minutes === 'string') {
        return renderMrcMinutesLegacy(minutes);
    }

    var items = minutes || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div style="font-size:12px;color:#666;">' + items.length + ' minute' + (items.length !== 1 ? 's' : '') + ' item' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showMinuteForm()" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">+ Add Item</button>';
    html += '</div>';

    html += '<div id="mrc-minute-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:#888;font-size:12px;padding:20px;text-align:center;">No minutes items yet. Click "+ Add Item" to create one.</div>';
        return html;
    }

    html += '<div style="display:flex;flex-direction:column;gap:8px;">';
    items.forEach(function(item) {
        html += '<div style="padding:10px 14px;border:1px solid #e0e0e0;border-radius:6px;background:#f9f9f9;border-left:3px solid #1976d2;">';
        html += '<div style="display:flex;align-items:center;justify-content:space-between;">';
        html += '<div style="display:flex;align-items:center;gap:8px;">';
        html += '<span style="font-size:10px;font-weight:700;color:#1976d2;background:#e3f2fd;padding:1px 6px;border-radius:3px;">#' + item.item + '</span>';
        html += '<span style="font-size:12px;font-weight:600;color:#333;">' + item.title + '</span>';
        if (item.presenter) html += '<span style="font-size:10px;color:#888;">(' + item.presenter + ')</span>';
        html += '</div>';
        html += '<div>';
        html += '<button onclick="window.MG.showMinuteForm(' + item.item + ')" style="padding:2px 8px;font-size:10px;border:1px solid #1976d2;border-radius:3px;cursor:pointer;background:white;color:#1976d2;margin-right:4px;">Edit</button>';
        html += '<button onclick="window.MG.deleteMinuteItem(' + item.item + ')" style="padding:2px 8px;font-size:10px;border:1px solid #d32f2f;border-radius:3px;cursor:pointer;background:white;color:#d32f2f;">Del</button>';
        html += '</div></div>';
        if (item.text) {
            html += '<div style="font-size:11px;color:#555;margin-top:6px;line-height:1.6;white-space:pre-wrap;">' + item.text + '</div>';
        }
        html += '</div>';
    });
    html += '</div>';
    return html;
}

function renderMrcMinutesLegacy(text) {
    // Read-only rendering of legacy markdown minutes
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">';
    html += '<div style="font-size:12px;color:#666;">Meeting Minutes (legacy format)</div>';
    html += '</div>';

    if (!text) {
        html += '<div style="color:#888;font-size:12px;padding:20px;text-align:center;">No minutes recorded.</div>';
        return html;
    }

    var lines = text.split('\n');
    html += '<div style="font-size:12px;line-height:1.7;color:#333;">';
    var inList = false;
    lines.forEach(function(line) {
        if (line.match(/^### /)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h4 style="font-size:12px;font-weight:700;color:#1565c0;margin:16px 0 6px 0;border-bottom:1px solid #e0e0e0;padding-bottom:4px;">' + line.replace(/^### /, '') + '</h4>';
        } else if (line.match(/^## /)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h3 style="font-size:13px;font-weight:700;color:#333;margin:20px 0 8px 0;">' + line.replace(/^## /, '') + '</h3>';
        } else if (line.match(/^\*\*.*\*\*$/)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<div style="font-weight:600;margin-top:8px;">' + line.replace(/\*\*/g, '') + '</div>';
        } else if (line.match(/^- /)) {
            if (!inList) { html += '<ul style="margin:4px 0;padding-left:20px;">'; inList = true; }
            html += '<li>' + line.replace(/^- /, '').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') + '</li>';
        } else if (line.match(/^\d+\. /)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<div style="margin:2px 0;padding-left:8px;">' + line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') + '</div>';
        } else if (line.trim() === '') {
            if (inList) { html += '</ul>'; inList = false; }
        } else {
            html += '<div>' + line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') + '</div>';
        }
    });
    if (inList) html += '</ul>';
    html += '</div>';
    return html;
}

function showMinuteForm(editItemNum) {
    var area = document.getElementById('mrc-minute-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editItemNum) {
        var items = Array.isArray(m.minutes) ? m.minutes : [];
        existing = items.find(function(mi) { return mi.item === editItemNum; });
    }

    var html = '<div style="padding:12px;border:1px solid #e0e0e0;border-radius:6px;background:#f8fafc;margin-bottom:12px;">';
    html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">' + (existing ? 'Edit Minutes Item #' + editItemNum : 'New Minutes Item') + '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Title</label>';
    html += '<input type="text" id="mrc-mf-title" value="' + (existing ? existing.title : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Presenter</label>';
    html += '<input type="text" id="mrc-mf-presenter" value="' + (existing ? (existing.presenter || '') : '') + '" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    html += '</div>';
    html += '<div style="margin-top:8px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Minutes Text</label>';
    html += '<textarea id="mrc-mf-text" rows="6" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;line-height:1.5;">' + (existing ? (existing.text || '') : '') + '</textarea></div>';
    html += '<div style="display:flex;gap:8px;margin-top:8px;">';
    html += '<button onclick="window.MG.saveMinuteItem(' + (editItemNum || 0) + ')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-minute-form-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveMinuteItem(editItemNum) {
    var m = window._mrcMeeting;
    var title = document.getElementById('mrc-mf-title').value.trim();
    if (!title) { alert('Title is required'); return; }
    var body = {
        title: title,
        presenter: document.getElementById('mrc-mf-presenter').value.trim(),
        text: document.getElementById('mrc-mf-text').value,
    };
    if (editItemNum) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/minutes-items/' + editItemNum + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/minutes-items', body, m.id);
    }
}

function deleteMinuteItem(itemNum) {
    if (!confirm('Delete minutes item #' + itemNum + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/minutes-items/' + itemNum + '/delete', {}, m.id);
}

