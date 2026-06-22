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
// Audit trail (global view)
// ================================================================
function renderAuditTrail() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading audit trail...</div>';

    console.log('[AuditTrail] Fetching audit entries');
    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/audit-trail?limit=200', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error loading audit trail</div>';
                return;
            }
            console.log('[AuditTrail] Loaded', data.returned, 'of', data.total_entries, 'entries');

            if (data.entries.length === 0) {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">' +
                    '<div style="font-size:14px;font-weight:600;margin-bottom:8px;">No Audit Entries Yet</div>' +
                    '<div style="font-size:12px;">Model usage events will appear here as models are invoked through the platform.</div>' +
                    '</div>';
                return;
            }

            var html = '<div style="padding:12px 16px;border-bottom:1px solid #eee;background:#f5f5f5;">';
            html += '<span style="font-size:11px;color:#666;">Showing <b>' + data.returned + '</b> of <b>' + data.total_entries + '</b> entries</span>';
            html += '</div>';

            html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
            html += '<thead><tr style="background:#fafafa;">';
            ['Timestamp', 'Model', 'Event', 'User', 'Action', 'Source'].forEach(function(h) {
                html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;position:sticky;top:0;background:#fafafa;">' + h + '</th>';
            });
            html += '</tr></thead><tbody>';

            data.entries.forEach(function(e) {
                html += '<tr>';
                html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;font-size:10px;">' + e.timestamp + '</td>';
                html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1976d2;cursor:pointer;" onclick="window.MG.showDetail(\'' + e.model_id + '\')">' + e.model_id + '</td>';
                html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">' + badge(e.event_type, '#1976d2') + '</td>';
                html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">' + e.user + '</td>';
                html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">' + e.action + '</td>';
                html += '<td style="padding:5px 10px;border-bottom:1px solid #f0f0f0;">' + e.source + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';

            content.innerHTML = html;

            document.getElementById('mg-stats-bar').innerHTML =
                '<span>Total audit entries: <b>' + data.total_entries + '</b></span>' +
                '<span>Showing: <b>' + data.returned + '</b></span>';
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load audit trail</div>';
            console.error('Audit trail error:', err);
        });
}

// ================================================================
// Show / Hide

