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

// Parameter inventory
// ================================================================
function renderParameterInventory() {
    var content = document.getElementById('mg-content');
    var pdfUrl = getBaseUrl() + '/api/v1/governance/parameter-inventory/pdf';

    var html = '<div style="padding:16px;">';
    html += '<div style="font-size:13px;font-weight:700;color:#333;margin-bottom:8px;">Model Parameter Inventory</div>';
    html += '<div style="font-size:11px;color:#666;margin-bottom:16px;">Complete inventory of all hard-coded input parameters across the analytical model codebase. Maintained for model governance and MRC review.</div>';

    // Action bar
    html += '<div style="display:flex;gap:10px;margin-bottom:16px;">';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:12px;font-weight:500;">&#x2913; Download PDF</a>';
    html += '</div>';

    // Embedded PDF viewer
    html += '<div id="mg-params-pdf-container" style="border:1px solid #e0e0e0;border-radius:6px;overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="600" style="border:none;">';
    html += '<div style="padding:40px;text-align:center;">';
    html += '<div style="font-size:32px;margin-bottom:12px;">&#x1F4CB;</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">Parameter Inventory PDF</div>';
    html += '<div style="font-size:11px;color:#888;margin-bottom:16px;">Your browser cannot display the PDF inline.</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-block;padding:8px 20px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:12px;">Open PDF</a>';
    html += '</div>';
    html += '</object>';
    html += '</div>';

    html += '</div>';
    content.innerHTML = html;

    // Check if PDF exists
    fetch(pdfUrl, {method: 'HEAD'}).then(function(resp) {
        if (!resp.ok) {
            var container = document.getElementById('mg-params-pdf-container');
            if (container) {
                container.innerHTML = '<div style="padding:40px;text-align:center;">' +
                    '<div style="font-size:32px;margin-bottom:12px;">&#x26A0;</div>' +
                    '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">No Parameter Inventory Available</div>' +
                    '<div style="font-size:11px;color:#888;">Run: <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;">python app.py check params --pdf</code></div>' +
                    '</div>';
            }
        }
    });
}


// ================================================================
// MRC — Main view with sub-tabs
// ================================================================
var mrcSubTab = 'meetings';

function renderMRC() {
    console.log('[MRC] Rendering MRC view');
    var content = document.getElementById('mg-content');

    var html = '<div style="padding:0;">';

    // Members summary bar
    html += '<div style="display:flex;gap:10px;padding:12px 16px;border-bottom:1px solid #eee;flex-wrap:wrap;">';
    html += '<div style="flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid #1976d2;">';
    html += '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">Chair</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;">Johnny Mattimore</div></div>';
    html += '<div style="flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid #388e3c;">';
    html += '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">Model Owner</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;">David K Kelly</div></div>';
    html += '<div style="flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid #f57c00;">';
    html += '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">Frequency</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;">Quarterly</div></div>';
    html += '</div>';

    // Sub-tabs
    html += '<div style="display:flex;border-bottom:1px solid #eee;background:#fafafa;">';
    var subTabs = [
        {id: 'meetings', label: 'Meetings'},
        {id: 'tor', label: 'Terms of Reference'},
    ];
    subTabs.forEach(function(t) {
        html += '<button id="mrc-stab-' + t.id + '" onclick="window.MG.switchMrcTab(\'' + t.id + '\')" style="padding:8px 14px;font-size:11px;border:none;cursor:pointer;border-bottom:2px solid ' + (t.id === mrcSubTab ? '#1976d2' : 'transparent') + ';background:transparent;color:' + (t.id === mrcSubTab ? '#1976d2' : '#666') + ';font-weight:' + (t.id === mrcSubTab ? '600' : '400') + ';">' + t.label + '</button>';
    });
    html += '</div>';

    html += '<div id="mrc-sub-content" style="padding:0;"></div>';
    html += '</div>';

    content.innerHTML = html;

    // Render active sub-tab
    if (mrcSubTab === 'meetings') renderMrcMeetingsList();
    else if (mrcSubTab === 'tor') renderMrcToR();
}

function switchMrcSubTab(tabId) {
    mrcSubTab = tabId;
    ['meetings', 'tor'].forEach(function(t) {
        var btn = document.getElementById('mrc-stab-' + t);
        if (btn) {
            btn.style.borderBottomColor = t === tabId ? '#1976d2' : 'transparent';
            btn.style.color = t === tabId ? '#1976d2' : '#666';
            btn.style.fontWeight = t === tabId ? '600' : '400';
        }
    });
    if (tabId === 'meetings') renderMrcMeetingsList();
    else if (tabId === 'tor') renderMrcToR();
}

function renderMrcToR() {
    var sc = document.getElementById('mrc-sub-content');
    var pdfUrl = getBaseUrl() + '/api/v1/governance/mrc/terms-of-reference/pdf';

    var html = '<div style="padding:16px;">';
    html += '<div style="display:flex;gap:10px;margin-bottom:16px;">';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:12px;font-weight:500;">&#x2913; Download Terms of Reference</a>';
    html += '</div>';
    html += '<div id="mrc-tor-pdf-container" style="border:1px solid #e0e0e0;border-radius:6px;overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="550" style="border:none;">';
    html += '<div style="padding:40px;text-align:center;"><a href="' + pdfUrl + '" target="_blank" style="padding:8px 20px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:12px;">Open PDF</a></div>';
    html += '</object></div></div>';
    sc.innerHTML = html;

    fetch(pdfUrl, {method: 'HEAD'}).then(function(resp) {
        if (!resp.ok) {
            var c = document.getElementById('mrc-tor-pdf-container');
            if (c) c.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">ToR PDF not generated. Run: <code>python -m docs.models.mrc_tor.generator --pdf</code></div>';
        }
    });
}

// ================================================================
// MRC Meetings list
// ================================================================
function renderMrcMeetingsList() {
    var sc = document.getElementById('mrc-sub-content');
    sc.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading meetings...</div>';

    console.log('[MRC] Fetching meetings list');
    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                sc.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load meetings</div>';
                return;
            }
            var meetings = data.meetings;
            console.log('[MRC] Loaded', meetings.length, 'meetings');
            var html = '<div style="padding:16px;">';

            // Action bar
            html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">';
            html += '<div style="font-size:12px;color:#666;">' + meetings.length + ' meeting' + (meetings.length !== 1 ? 's' : '') + '</div>';
            html += '<button onclick="window.MG.showNewMeetingForm()" style="padding:6px 14px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:500;">+ New Meeting</button>';
            html += '</div>';

            if (meetings.length === 0) {
                html += '<div style="padding:40px;text-align:center;color:#888;font-size:12px;">No meetings recorded yet.</div>';
            } else {
                html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
                html += '<thead><tr style="background:#fafafa;">';
                ['Date', 'Title', 'Status', 'Chair', 'Models', 'Agenda', 'Minutes', 'Docs'].forEach(function(h) {
                    html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
                });
                html += '</tr></thead><tbody>';

                meetings.forEach(function(m) {
                    var statusColor = m.status === 'Completed' ? '#388e3c' : m.status === 'Scheduled' ? '#1976d2' : '#f57c00';
                    html += '<tr style="cursor:pointer;" onmouseenter="this.style.background=\'#f5f5f5\'" onmouseleave="this.style.background=\'\'" onclick="window.MG.showMeeting(\'' + m.id + '\')">';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + m.date + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;color:#1976d2;font-weight:500;">' + m.title + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(m.status, statusColor) + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + m.chair + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + m.models_in_scope + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + m.agenda_items + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + (m.has_minutes ? '<span style="color:#388e3c;">&#x2713;</span>' : '<span style="color:#ccc;">—</span>') + '</td>';
                    html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;text-align:center;">' + m.documents + '</td>';
                    html += '</tr>';
                });

                html += '</tbody></table>';
            }

            html += '</div>';
            sc.innerHTML = html;
        })
        .catch(function(err) {
            sc.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + err.message + '</div>';
        });
}

// ================================================================

