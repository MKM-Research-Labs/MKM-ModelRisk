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
// Bibliography tab
// ================================================================
var mgBibSortCol = 'year';
var mgBibSortAsc = false;
var mgBibFilter = '';
var mgBibData = [];

function renderBibliography() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading bibliography...</div>';

    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/bibliography', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error loading bibliography</div>';
                return;
            }

            mgBibData = data.references || [];
            var categories = data.categories || [];
            var refs = mgBibData.slice();

            // Filter
            if (mgBibFilter) {
                refs = refs.filter(function(r) { return r.category === mgBibFilter; });
            }

            // Sort
            refs.sort(function(a, b) {
                if (mgBibSortCol === 'year') {
                    return mgBibSortAsc ? ((a.year || 0) - (b.year || 0)) : ((b.year || 0) - (a.year || 0));
                }
                var va = (a[mgBibSortCol] || '').toLowerCase();
                var vb = (b[mgBibSortCol] || '').toLowerCase();
                return mgBibSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
            });

            var html = '<div style="padding:16px;">';

            // Controls bar
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">';
            html += '<div style="display:flex;gap:8px;align-items:center;">';
            html += '<span style="font-size:11px;font-weight:600;color:#555;">Category:</span>';
            html += '<select id="mg-bib-cat" onchange="mgBibFilter=this.value;renderBibliography();" style="padding:4px 8px;font-size:11px;border:1px solid #ccc;border-radius:4px;">';
            html += '<option value="">All (' + mgBibData.length + ')</option>';
            for (var ci = 0; ci < categories.length; ci++) {
                var sel = mgBibFilter === categories[ci] ? ' selected' : '';
                html += '<option value="' + categories[ci] + '"' + sel + '>' + categories[ci] + '</option>';
            }
            html += '</select></div>';
            html += '<div style="display:flex;gap:8px;">';
            html += '<button onclick="window.MG.showBibForm()" style="padding:5px 14px;font-size:11px;background:#1976d2;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:600;">+ Add Reference</button>';
            html += '<button onclick="window.MG.exportBibtex()" style="padding:5px 14px;font-size:11px;background:#f5f5f5;color:#333;border:1px solid #ccc;border-radius:4px;cursor:pointer;">Export BibTeX</button>';
            html += '</div></div>';

            // Table
            html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
            html += '<thead><tr style="background:#eceff1;">';

            var cols = [
                {key:'author', label:'Author(s)', w:'22%'},
                {key:'year', label:'Year', w:'6%'},
                {key:'title', label:'Title', w:'30%'},
                {key:'journal', label:'Journal / Publisher', w:'22%'},
                {key:'category', label:'Category', w:'12%'},
                {key:'_actions', label:'', w:'8%'}
            ];

            for (var ci = 0; ci < cols.length; ci++) {
                var c = cols[ci];
                var sortable = c.key !== '_actions';
                var arrow = '';
                if (c.key === mgBibSortCol) arrow = mgBibSortAsc ? ' \u25b4' : ' \u25be';
                var onClick = sortable ? ' onclick="window.MG.sortBib(\'' + c.key + '\')" style="cursor:pointer;"' : '';
                html += '<th style="padding:8px 10px;text-align:left;font-weight:600;font-size:10px;color:#555;width:' + c.w + ';"' + onClick + '>' + c.label + arrow + '</th>';
            }
            html += '</tr></thead><tbody>';

            for (var i = 0; i < refs.length; i++) {
                var r = refs[i];
                var bg = i % 2 === 0 ? '#fff' : '#f8f9fa';
                var link = r.doi ? 'https://doi.org/' + r.doi : (r.url || '');

                html += '<tr style="background:' + bg + ';border-bottom:1px solid #eee;">';
                html += '<td style="padding:6px 10px;">' + (r.author || '') + '</td>';
                html += '<td style="padding:6px 10px;">' + (r.year || '') + '</td>';
                html += '<td style="padding:6px 10px;">';
                if (link) html += '<a href="' + link + '" target="_blank" style="color:#1976d2;">';
                html += (r.title || '');
                if (link) html += '</a>';
                html += '</td>';
                html += '<td style="padding:6px 10px;color:#666;font-style:italic;">' + (r.journal || '') + '</td>';
                html += '<td style="padding:6px 10px;"><span style="background:#e3f2fd;color:#1565c0;padding:1px 6px;border-radius:8px;font-size:10px;">' + (r.category || '') + '</span></td>';
                html += '<td style="padding:6px 10px;">' +
                    '<a href="#" onclick="event.preventDefault();window.MG.editBibRef(\'' + r.id + '\')" style="color:#1976d2;font-size:10px;">Edit</a> ' +
                    '<a href="#" onclick="event.preventDefault();window.MG.deleteBibRef(\'' + r.id + '\')" style="color:#c62828;font-size:10px;">Del</a>' +
                    '</td></tr>';
            }

            if (refs.length === 0) {
                html += '<tr><td colspan="6" style="padding:20px;text-align:center;color:#888;">No references match filter.</td></tr>';
            }

            html += '</tbody></table></div>';
            content.innerHTML = html;

            document.getElementById('mg-stats-bar').innerHTML =
                '<span>References: <b>' + refs.length + '</b>' + (mgBibFilter ? ' (filtered from ' + mgBibData.length + ')' : '') + '</span>';
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load bibliography: ' + err.message + '</div>';
        });
}

window.MG = window.MG || {};

window.MG.sortBib = function(col) {
    if (mgBibSortCol === col) {
        mgBibSortAsc = !mgBibSortAsc;
    } else {
        mgBibSortCol = col;
        mgBibSortAsc = col === 'year' ? false : true;
    }
    renderBibliography();
};

window.MG.showBibForm = function(editRef) {
    var existing = document.getElementById('mg-bib-form-popup');
    if (existing) existing.remove();

    var r = editRef || {};
    var isEdit = !!r.id;

    var popup = document.createElement('div');
    popup.id = 'mg-bib-form-popup';
    popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;border:1px solid #ccc;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:4000;padding:20px;min-width:420px;font-size:12px;';

    var fields = [
        {id:'bib-author', label:'Author(s)', val: r.author || '', type:'text'},
        {id:'bib-year', label:'Year', val: r.year || '', type:'number'},
        {id:'bib-title', label:'Title', val: r.title || '', type:'text'},
        {id:'bib-journal', label:'Journal / Publisher', val: r.journal || '', type:'text'},
        {id:'bib-doi', label:'DOI', val: r.doi || '', type:'text'},
        {id:'bib-url', label:'URL', val: r.url || '', type:'text'},
        {id:'bib-category', label:'Category', val: r.category || '', type:'text'},
        {id:'bib-notes', label:'Notes', val: r.notes || '', type:'text'}
    ];

    var html = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">' +
        '<span style="font-weight:bold;font-size:14px;">' + (isEdit ? 'Edit' : 'Add') + ' Reference</span>' +
        '<button onclick="document.getElementById(\'mg-bib-form-popup\').remove()" style="border:none;background:none;font-size:20px;cursor:pointer;color:#666;">&times;</button></div>';

    for (var fi = 0; fi < fields.length; fi++) {
        var f = fields[fi];
        html += '<div style="margin-bottom:8px;">' +
            '<label style="display:block;font-size:10px;font-weight:600;color:#555;margin-bottom:2px;">' + f.label + '</label>' +
            '<input id="' + f.id + '" type="' + f.type + '" value="' + f.val.toString().replace(/"/g, '&quot;') + '" ' +
            'style="width:100%;padding:6px 8px;font-size:11px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;"></div>';
    }

    html += '<div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px;">' +
        '<button onclick="document.getElementById(\'mg-bib-form-popup\').remove()" style="padding:6px 16px;font-size:11px;background:#f5f5f5;border:1px solid #ccc;border-radius:4px;cursor:pointer;">Cancel</button>' +
        '<button onclick="window.MG.submitBibRef(' + (isEdit ? "\'" + r.id + "\'" : 'null') + ')" style="padding:6px 16px;font-size:11px;background:#1976d2;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:600;">' + (isEdit ? 'Save' : 'Add') + '</button></div>';

    popup.innerHTML = html;
    document.body.appendChild(popup);
};

window.MG.submitBibRef = function(refId) {
    var body = {
        author: document.getElementById('bib-author').value,
        year: parseInt(document.getElementById('bib-year').value) || 0,
        title: document.getElementById('bib-title').value,
        journal: document.getElementById('bib-journal').value,
        doi: document.getElementById('bib-doi').value,
        url: document.getElementById('bib-url').value,
        category: document.getElementById('bib-category').value,
        notes: document.getElementById('bib-notes').value
    };

    var baseUrl = getBaseUrl();
    var url = baseUrl + '/api/v1/governance/bibliography';
    var method = 'POST';
    if (refId) {
        url += '/' + refId;
        method = 'PUT';
    }

    fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            var popup = document.getElementById('mg-bib-form-popup');
            if (popup) popup.remove();
            if (window.showSuccess) window.showSuccess(refId ? 'Reference updated' : 'Reference added');
            renderBibliography();
        } else {
            if (window.showError) window.showError(data.message || 'Failed');
        }
    })
    .catch(function(err) {
        if (window.showError) window.showError('Failed: ' + err.message);
    });
};

window.MG.editBibRef = function(refId) {
    var ref = mgBibData.find(function(r) { return r.id === refId; });
    if (ref) window.MG.showBibForm(ref);
};

window.MG.deleteBibRef = function(refId) {
    if (!confirm('Delete this reference?')) return;
    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/bibliography/' + refId, {
        method: 'DELETE',
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (window.showSuccess) window.showSuccess('Reference deleted');
            renderBibliography();
        }
    })
    .catch(function(err) {
        if (window.showError) window.showError('Delete failed: ' + err.message);
    });
};

window.MG.exportBibtex = function() {
    var refs = mgBibData || [];
    var bibtex = '';
    for (var i = 0; i < refs.length; i++) {
        var r = refs[i];
        var key = (r.author || 'unknown').split(',')[0].split(' ').pop().toLowerCase() + (r.year || '');
        bibtex += '@article{' + key + ',\n';
        bibtex += '  author = {' + (r.author || '') + '},\n';
        bibtex += '  title = {' + (r.title || '') + '},\n';
        bibtex += '  year = {' + (r.year || '') + '},\n';
        if (r.journal) bibtex += '  journal = {' + r.journal + '},\n';
        if (r.doi) bibtex += '  doi = {' + r.doi + '},\n';
        if (r.url) bibtex += '  url = {' + r.url + '},\n';
        bibtex += '}\n\n';
    }

    var blob = new Blob([bibtex], {type: 'text/plain'});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'bibliography.bib';
    a.click();
};
