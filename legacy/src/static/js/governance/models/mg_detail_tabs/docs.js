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

function renderDocsTab(m) {
    if (!m || !m.model_id) {
        return '<div style="padding:40px;text-align:center;color:#888;font-size:12px;">' +
            'No model selected.</div>';
    }
    var docUrl = '/api/v1/governance/models/' + m.model_id + '/documentation/pdf';
    var testUrl = '/api/v1/governance/models/' + m.model_id + '/test-results/pdf';
    var analysisUrl = '/api/v1/governance/models/' + m.model_id + '/analysis/pdf';

    var html = '<div style="display:flex;flex-direction:column;height:100%;">';

    // Sub-tab bar
    html += '<div id="mg-docs-subtabs" style="display:flex;gap:0;border-bottom:2px solid #e0e0e0;margin-bottom:12px;">';
    var sections = [
        {id: 'core-docs', label: 'Core Documentation'},
        {id: 'test-results', label: 'Test Results'},
        {id: 'analysis', label: 'Analysis'},
    ];
    sections.forEach(function(s, i) {
        var active = i === 0;
        html += '<button id="mg-docs-btn-' + s.id + '" onclick="window.MG.switchDocsSection(\'' + s.id + '\')" ';
        html += 'style="padding:8px 16px;font-size:11px;font-weight:' + (active ? '600' : '400') + ';';
        html += 'border:none;cursor:pointer;background:transparent;';
        html += 'color:' + (active ? '#1976d2' : '#666') + ';';
        html += 'border-bottom:2px solid ' + (active ? '#1976d2' : 'transparent') + ';';
        html += 'margin-bottom:-2px;">' + s.label + '</button>';
    });
    html += '</div>';

    // Section containers
    // -- Core Documentation
    html += '<div id="mg-docs-sec-core-docs" style="flex:1;display:flex;flex-direction:column;">';
    html += _docsPdfSection(docUrl, 'mg-doc-pdf-container', 'Model documentation for ' + m.model_id + ' &mdash; ' + m.name);
    html += '</div>';

    // -- Test Results (hidden initially)
    html += '<div id="mg-docs-sec-test-results" style="flex:1;display:none;flex-direction:column;">';
    html += _docsPdfSection(testUrl, 'mg-test-pdf-container', 'Automated test results for model ' + m.model_id);
    html += '</div>';

    // -- Analysis (hidden initially)
    html += '<div id="mg-docs-sec-analysis" style="flex:1;display:none;flex-direction:column;">';
    html += _docsPdfSection(analysisUrl, 'mg-analysis-pdf-container', 'Model analysis for ' + m.model_id + ' &mdash; sensitivity, stress testing');
    html += '</div>';

    html += '</div>';

    // Check PDF availability for each section
    var checks = [
        {url: docUrl, containerId: 'mg-doc-pdf-container', label: 'No Documentation Available', hint: 'Model documentation PDF has not been generated for ' + m.model_id + '.'},
        {url: testUrl, containerId: 'mg-test-pdf-container', label: 'No Test Results Available', hint: 'Run: <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;">python app.py check tests --pdf</code>'},
        {url: analysisUrl, containerId: 'mg-analysis-pdf-container', label: 'No Analysis Available', hint: 'Run: <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;">python -m docs.models.sensitivities.generate_all_analysis</code>'},
    ];
    checks.forEach(function(c) {
        fetch(c.url, {method: 'HEAD'}).then(function(resp) {
            if (!resp.ok) {
                var el = document.getElementById(c.containerId);
                if (el) {
                    el.innerHTML = '<div style="padding:40px;text-align:center;">' +
                        '<div style="font-size:32px;margin-bottom:12px;">&#x26A0;</div>' +
                        '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">' + c.label + '</div>' +
                        '<div style="font-size:11px;color:#888;">' + c.hint + '</div></div>';
                }
            }
        });
    });

    return html;
}

function _docsPdfSection(pdfUrl, containerId, description) {
    var html = '';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;margin-bottom:8px;">';
    html += '<div style="font-size:12px;color:#666;">' + description + '</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:11px;font-weight:500;">&#x2913; Download PDF</a>';
    html += '</div>';
    html += '<div id="' + containerId + '" style="flex:1;min-height:500px;border:1px solid #e0e0e0;border-radius:6px;overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="500" style="border:none;">';
    html += '<div style="padding:40px;text-align:center;">';
    html += '<div style="font-size:32px;margin-bottom:12px;">&#x1F4C4;</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">PDF Document</div>';
    html += '<div style="font-size:11px;color:#888;margin-bottom:16px;">Your browser cannot display the PDF inline.</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-block;padding:8px 20px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:12px;">Open PDF</a>';
    html += '</div></object></div>';
    return html;
}

function switchDocsSection(sectionId) {
    var sectionIds = ['core-docs', 'test-results', 'analysis'];
    sectionIds.forEach(function(s) {
        var sec = document.getElementById('mg-docs-sec-' + s);
        var btn = document.getElementById('mg-docs-btn-' + s);
        if (sec) sec.style.display = s === sectionId ? 'flex' : 'none';
        if (btn) {
            btn.style.borderBottomColor = s === sectionId ? '#1976d2' : 'transparent';
            btn.style.color = s === sectionId ? '#1976d2' : '#666';
            btn.style.fontWeight = s === sectionId ? '600' : '400';
        }
    });
}
