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
// Risk Rating tab
// ================================================================

var riskRatingColors = {
    'Acceptable': '#388e3c',
    'Conditional': '#f57c00',
    'Unacceptable': '#d32f2f',
    'Not Rated': '#9e9e9e'
};

function riskRatingBadge(rating) {
    var c = riskRatingColors[rating] || '#9e9e9e';
    return '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;color:white;background:' + c + ';">' + (rating || 'Not Rated') + '</span>';
}

function renderRiskRatingTab(m) {
    var rr = m.overall_risk_rating || {};
    var effRating = rr.effective_rating || 'Not Rated';
    var calcRating = rr.calculated_rating || 'Not Rated';
    var score = rr.calculated_score;
    var cs = rr.component_scores || {};
    var hasOverride = rr.mrc_override != null;

    var html = '';

    // Section header
    html += '<div style="font-size:13px;font-weight:700;color:#333;margin-bottom:4px;">Overall Model Risk Rating</div>';
    html += '<div style="font-size:11px;color:#666;margin-bottom:16px;">Composite assessment synthesising validation coverage, remediation health, review currency, assumption risk, and limitation risk.</div>';

    // Effective rating banner
    var bannerColor = riskRatingColors[effRating] || '#9e9e9e';
    html += '<div style="padding:20px;border-radius:8px;background:linear-gradient(135deg, ' + bannerColor + '22 0%, ' + bannerColor + '11 100%);border:2px solid ' + bannerColor + ';margin-bottom:16px;text-align:center;">';
    html += '<div style="font-size:10px;color:#888;text-transform:uppercase;margin-bottom:6px;">Effective Rating</div>';
    html += '<div style="font-size:28px;font-weight:800;color:' + bannerColor + ';">' + effRating + '</div>';
    if (score !== null && score !== undefined) {
        html += '<div style="font-size:12px;color:#666;margin-top:4px;">Composite Score: <b>' + Math.round(score * 100) + '%</b></div>';
    }
    if (hasOverride) {
        html += '<div style="font-size:10px;color:#1976d2;margin-top:6px;">MRC Override Active (calculated: ' + calcRating + ')</div>';
    }
    html += '</div>';

    // MRC override info box
    if (hasOverride) {
        html += '<div style="padding:12px 16px;border-radius:6px;border:1px solid #bbdefb;background:#e3f2fd;margin-bottom:16px;">';
        html += '<div style="font-size:11px;font-weight:600;color:#1565c0;margin-bottom:6px;">MRC Override</div>';
        html += '<div style="font-size:11px;color:#333;"><b>Rating:</b> ' + rr.mrc_override + '</div>';
        html += '<div style="font-size:11px;color:#333;"><b>Reason:</b> ' + (rr.mrc_override_reason || '\u2014') + '</div>';
        html += '<div style="font-size:10px;color:#888;margin-top:4px;">' + (rr.mrc_override_by || '') + ' on ' + (rr.mrc_override_date || '') + '</div>';
        html += '</div>';
    }

    // Component breakdown
    html += '<div style="font-size:12px;font-weight:600;color:#333;margin-bottom:12px;">Component Breakdown</div>';

    var components = [
        {key: 'validation_coverage', label: 'Validation Coverage', weight: 0.30, desc: 'Fraction of 9 questions fully addressed'},
        {key: 'remediation_health', label: 'Remediation Health', weight: 0.25, desc: 'Open and overdue remediation items'},
        {key: 'review_currency', label: 'Review Currency', weight: 0.20, desc: 'Is the review schedule current'},
        {key: 'assumption_risk', label: 'Assumption Risk', weight: 0.15, desc: 'High-impact assumption count'},
        {key: 'limitation_risk', label: 'Limitation Risk', weight: 0.10, desc: 'High-impact limitation count'}
    ];

    components.forEach(function(comp) {
        var val = cs[comp.key];
        var pct = val !== null && val !== undefined ? Math.round(val * 100) : 0;
        var color = val === null || val === undefined ? '#9e9e9e' : val >= 0.75 ? '#388e3c' : val >= 0.45 ? '#f57c00' : '#d32f2f';

        html += '<div style="margin-bottom:12px;">';
        html += '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">';
        html += '<div>';
        html += '<span style="font-size:11px;color:#333;font-weight:600;">' + comp.label + '</span>';
        html += '<span style="font-size:10px;color:#888;margin-left:6px;">(' + Math.round(comp.weight * 100) + '% weight)</span>';
        html += '</div>';
        html += '<span style="font-size:12px;font-weight:700;color:' + color + ';">' + (val !== null && val !== undefined ? pct + '%' : 'N/A') + '</span>';
        html += '</div>';
        html += '<div style="height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden;">';
        html += '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:4px;transition:width 0.3s;"></div>';
        html += '</div>';
        html += '<div style="font-size:10px;color:#999;margin-top:2px;">' + comp.desc + '</div>';
        html += '</div>';
    });

    // Last calculated
    if (rr.last_calculated) {
        html += '<div style="font-size:10px;color:#888;margin-top:8px;margin-bottom:16px;">Last calculated: ' + rr.last_calculated.split('T')[0] + '</div>';
    }

    // Action buttons
    html += '<div style="display:flex;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid #eee;">';
    html += '<button onclick="window.MG.refreshRiskRating(\'' + m.model_id + '\')" style="padding:6px 16px;font-size:11px;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:white;color:#1976d2;">Recalculate</button>';
    if (hasOverride) {
        html += '<button onclick="window.MG.clearRiskOverride(\'' + m.model_id + '\')" style="padding:6px 16px;font-size:11px;border:1px solid #d32f2f;border-radius:4px;cursor:pointer;background:white;color:#d32f2f;">Clear Override</button>';
    } else {
        html += '<button onclick="window.MG.showRiskOverrideForm(\'' + m.model_id + '\')" style="padding:6px 16px;font-size:11px;border:1px solid #f57c00;border-radius:4px;cursor:pointer;background:white;color:#f57c00;">Apply MRC Override</button>';
    }
    html += '</div>';

    // Override form area
    html += '<div id="rr-override-area" style="margin-top:12px;"></div>';

    return html;
}

function refreshRiskRating(modelId) {
    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/risk-rating', {mode: 'cors'})
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            var m = window._mgCurrentModel;
            m.overall_risk_rating = data.risk_rating;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderRiskRatingTab(m);
        }
    })
    .catch(function(err) { console.error('[RiskRating] Refresh error:', err); });
}

function showRiskOverrideForm(modelId) {
    var area = document.getElementById('rr-override-area');
    var html = '<div style="padding:16px;border:1px solid #e0e0e0;border-radius:8px;background:#f8fafc;">';
    html += '<div style="font-size:12px;font-weight:600;color:#333;margin-bottom:12px;">Apply MRC Override</div>';

    html += '<div style="margin-bottom:10px;">';
    html += '<label style="font-size:10px;color:#888;text-transform:uppercase;display:block;margin-bottom:3px;">Override Rating</label>';
    html += '<select id="rr-of-rating" style="width:100%;padding:6px 8px;font-size:11px;border:1px solid #ddd;border-radius:4px;">';
    ['Acceptable', 'Conditional', 'Unacceptable'].forEach(function(r) {
        html += '<option value="' + r + '">' + r + '</option>';
    });
    html += '</select></div>';

    html += '<div style="margin-bottom:10px;">';
    html += '<label style="font-size:10px;color:#888;text-transform:uppercase;display:block;margin-bottom:3px;">Reason for Override</label>';
    html += '<textarea id="rr-of-reason" rows="3" placeholder="MRC rationale for overriding the calculated rating..." style="width:100%;padding:6px 8px;font-size:11px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;"></textarea>';
    html += '</div>';

    html += '<div style="margin-bottom:12px;">';
    html += '<label style="font-size:10px;color:#888;text-transform:uppercase;display:block;margin-bottom:3px;">Override By</label>';
    html += '<input id="rr-of-user" type="text" value="Johnny Mattimore" style="width:100%;padding:6px 8px;font-size:11px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;">';
    html += '</div>';

    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.saveRiskOverride(\'' + modelId + '\')" style="padding:6px 16px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:#f57c00;color:white;">Apply Override</button>';
    html += '<button onclick="document.getElementById(\'rr-override-area\').innerHTML=\'\';" style="padding:6px 16px;font-size:11px;border:1px solid #ddd;border-radius:4px;cursor:pointer;background:white;color:#666;">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRiskOverride(modelId) {
    var reason = document.getElementById('rr-of-reason').value.trim();
    if (!reason) { alert('A reason is required for the MRC override'); return; }

    var body = {
        rating: document.getElementById('rr-of-rating').value,
        reason: reason,
        user: document.getElementById('rr-of-user').value.trim() || 'unknown'
    };

    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/risk-rating/override', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mgCurrentModel = data.model;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderRiskRatingTab(data.model);
        } else {
            alert(data.message || 'Failed to save override');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function clearRiskOverride(modelId) {
    var reason = prompt('Reason for clearing the MRC override:');
    if (!reason || !reason.trim()) return;

    var body = {
        rating: null,
        reason: reason.trim(),
        user: 'Johnny Mattimore'
    };

    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/risk-rating/override', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mgCurrentModel = data.model;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderRiskRatingTab(data.model);
        } else {
            alert(data.message || 'Failed to clear override');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

