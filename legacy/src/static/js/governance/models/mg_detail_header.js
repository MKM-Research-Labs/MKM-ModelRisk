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
// Model detail view
// ================================================================
function showModelDetail(modelId) {
    console.log('[Governance] Loading model detail:', modelId);
    mgSelectedModel = modelId;
    document.getElementById('mg-back-btn').style.display = 'inline-block';
    document.getElementById('mg-title').textContent = 'Model Detail';

    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading model detail...</div>';

    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/models/' + modelId, {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error loading model</div>';
                return;
            }
            console.log('[Governance] Model loaded:', data.model.short_name, '(Tier', data.model.tier + ')');
            mgDetailData = data;
            renderModelDetail(data.model, data.audit_entries);
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load model detail</div>';
            console.error('[Governance] Model detail error:', err);
        });
}

function renderModelDetail(m, auditEntries) {
    var content = document.getElementById('mg-content');
    var html = '';

    // Model header card
    html += '<div style="padding:16px;background:linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);border-bottom:1px solid #ddd;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:flex-start;">';
    html += '<div>';
    html += '<div style="font-size:20px;font-weight:700;color:#333;">' + (catIcons[m.category] || '') + ' ' + m.name + '</div>';
    html += '<div style="font-size:12px;color:#666;margin-top:4px;">' + m.model_id + ' &middot; v' + m.version + ' &middot; ' + m.category + '</div>';
    html += '<div style="margin-top:8px;">' + tierBadge(m.tier) + ' <span style="font-size:11px;color:#555;margin-left:8px;">' + (tierLabels[m.tier] || '') + '</span>';
    var _rr = (m.overall_risk_rating || {});
    var _effRating = _rr.effective_rating || _rr.calculated_rating || 'Not Rated';
    html += ' <span style="margin-left:8px;">' + riskRatingBadge(_effRating) + '</span>';
    html += '</div>';
    html += '</div>';
    html += '<div style="text-align:right;">';
    html += '<div style="font-size:10px;color:#888;text-transform:uppercase;">Owner' + editBtn('owner', m.model_id) + '</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;">' + m.owner + '</div>';
    html += '<div style="font-size:10px;color:#666;">' + (m.model_owner_role || '') + editBtn('model_owner_role', m.model_id) + '</div>';
    html += '<div style="margin-top:8px;">' + ragBadge(m.rag_rating) + editBtn('rag_rating', m.model_id) + '</div>';
    html += '</div></div>';

    // Governance dates bar
    html += '<div style="display:flex;gap:20px;margin-top:12px;padding-top:10px;border-top:1px solid #ccc;flex-wrap:wrap;">';
    html += '<div style="font-size:11px;"><span style="color:#888;">Last Review:</span> <b>' + (m.last_review_date || '—') + '</b>' + editBtn('last_review_date', m.model_id) + '</div>';
    html += '<div style="font-size:11px;"><span style="color:#888;">MRC Signoff:</span> <b>' + (m.mrc_signoff_date || '—') + '</b>' + editBtn('mrc_signoff_date', m.model_id) + '</div>';
    html += '<div style="font-size:11px;"><span style="color:#888;">Next Review:</span> <b>' + (m.next_review_date || '—') + '</b>' + editBtn('next_review_date', m.model_id) + '</div>';
    html += '<div style="font-size:11px;"><span style="color:#888;">Recertification:</span> <b>' + (m.recertification_date || '—') + '</b>' + editBtn('recertification_date', m.model_id) + '</div>';
    html += '</div>';
    html += '</div>';

    // Detail tabs
    html += '<div id="mg-detail-tabs" style="display:flex;border-bottom:1px solid #eee;background:#fafafa;">';
    var openRem = (m.remediation_steps || []).filter(function(r) { return r.status === 'Open'; }).length;
    var _vqList = m.validation_questions || [];
    var _vqAddr = _vqList.filter(function(q) { return q.status === 'Addressed'; }).length;
    var _vqAppl = _vqList.filter(function(q) { return q.status !== 'Not Applicable'; }).length;
    var detailTabs = [
        {id: 'overview', label: 'Overview'},
        {id: 'remediation', label: 'Remediation' + (openRem > 0 ? ' (' + openRem + ')' : '')},
        {id: 'versions', label: 'Versions (' + (m.version_history || []).length + ')'},
        {id: 'limits', label: 'Limitations (' + (m.limitations || []).length + ')'},
        {id: 'assumptions', label: 'Assumptions (' + (m.assumptions || []).length + ')'},
        {id: 'changes', label: 'Changes'},
        {id: 'validation', label: 'Validation (' + _vqAddr + '/' + _vqAppl + ')'},
        {id: 'riskrating', label: 'Risk Rating'},
        {id: 'docs', label: 'Docs'},
        {id: 'modelaudit', label: 'Audit (' + (auditEntries || []).length + ')'},
    ];
    detailTabs.forEach(function(t, i) {
        html += '<button id="mg-dtab-' + t.id + '" onclick="window.MG.switchDetailTab(\'' + t.id + '\')" style="padding:8px 14px;font-size:11px;border:none;cursor:pointer;border-bottom:2px solid ' + (i === 0 ? '#1976d2' : 'transparent') + ';background:transparent;color:' + (i === 0 ? '#1976d2' : '#666') + ';font-weight:' + (i === 0 ? '600' : '400') + ';">' + t.label + '</button>';
    });
    html += '</div>';

    // Content area
    html += '<div id="mg-detail-content" style="padding:16px;overflow-y:auto;">';
    html += renderOverviewTab(m);
    html += '</div>';

    content.innerHTML = html;

    // Store for tab switching
    window._mgCurrentModel = m;
    window._mgAuditEntries = auditEntries;
}

function switchDetailTab(tabId) {
    var allTabs = ['overview', 'remediation', 'versions', 'limits', 'assumptions', 'changes', 'validation', 'riskrating', 'docs', 'modelaudit'];
    allTabs.forEach(function(t) {
        var btn = document.getElementById('mg-dtab-' + t);
        if (btn) {
            btn.style.borderBottomColor = t === tabId ? '#1976d2' : 'transparent';
            btn.style.color = t === tabId ? '#1976d2' : '#666';
            btn.style.fontWeight = t === tabId ? '600' : '400';
        }
    });

    var m = window._mgCurrentModel;
    var auditEntries = window._mgAuditEntries;
    var dc = document.getElementById('mg-detail-content');
    if (!dc) return;

    // No model loaded (e.g. detail view never opened): render an empty-state
    // rather than throwing on m.model_id inside the per-tab renderers.
    if (!m && tabId !== 'modelaudit') {
        dc.innerHTML = '<div style="padding:40px;text-align:center;color:#888;' +
            'font-size:12px;">No model selected.</div>';
        return;
    }

    if (tabId === 'overview') dc.innerHTML = renderOverviewTab(m);
    else if (tabId === 'remediation') dc.innerHTML = renderRemediationTab(m);
    else if (tabId === 'versions') dc.innerHTML = renderVersionHistoryTab(m);
    else if (tabId === 'limits') dc.innerHTML = renderLimitationsTab(m);
    else if (tabId === 'assumptions') dc.innerHTML = renderAssumptionsTab(m);
    else if (tabId === 'changes') dc.innerHTML = renderChangesTab(m);
    else if (tabId === 'modelaudit') dc.innerHTML = renderAuditTab(auditEntries);
    else if (tabId === 'validation') dc.innerHTML = renderValidationTab(m);
    else if (tabId === 'riskrating') { dc.innerHTML = renderRiskRatingTab(m); refreshRiskRating(m.model_id); }
    else if (tabId === 'docs') dc.innerHTML = renderDocsTab(m);
}

