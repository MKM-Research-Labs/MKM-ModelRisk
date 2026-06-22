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
// Documents (with upload)
// ================================================================
function renderMrcDocuments(m) {
    var mc = document.getElementById('mrc-meeting-content');
    var docs = m.documents || [];

    var html = '<div>';

    // Upload form
    html += '<div style="margin-bottom:16px;padding:12px;border:1px dashed #ccc;border-radius:6px;background:#fafafa;">';
    html += '<div style="font-size:11px;font-weight:600;color:#333;margin-bottom:8px;">Upload Supporting Document</div>';
    html += '<form id="mrc-upload-form" style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">File</label>';
    html += '<input type="file" id="mrc-upload-file" style="font-size:10px;"></div>';
    html += '<div style="flex:1;min-width:150px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Description</label>';
    html += '<input type="text" id="mrc-upload-desc" placeholder="Brief description" style="width:100%;font-size:11px;padding:4px 8px;border:1px solid #ddd;border-radius:3px;"></div>';
    html += '<button type="button" onclick="window.MG.uploadMeetingDoc(\'' + m.id + '\')" style="padding:6px 14px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;white-space:nowrap;">Upload</button>';
    html += '</form>';
    html += '<div id="mrc-upload-status" style="margin-top:4px;font-size:10px;"></div>';
    html += '</div>';

    // Document list
    if (docs.length === 0) {
        html += '<div style="color:#888;font-size:12px;">No documents uploaded yet.</div>';
    } else {
        html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
        html += '<thead><tr style="background:#fafafa;">';
        ['Filename', 'Description', 'Uploaded By', 'Date', ''].forEach(function(h) {
            html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';

        docs.forEach(function(d) {
            var dlUrl = getBaseUrl() + '/api/v1/governance/mrc/meetings/' + m.id + '/documents/' + encodeURIComponent(d.filename);
            html += '<tr>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:500;">' + d.filename + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (d.description || '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + (d.uploaded_by || '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (d.uploaded_at ? d.uploaded_at.substring(0, 10) : '\u2014') + '</td>';
            html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;"><a href="' + dlUrl + '" target="_blank" style="color:#1976d2;text-decoration:none;font-size:10px;">Download</a></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
    }
    html += '</div>';
    mc.innerHTML = html;
}

function uploadMeetingDoc(meetingId) {
    var fileInput = document.getElementById('mrc-upload-file');
    var descInput = document.getElementById('mrc-upload-desc');
    var statusEl = document.getElementById('mrc-upload-status');

    if (!fileInput.files || fileInput.files.length === 0) {
        statusEl.innerHTML = '<span style="color:red;">Please select a file.</span>';
        return;
    }

    var formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('description', descInput.value);
    formData.append('user', 'David K Kelly');

    statusEl.innerHTML = '<span style="color:#1976d2;">Uploading...</span>';

    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId + '/documents', {
        method: 'POST',
        body: formData,
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            statusEl.innerHTML = '<span style="color:#388e3c;">Uploaded successfully.</span>';
            showMrcMeeting(meetingId);
        } else {
            statusEl.innerHTML = '<span style="color:red;">' + (data.message || 'Upload failed') + '</span>';
        }
    })
    .catch(function(err) {
        statusEl.innerHTML = '<span style="color:red;">Error: ' + err.message + '</span>';
    });
}

// ── New meeting form ──
function showNewMeetingForm() {
    var sc = document.getElementById('mrc-sub-content');

    var html = '<div style="padding:16px;">';
    html += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">';
    html += '<button onclick="window.MG.switchMrcTab(\'meetings\')" style="padding:4px 10px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#e3f2fd;color:#1976d2;font-weight:500;">&larr; Back</button>';
    html += '<div style="font-size:14px;font-weight:700;color:#333;">Create New MRC Meeting</div>';
    html += '</div>';

    var fields = [
        {id: 'title', label: 'Meeting Title', type: 'text', value: 'MRC Meeting'},
        {id: 'date', label: 'Date', type: 'date', value: new Date().toISOString().substring(0, 10)},
        {id: 'time', label: 'Time', type: 'time', value: '10:00'},
        {id: 'location', label: 'Location', type: 'text', value: 'Virtual (Teams)'},
    ];

    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">';
    fields.forEach(function(f) {
        html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">' + f.label + '</label>';
        html += '<input type="' + f.type + '" id="mrc-new-' + f.id + '" value="' + f.value + '" style="width:100%;font-size:11px;padding:6px 8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;"></div>';
    });
    html += '</div>';

    // Models in scope (checkboxes)
    html += '<div style="margin-bottom:16px;">';
    html += '<label style="font-size:10px;color:#666;display:block;margin-bottom:6px;">Models in Scope</label>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:6px;">';
    if (mgData && mgData.models) {
        mgData.models.forEach(function(mod) {
            html += '<label style="display:flex;align-items:center;gap:4px;font-size:11px;padding:4px 8px;border:1px solid #ddd;border-radius:4px;cursor:pointer;background:#fafafa;">';
            html += '<input type="checkbox" class="mrc-model-cb" value="' + mod.model_id + '" checked> ' + mod.model_id + ' ' + mod.short_name;
            html += '</label>';
        });
    }
    html += '</div></div>';

    // Supporting documents
    html += '<div style="margin-bottom:16px;">';
    html += '<label style="font-size:10px;color:#666;display:block;margin-bottom:6px;">Supporting Documents</label>';
    html += '<div id="mrc-new-docs-list" style="margin-bottom:8px;"></div>';
    html += '<div style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap;padding:10px;border:1px dashed #ccc;border-radius:6px;background:#fafafa;">';
    html += '<div><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">File</label>';
    html += '<input type="file" id="mrc-new-doc-file" style="font-size:10px;"></div>';
    html += '<div style="flex:1;min-width:150px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:2px;">Description</label>';
    html += '<input type="text" id="mrc-new-doc-desc" placeholder="Brief description" style="width:100%;font-size:11px;padding:4px 8px;border:1px solid #ddd;border-radius:3px;box-sizing:border-box;"></div>';
    html += '<button type="button" onclick="window.MG.addNewMeetingDoc()" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:white;color:#1976d2;font-weight:500;white-space:nowrap;">+ Add File</button>';
    html += '</div>';
    html += '</div>';

    html += '<div id="mrc-create-status" style="margin-bottom:8px;font-size:10px;"></div>';
    html += '<button onclick="window.MG.createMeeting()" style="padding:8px 20px;font-size:12px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:600;">Create Meeting</button>';

    html += '</div>';
    sc.innerHTML = html;
    window._mrcPendingDocs = [];
}

function addNewMeetingDoc() {
    var fileInput = document.getElementById('mrc-new-doc-file');
    var descInput = document.getElementById('mrc-new-doc-desc');
    if (!fileInput.files || fileInput.files.length === 0) return;

    var file = fileInput.files[0];
    window._mrcPendingDocs = window._mrcPendingDocs || [];
    window._mrcPendingDocs.push({file: file, description: descInput.value});

    // Update the visual list
    var listEl = document.getElementById('mrc-new-docs-list');
    var html = '';
    window._mrcPendingDocs.forEach(function(d, i) {
        html += '<div style="display:flex;align-items:center;gap:8px;padding:4px 8px;margin-bottom:4px;border:1px solid #e0e0e0;border-radius:4px;background:white;font-size:11px;">';
        html += '<span style="flex:1;font-weight:500;">' + d.file.name + '</span>';
        if (d.description) html += '<span style="color:#888;">' + d.description + '</span>';
        html += '<span style="color:#888;font-size:10px;">(' + (d.file.size / 1024).toFixed(0) + ' KB)</span>';
        html += '<button onclick="window.MG.removeNewMeetingDoc(' + i + ')" style="border:none;background:none;color:#d32f2f;cursor:pointer;font-size:14px;padding:0 4px;" title="Remove">&times;</button>';
        html += '</div>';
    });
    listEl.innerHTML = html;

    // Reset inputs
    fileInput.value = '';
    descInput.value = '';
}

function removeNewMeetingDoc(index) {
    window._mrcPendingDocs.splice(index, 1);
    var listEl = document.getElementById('mrc-new-docs-list');
    var html = '';
    window._mrcPendingDocs.forEach(function(d, i) {
        html += '<div style="display:flex;align-items:center;gap:8px;padding:4px 8px;margin-bottom:4px;border:1px solid #e0e0e0;border-radius:4px;background:white;font-size:11px;">';
        html += '<span style="flex:1;font-weight:500;">' + d.file.name + '</span>';
        if (d.description) html += '<span style="color:#888;">' + d.description + '</span>';
        html += '<span style="color:#888;font-size:10px;">(' + (d.file.size / 1024).toFixed(0) + ' KB)</span>';
        html += '<button onclick="window.MG.removeNewMeetingDoc(' + i + ')" style="border:none;background:none;color:#d32f2f;cursor:pointer;font-size:14px;padding:0 4px;" title="Remove">&times;</button>';
        html += '</div>';
    });
    listEl.innerHTML = html;
}

function uploadPendingDocs(meetingId) {
    var docs = window._mrcPendingDocs || [];
    if (docs.length === 0) {
        showMrcMeeting(meetingId);
        return;
    }
    var statusEl = document.getElementById('mrc-create-status');
    var uploaded = 0;
    var total = docs.length;
    statusEl.innerHTML = '<span style="color:#1976d2;">Uploading documents (' + uploaded + '/' + total + ')...</span>';

    function uploadNext() {
        if (uploaded >= total) {
            window._mrcPendingDocs = [];
            showMrcMeeting(meetingId);
            return;
        }
        var d = docs[uploaded];
        var formData = new FormData();
        formData.append('file', d.file);
        formData.append('description', d.description || '');
        formData.append('user', 'David K Kelly');

        fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId + '/documents', {
            method: 'POST',
            body: formData,
        })
        .then(function(r) { return r.json(); })
        .then(function() {
            uploaded++;
            if (statusEl) statusEl.innerHTML = '<span style="color:#1976d2;">Uploading documents (' + uploaded + '/' + total + ')...</span>';
            uploadNext();
        })
        .catch(function() {
            uploaded++;
            uploadNext();
        });
    }
    uploadNext();
}

function createMeeting() {
    var title = document.getElementById('mrc-new-title').value;
    var date = document.getElementById('mrc-new-date').value;
    var time = document.getElementById('mrc-new-time').value;
    var location = document.getElementById('mrc-new-location').value;
    var statusEl = document.getElementById('mrc-create-status');

    var modelCbs = document.querySelectorAll('.mrc-model-cb:checked');
    var models = [];
    modelCbs.forEach(function(cb) { models.push(cb.value); });

    if (!title || !date) {
        statusEl.innerHTML = '<span style="color:red;">Title and date are required.</span>';
        return;
    }

    var hasDocs = window._mrcPendingDocs && window._mrcPendingDocs.length > 0;
    statusEl.innerHTML = '<span style="color:#1976d2;">Creating meeting...</span>';

    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            title: title,
            date: date,
            time: time,
            location: location,
            status: 'Scheduled',
            models_in_scope: models,
        }),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (hasDocs) {
                uploadPendingDocs(data.meeting.id);
            } else {
                showMrcMeeting(data.meeting.id);
            }
        } else {
            statusEl.innerHTML = '<span style="color:red;">' + (data.message || 'Failed') + '</span>';
        }
    })
    .catch(function(err) {
        statusEl.innerHTML = '<span style="color:red;">Error: ' + err.message + '</span>';
    });
}

