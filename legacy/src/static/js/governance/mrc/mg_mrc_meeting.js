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
var mrcMeetingTab = 'agenda';

function showMrcMeeting(meetingId) {
    var sc = document.getElementById('mrc-sub-content');
    sc.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading meeting...</div>';

    console.log('[MRC] Loading meeting:', meetingId);
    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId, {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                sc.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Meeting not found</div>';
                return;
            }
            console.log('[MRC] Meeting loaded:', data.meeting.title, '(' + data.meeting.status + ')');
            window._mrcMeeting = data.meeting;
            mrcMeetingTab = 'agenda';
            renderMrcMeetingDetail(data.meeting);
        })
        .catch(function(err) {
            console.error('[MRC] Meeting load error:', err);
            sc.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + err.message + '</div>';
        });
}

function renderMrcMeetingDetail(m) {
    var sc = document.getElementById('mrc-sub-content');

    var html = '<div style="padding:0;">';

    // Header
    html += '<div style="padding:12px 16px;border-bottom:1px solid #eee;">';
    html += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">';
    html += '<button onclick="window.MG.switchMrcTab(\'meetings\')" style="padding:4px 10px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#e3f2fd;color:#1976d2;font-weight:500;">&larr; Back</button>';
    html += '<div style="font-size:14px;font-weight:700;color:#333;">' + m.title + '</div>';
    var statusColor = m.status === 'Completed' ? '#388e3c' : m.status === 'Scheduled' ? '#1976d2' : '#f57c00';
    html += badge(m.status, statusColor);
    html += '<div style="flex:1;"></div>';
    html += '<button onclick="window.MG.downloadMeetingPdf(\'' + m.id + '\')" style="padding:5px 12px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#e3f2fd;color:#1976d2;font-weight:500;">&#x2913; Meeting Pack PDF</button>';
    html += '</div>';

    // Meeting info row
    html += '<div style="display:flex;gap:20px;font-size:11px;color:#666;flex-wrap:wrap;">';
    html += '<span>Date: <b>' + m.date + '</b></span>';
    html += '<span>Time: <b>' + (m.time || '\u2014') + '</b></span>';
    html += '<span>Location: <b>' + (m.location || '\u2014') + '</b></span>';
    html += '<span>Chair: <b>' + m.chair + '</b></span>';
    html += '</div>';
    html += '</div>';

    // Meeting sub-tabs
    html += '<div style="display:flex;border-bottom:1px solid #eee;background:#fafafa;">';
    var pCount = (m.participants || []).length;
    var minCount = Array.isArray(m.minutes) ? m.minutes.length : 0;
    var mTabs = [
        {id: 'agenda', label: 'Agenda (' + (m.agenda || []).length + ')'},
        {id: 'minutes', label: 'Minutes (' + minCount + ')'},
        {id: 'participants', label: 'Participants (' + pCount + ')'},
        {id: 'models', label: 'Models (' + (m.models_in_scope || []).length + ')'},
        {id: 'decisions', label: 'Decisions (' + (m.decisions || []).length + ')'},
        {id: 'actions', label: 'Actions (' + (m.actions || []).length + ')'},
        {id: 'mdocs', label: 'Documents (' + (m.documents || []).length + ')'},
    ];
    mTabs.forEach(function(t) {
        html += '<button id="mrc-mtab-' + t.id + '" onclick="window.MG.switchMeetingTab(\'' + t.id + '\')" style="padding:8px 14px;font-size:11px;border:none;cursor:pointer;border-bottom:2px solid ' + (t.id === mrcMeetingTab ? '#1976d2' : 'transparent') + ';background:transparent;color:' + (t.id === mrcMeetingTab ? '#1976d2' : '#666') + ';font-weight:' + (t.id === mrcMeetingTab ? '600' : '400') + ';">' + t.label + '</button>';
    });
    html += '</div>';

    html += '<div id="mrc-meeting-content" style="padding:16px;overflow-y:auto;"></div>';
    html += '</div>';

    sc.innerHTML = html;
    renderMeetingTabContent(mrcMeetingTab, m);
}

function switchMeetingTab(tabId) {
    mrcMeetingTab = tabId;
    ['agenda', 'minutes', 'participants', 'models', 'decisions', 'actions', 'mdocs'].forEach(function(t) {
        var btn = document.getElementById('mrc-mtab-' + t);
        if (btn) {
            btn.style.borderBottomColor = t === tabId ? '#1976d2' : 'transparent';
            btn.style.color = t === tabId ? '#1976d2' : '#666';
            btn.style.fontWeight = t === tabId ? '600' : '400';
        }
    });
    renderMeetingTabContent(tabId, window._mrcMeeting);
}

function renderMeetingTabContent(tabId, m) {
    var mc = document.getElementById('mrc-meeting-content');
    if (tabId === 'agenda') mc.innerHTML = renderMrcAgenda(m);
    else if (tabId === 'minutes') mc.innerHTML = renderMrcMinutes(m);
    else if (tabId === 'participants') mc.innerHTML = renderMrcParticipants(m);
    else if (tabId === 'models') mc.innerHTML = renderMrcModelsInScope(m);
    else if (tabId === 'decisions') mc.innerHTML = renderMrcDecisions(m);
    else if (tabId === 'actions') mc.innerHTML = renderMrcActions(m);
    else if (tabId === 'mdocs') renderMrcDocuments(m);
}

function downloadMeetingPdf(meetingId) {
    window.open(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId + '/pdf', '_blank');
}

// ================================================================
// CRUD helper — POST JSON, refresh meeting on success
// ================================================================
function mrcCrudPost(url, body, meetingId) {
    fetch(getBaseUrl() + url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mrcMeeting = data.meeting;
            renderMrcMeetingDetail(data.meeting);
            // Restore the current tab
            switchMeetingTab(mrcMeetingTab);
        } else {
            alert(data.message || 'Operation failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

// ================================================================
// Sub-module code
// ================================================================
