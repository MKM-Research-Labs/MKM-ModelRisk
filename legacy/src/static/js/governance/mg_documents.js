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
// Documents tab
// ================================================================
function renderDocuments() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading documents...</div>';

    var baseUrl = getBaseUrl();

    // Use page-load preloaded cache if available
    if (window._tdPreGovDocs) {
        var cached = window._tdPreGovDocs;
        window._tdPreGovDocs = null;
        _applyDocuments(cached);
        return;
    }

    fetch(baseUrl + '/api/v1/governance/documents', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) { _applyDocuments(data); })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error loading documents: ' + err + '</div>';
        });
}

function _applyDocuments(data) {
    var content = document.getElementById('mg-content');
    if (!content) return;
    // The upload form must render regardless of whether the list fetch succeeded
    // — users still need the ability to add documents. Any list-load error is
    // surfaced inline below the form rather than replacing the whole panel.
    var loadError = data.status !== 'success';
    var docs = (data.documents || []);

            var html = '<div style="padding:16px;">';

            // Upload section
            html += '<div style="margin-bottom:20px;padding:16px;border:2px dashed #ccc;border-radius:8px;background:#fafafa;">';
            html += '<div style="font-weight:600;font-size:13px;color:#333;margin-bottom:8px;">Upload Document</div>';
            html += '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">';
            html += '<input type="file" id="mg-doc-file" style="font-size:11px;">';
            html += '<input type="text" id="mg-doc-desc" placeholder="Description (optional)" style="flex:1;padding:6px 8px;font-size:11px;border:1px solid #ccc;border-radius:4px;min-width:150px;">';
            html += '<button onclick="window.MG.uploadDocument()" style="padding:6px 16px;font-size:11px;background:#1976d2;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:600;">Upload</button>';
            html += '</div></div>';

            // Inline error (if the list fetch failed) — shown below the upload form
            if (loadError) {
                html += '<div style="padding:10px 12px;margin-bottom:12px;border:1px solid #ef9a9a;background:#ffebee;color:#c62828;font-size:11px;border-radius:4px;">' +
                        'Could not load existing document list. Upload still works.' +
                        '</div>';
            }

            // Documents table
            html += '<div style="font-weight:600;font-size:13px;color:#333;margin-bottom:8px;">Uploaded Documents (' + docs.length + ')</div>';
            if (docs.length > 0) {
                html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
                html += '<thead><tr style="background:#eceff1;">';
                html += '<th style="padding:8px 10px;text-align:left;font-weight:600;">Name</th>';
                html += '<th style="padding:8px 10px;text-align:left;font-weight:600;">Description</th>';
                html += '<th style="padding:8px 10px;text-align:left;font-weight:600;">Date Added</th>';
                html += '<th style="padding:8px 10px;text-align:right;font-weight:600;">Size</th>';
                html += '<th style="padding:8px 10px;text-align:center;font-weight:600;">Actions</th>';
                html += '</tr></thead><tbody>';

                for (var i = 0; i < docs.length; i++) {
                    var d = docs[i];
                    var bg = i % 2 === 0 ? '#fff' : '#f8f9fa';
                    var sizeKb = d.size ? (d.size / 1024).toFixed(1) + ' KB' : '';
                    var dateStr = d.uploaded_at ? d.uploaded_at.substring(0, 10) : '';

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid #eee;">';
                    html += '<td style="padding:6px 10px;">' + (d.filename || '') + '</td>';
                    html += '<td style="padding:6px 10px;color:#666;">' + (d.description || '') + '</td>';
                    html += '<td style="padding:6px 10px;">' + dateStr + '</td>';
                    html += '<td style="padding:6px 10px;text-align:right;">' + sizeKb + '</td>';
                    html += '<td style="padding:6px 10px;text-align:center;">' +
                        '<a href="#" onclick="event.preventDefault();window.MG.downloadDocument(\'' + d.id + '\')" style="color:#1976d2;margin-right:8px;">Download</a>' +
                        '<a href="#" onclick="event.preventDefault();window.MG.deleteDocument(\'' + d.id + '\')" style="color:#c62828;">Delete</a>' +
                        '</td></tr>';
                }
                html += '</tbody></table>';
            } else {
                html += '<div style="padding:16px;color:#888;font-size:11px;text-align:center;">No documents uploaded yet.</div>';
            }

            html += '</div>';
            content.innerHTML = html;

    document.getElementById('mg-stats-bar').innerHTML =
        '<span>Documents: <b>' + docs.length + '</b></span>';
}

window.MG = window.MG || {};

window.MG.uploadDocument = function() {
    var fileInput = document.getElementById('mg-doc-file');
    var descInput = document.getElementById('mg-doc-desc');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        if (window.showError) window.showError('Please select a file');
        return;
    }

    var formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('description', descInput ? descInput.value : '');

    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/documents/upload', {
        method: 'POST',
        body: formData,
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (window.showSuccess) window.showSuccess('Document uploaded: ' + data.document.filename);
            renderDocuments();
        } else {
            if (window.showError) window.showError(data.message || 'Upload failed');
        }
    })
    .catch(function(err) {
        if (window.showError) window.showError('Upload failed: ' + err.message);
    });
};

window.MG.downloadDocument = function(docId) {
    var baseUrl = getBaseUrl();
    window.open(baseUrl + '/api/v1/governance/documents/' + docId + '/download', '_blank');
};

window.MG.deleteDocument = function(docId) {
    if (!confirm('Delete this document?')) return;
    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/documents/' + docId + '/delete', {
        method: 'POST',
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (window.showSuccess) window.showSuccess('Document deleted');
            renderDocuments();
        }
    })
    .catch(function(err) {
        if (window.showError) window.showError('Delete failed: ' + err.message);
    });
};
