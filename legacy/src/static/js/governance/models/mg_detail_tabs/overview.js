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
// Detail tab renderers
// ================================================================
function renderOverviewTab(m) {
    var html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">';

    // Left: key details
    html += '<div>';
    html += sectionHeader('Model Details');
    html += infoRow('Description', m.description);
    html += infoRow('Methodology', m.methodology);
    html += infoRow('Tier Rationale', m.tier_rationale);
    html += infoRow('Source Module', '<code style="font-size:11px;background:#f0f0f0;padding:2px 6px;border-radius:3px;">' + m.source_module + '</code>');
    html += infoRow('Materiality', m.materiality);
    html += infoRow('Complexity', m.complexity);
    html += '</div>';

    // Right: governance status
    html += '<div>';
    html += sectionHeader('Governance Status');
    html += infoRow('RAG Rating', ragBadge(m.rag_rating) + editBtn('rag_rating', m.model_id));
    html += infoRow('Model Owner', '<b>' + (m.owner || '\u2014') + '</b>' + (m.model_owner_role ? ' (' + m.model_owner_role + ')' : '') + editBtn('owner', m.model_id));
    html += infoRow('Lifecycle Stage', statusDot(lifecycleColors[m.lifecycle_stage] || '#999') + m.lifecycle_stage + editBtn('lifecycle_stage', m.model_id));
    html += infoRow('Validation Status', m.validation_status + editBtn('validation_status', m.model_id));
    html += infoRow('Last Review', (m.last_review_date || '<span style="color:#f57c00;">Not yet reviewed</span>') + editBtn('last_review_date', m.model_id));
    html += infoRow('MRC Signoff', (m.mrc_signoff_date || '<span style="color:#f57c00;">Pending</span>') + editBtn('mrc_signoff_date', m.model_id));
    html += infoRow('Next Review', (m.next_review_date || 'Not scheduled') + editBtn('next_review_date', m.model_id));
    html += infoRow('Recertification', (m.recertification_date || 'Not scheduled') + editBtn('recertification_date', m.model_id));
    html += infoRow('Review Frequency', (m.review_frequency || '\u2014') + editBtn('review_frequency', m.model_id));
    html += infoRow('Peer Reviewer', (m.peer_reviewer || '<span style="color:#f57c00;">TBD</span>') + editBtn('peer_reviewer', m.model_id));

    html += sectionHeader('Testing');
    var tc = m.test_coverage || {};
    html += infoRow('Unit Tests', tc.unit_tests ? '\u2705 Yes' : '\u274c No');
    html += infoRow('Integration Tests', tc.integration_tests ? '\u2705 Yes' : '\u274c No');
    html += infoRow('Benchmark Tests', tc.benchmark_tests ? '\u2705 Yes (' + (tc.benchmark_reference || '') + ')' : '\u274c No');
    html += infoRow('Test File', tc.test_file ? '<code style="font-size:10px;background:#f0f0f0;padding:2px 4px;border-radius:2px;">' + tc.test_file + '</code>' : '\u2014');

    if (m.alternatives_considered && m.alternatives_considered.length > 0) {
        html += sectionHeader('Alternatives Considered');
        html += '<div style="font-size:11px;color:#555;">';
        m.alternatives_considered.forEach(function(a) {
            html += '<div style="padding:2px 0;">\u2022 ' + a + '</div>';
        });
        html += '<div style="margin-top:6px;font-size:11px;color:#333;font-style:italic;">' + (m.methodology_rationale || '') + '</div>';
        html += '</div>';
    }

    // Dependencies
    html += sectionHeader('Dependencies');
    html += infoRow('Upstream', (m.upstream_models && m.upstream_models.length > 0) ? m.upstream_models.join(', ') : 'None (input model)');
    html += infoRow('Downstream', (m.downstream_models && m.downstream_models.length > 0) ? m.downstream_models.join(', ') : 'None (terminal model)');

    // Known failure modes
    if (m.known_failure_modes && m.known_failure_modes.length > 0) {
        html += sectionHeader('Known Failure Modes');
        html += '<div style="font-size:11px;color:#555;">';
        m.known_failure_modes.forEach(function(f) {
            html += '<div style="padding:2px 0;color:#d32f2f;">\u26a0 ' + f + '</div>';
        });
        html += '</div>';
    }

    html += '</div></div>';
    return html;
}
