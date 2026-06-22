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

(function() {
    var MG_W = '__PANEL_W__';
    var MG_H = '__PANEL_H__';
    var mgPanel = null;
    var mgData = null;
    var mgDetailData = null;
    var mgActiveTab = 'inventory';
    var mgSelectedModel = null;
    var mgSortCol = null;
    var mgSortAsc = true;
    var mgFilters = {};
    var mgExpanded = false;

    function getBaseUrl() {
        var cfg = window.__BACKEND_CONFIG || {};
        return cfg.url || '';
    }

    // ==============================================================
    // Sub-module code
    // ==============================================================
__MG_HELPERS_JS__
__MG_EDIT_MODAL_JS__
__MG_PANEL_UI_JS__
__MG_INVENTORY_JS__
__MG_DETAIL_HEADER_JS__
__MG_DETAIL_TABS_JS__
__MG_CHAIN_JS__
__MG_BCBS239_JS__
__MG_VALIDATION_JS__
__MG_RACI_JS__
__MG_MRC_JS__
__MG_MRC_MEETING_JS__
__MG_AUDIT_JS__
__MG_DOCUMENTS_JS__
__MG_BIBLIOGRAPHY_JS__
__MG_AUDIT_REPORTS_JS__
__MG_LINEAGE_JS__
__MG_FIELD_LINEAGE_JS__

    // ================================================================
    // Tab switching
    // ================================================================
    function switchMgTab(tab) {
        console.log('[Governance] Switching to tab:', tab);
        mgActiveTab = tab;
        mgSelectedModel = null;
        document.getElementById('mg-back-btn').style.display = 'none';
        // Restore default scroll for non-BCBS tabs
        var contentEl = document.getElementById('mg-content');
        if (contentEl) contentEl.style.overflowY = (tab === 'bcbs239' || tab === 'raci') ? 'hidden' : 'auto';
        ['inventory', 'chain', 'params', 'bcbs239', 'raci', 'mrc', 'audit', 'documents', 'bibliography', 'audit-reports', 'lineage', 'field-lineage'].forEach(function(t) {
            var btn = document.getElementById('mg-tab-' + t);
            if (btn) {
                btn.style.background = t === tab ? '#1976d2' : 'white';
                btn.style.color = t === tab ? 'white' : '#333';
            }
        });
        document.getElementById('mg-title').textContent = 'Regulatory Compliance';

        if (tab === 'inventory') renderInventory();
        else if (tab === 'chain') renderModelChain();
        else if (tab === 'bcbs239') renderBCBS239();
        else if (tab === 'raci') renderRACITab();
        else if (tab === 'mrc') renderMRC();
        else if (tab === 'audit') renderAuditTrail();
        else if (tab === 'documents') renderDocuments();
        else if (tab === 'bibliography') renderBibliography();
        else if (tab === 'audit-reports') renderAuditReports();
        else if (tab === 'lineage') renderDataLineage();
        else if (tab === 'field-lineage') renderFieldLineage();
    }

    // ================================================================
    // Show / hide / navigation
    // ================================================================
    function showInventory() {
        mgSelectedModel = null;
        document.getElementById('mg-back-btn').style.display = 'none';
        switchMgTab('inventory');
    }

    function showMgPanel() {
        console.log('[Governance] Opening panel');
        createPanel();
        mgPanel.style.display = 'flex';
        mgSelectedModel = null;

        var content = document.getElementById('mg-content');
        content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading model inventory...</div>';

        var baseUrl = getBaseUrl();
        console.log('[Governance] Fetching model inventory from', baseUrl + '/api/v1/governance/models');
        fetch(baseUrl + '/api/v1/governance/models', {mode: 'cors'})
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.status !== 'success') {
                    content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + (data.message || 'Unknown') + '</div>';
                    return;
                }
                console.log('[Governance] Loaded', data.total_models, 'models');
                mgData = data;
                switchMgTab('inventory');
            })
            .catch(function(err) {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load model inventory. Is the server running?</div>';
                console.error('[Governance] Load error:', err);
            });
    }

    function hideMgPanel() {
        if (mgPanel) mgPanel.style.display = 'none';
        console.log('[Governance] Panel closed');
    }

__MG_MAIN_SETUP_JS__
})();
