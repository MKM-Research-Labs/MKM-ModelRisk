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
            // Colour and badge helpers
            // ================================================================
            var tierColors = {1: '#d32f2f', 2: '#f57c00', 3: '#1976d2', 4: '#388e3c'};
            var tierLabels = {1: 'Tier 1 - Maximum', 2: 'Tier 2 - Substantial', 3: 'Tier 3 - Moderate', 4: 'Tier 4 - Minimal'};
            var reviewColors = {'Overdue': '#d32f2f', 'Due Soon': '#f57c00', 'Upcoming': '#fbc02d', 'On Track': '#388e3c', 'Not Scheduled': '#9e9e9e'};
            var catIcons = {'Hazard': '\u26a0\ufe0f', 'Pricing': '\ud83d\udcb0', 'Loss': '\ud83d\udcc9', 'Spatial': '\ud83c\udf0d', 'Valuation': '\ud83c\udfe0', 'Risk': '\ud83d\udcca'};
            var lifecycleColors = {'Production': '#388e3c', 'Development': '#1976d2', 'Validation': '#f57c00', 'Retired': '#9e9e9e'};
            var ragColors = {'Green': '#388e3c', 'Amber': '#f57c00', 'Red': '#d32f2f', 'Not Rated': '#9e9e9e'};

            function badge(text, bg, fg) {
                return '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;background:' + bg + ';color:' + (fg || 'white') + ';">' + text + '</span>';
            }

            function tierBadge(tier) {
                return badge('Tier ' + tier, tierColors[tier] || '#999');
            }

            function reviewBadge(status) {
                return badge(status, reviewColors[status] || '#999');
            }

            function statusDot(color) {
                return '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + color + ';margin-right:4px;"></span>';
            }

            function ragBadge(rating) {
                var color = ragColors[rating] || '#9e9e9e';
                return '<span style="display:inline-flex;align-items:center;gap:4px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + color + ';border:1px solid ' + color + '88;"></span><span style="font-size:10px;font-weight:600;color:' + color + ';">' + (rating || 'Not Rated') + '</span></span>';
            }

            // ================================================================
            // Editable field definitions (mirrors server-side EDITABLE_FIELDS)
            // ================================================================
            var editableFields = {
                rag_rating: {type: 'choice', options: ['Green', 'Amber', 'Red'], label: 'RAG Rating'},
                owner: {type: 'text', label: 'Model Owner'},
                model_owner_role: {type: 'text', label: 'Owner Role'},
                lifecycle_stage: {type: 'choice', options: ['Development', 'Validation', 'Production', 'Retired'], label: 'Lifecycle Stage'},
                peer_reviewer: {type: 'text', label: 'Peer Reviewer'},
                last_review_date: {type: 'date', label: 'Last Review Date'},
                next_review_date: {type: 'date', label: 'Next Review Date'},
                mrc_signoff_date: {type: 'date', label: 'MRC Signoff Date'},
                recertification_date: {type: 'date', label: 'Recertification Date'},
                validation_status: {type: 'choice', options: ['Initial', 'Pending', 'Validated', 'Conditionally Approved', 'Rejected'], label: 'Validation Status'},
                review_frequency: {type: 'choice', options: ['Monthly', 'Quarterly', 'Semi-annual', 'Annual'], label: 'Review Frequency'},
            };

            function editBtn(field, modelId) {
                return '<button onclick="window.MG.openEdit(\'' + field + '\', \'' + modelId + '\')" style="margin-left:6px;padding:1px 6px;font-size:9px;border:1px solid #ccc;border-radius:3px;cursor:pointer;background:#f9f9f9;color:#666;" title="Edit ' + (editableFields[field] ? editableFields[field].label : field) + '">Edit</button>';
            }

            // ================================================================
            // HTML helpers
            // ================================================================
            function sectionHeader(text) {
                return '<div style="font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-top:16px;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #eee;">' + text + '</div>';
            }

            function infoRow(label, value) {
                return '<div style="display:flex;padding:3px 0;font-size:11px;">' +
                    '<span style="min-width:130px;color:#888;flex-shrink:0;">' + label + '</span>' +
                    '<span style="color:#333;">' + value + '</span></div>';
            }
