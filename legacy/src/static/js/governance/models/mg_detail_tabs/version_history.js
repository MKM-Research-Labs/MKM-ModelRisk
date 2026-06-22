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

function renderVersionHistoryTab(m) {
    var versions = m.version_history || [];
    if (versions.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No version history recorded</div>';

    var html = '<div style="padding:12px;">';

    // Current version banner
    html += '<div style="padding:10px 14px;background:#e3f2fd;border-radius:6px;border-left:3px solid #1976d2;margin-bottom:16px;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Current Version</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#1976d2;margin-left:10px;">v' + m.version + '</span>';
    html += '<span style="font-size:11px;color:#666;margin-left:10px;">' + m.lifecycle_stage + '</span>';
    html += '</div>';

    // Timeline
    html += '<div style="position:relative;padding-left:24px;">';

    // Vertical line
    html += '<div style="position:absolute;left:8px;top:8px;bottom:8px;width:2px;background:#e0e0e0;"></div>';

    versions.slice().reverse().forEach(function(v, i) {
        var isCurrent = v.version === m.version;
        var dotColor = isCurrent ? '#1976d2' : '#9e9e9e';
        var dotSize = isCurrent ? '12px' : '8px';

        html += '<div style="position:relative;padding:10px 0 16px 16px;">';

        // Timeline dot
        html += '<div style="position:absolute;left:-' + (isCurrent ? '18px' : '16px') + ';top:14px;width:' + dotSize + ';height:' + dotSize + ';border-radius:50%;background:' + dotColor + ';border:2px solid white;box-shadow:0 0 0 1px ' + dotColor + ';"></div>';

        // Version card
        html += '<div style="padding:12px 16px;border:1px solid ' + (isCurrent ? '#bbdefb' : '#e0e0e0') + ';border-radius:6px;background:' + (isCurrent ? '#f5f9ff' : 'white') + ';">';

        // Header row
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">';
        html += '<div>';
        html += '<span style="font-size:14px;font-weight:700;color:' + (isCurrent ? '#1976d2' : '#333') + ';">v' + v.version + '</span>';
        if (isCurrent) html += ' ' + badge('Current', '#1976d2');
        html += '</div>';
        html += '<span style="font-size:11px;color:#888;">' + v.date + '</span>';
        html += '</div>';

        // Description
        html += '<div style="font-size:12px;color:#555;margin-bottom:6px;">' + v.description + '</div>';

        // Footer
        html += '<div style="display:flex;gap:16px;font-size:10px;color:#888;">';
        html += '<span>Author: <b>' + v.author + '</b></span>';
        if (v.document) {
            html += '<span>Ref: <span style="color:#1976d2;">' + v.document + '</span></span>';
        }
        html += '</div>';

        html += '</div></div>';
    });

    html += '</div></div>';
    return html;
}
