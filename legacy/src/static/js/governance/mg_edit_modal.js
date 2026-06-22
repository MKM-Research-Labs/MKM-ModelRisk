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
            // Edit confirmation modal
            // ================================================================
            function openEditModal(field, modelId) {
                var spec = editableFields[field];
                if (!spec) return;

                var m = window._mgCurrentModel;
                var currentVal = m ? (m[field] || '') : '';

                // Remove existing modal
                var old = document.getElementById('mg-edit-modal');
                if (old) old.remove();

                var overlay = document.createElement('div');
                overlay.id = 'mg-edit-modal';
                overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);z-index:3000;display:flex;align-items:center;justify-content:center;';

                var dialog = document.createElement('div');
                dialog.style.cssText = 'background:white;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,0.3);width:420px;max-width:90vw;font-family:Arial,sans-serif;';

                // Header
                var hdr = document.createElement('div');
                hdr.style.cssText = 'padding:16px 20px;border-bottom:1px solid #eee;';
                hdr.innerHTML = '<div style="font-size:14px;font-weight:700;color:#333;">Edit ' + spec.label + '</div><div style="font-size:11px;color:#888;margin-top:2px;">Model: ' + modelId + '</div>';

                // Body
                var body = document.createElement('div');
                body.style.cssText = 'padding:16px 20px;';

                // Current value
                body.innerHTML = '<div style="font-size:11px;color:#666;margin-bottom:12px;">Current value: <b>' + (currentVal || '\u2014') + '</b></div>';

                // Input
                var inputHtml = '';
                if (spec.type === 'choice') {
                    inputHtml = '<select id="mg-edit-value" style="width:100%;padding:8px;font-size:12px;border:1px solid #ddd;border-radius:4px;">';
                    spec.options.forEach(function(opt) {
                        inputHtml += '<option value="' + opt + '"' + (opt === currentVal ? ' selected' : '') + '>' + opt + '</option>';
                    });
                    inputHtml += '</select>';
                } else if (spec.type === 'date') {
                    inputHtml = '<input type="date" id="mg-edit-value" value="' + currentVal + '" style="width:100%;padding:8px;font-size:12px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;">';
                } else {
                    inputHtml = '<input type="text" id="mg-edit-value" value="' + currentVal + '" style="width:100%;padding:8px;font-size:12px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;">';
                }
                body.innerHTML += '<label style="font-size:10px;color:#666;display:block;margin-bottom:4px;">New Value</label>' + inputHtml;

                // Reason
                body.innerHTML += '<div style="margin-top:12px;"><label style="font-size:10px;color:#666;display:block;margin-bottom:4px;">Reason for Change (required)</label><textarea id="mg-edit-reason" rows="3" style="width:100%;padding:8px;font-size:12px;border:1px solid #ddd;border-radius:4px;resize:vertical;box-sizing:border-box;" placeholder="Explain why this change is being made..."></textarea></div>';

                // Error
                body.innerHTML += '<div id="mg-edit-error" style="display:none;margin-top:8px;padding:6px 10px;background:#ffebee;color:#c62828;border-radius:4px;font-size:11px;"></div>';

                // Footer
                var footer = document.createElement('div');
                footer.style.cssText = 'padding:12px 20px;border-top:1px solid #eee;display:flex;gap:8px;justify-content:flex-end;';

                var cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Cancel';
                cancelBtn.style.cssText = 'padding:8px 18px;font-size:12px;border:1px solid #ddd;border-radius:4px;cursor:pointer;background:white;color:#666;';
                cancelBtn.onclick = function() { overlay.remove(); };

                var confirmBtn = document.createElement('button');
                confirmBtn.textContent = 'Confirm Change';
                confirmBtn.style.cssText = 'padding:8px 18px;font-size:12px;border:none;border-radius:4px;cursor:pointer;background:#1976d2;color:white;font-weight:600;';
                confirmBtn.onclick = function() {
                    var newVal = document.getElementById('mg-edit-value').value.trim();
                    var reason = document.getElementById('mg-edit-reason').value.trim();
                    var err = document.getElementById('mg-edit-error');

                    if (!newVal) {
                        err.textContent = 'Please select or enter a new value.';
                        err.style.display = 'block';
                        return;
                    }
                    if (!reason) {
                        err.textContent = 'A reason is required for all governance changes.';
                        err.style.display = 'block';
                        return;
                    }
                    if (newVal === currentVal) {
                        err.textContent = 'New value is the same as the current value.';
                        err.style.display = 'block';
                        return;
                    }

                    confirmBtn.disabled = true;
                    confirmBtn.textContent = 'Saving...';

                    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/update', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            field: field,
                            value: newVal,
                            reason: reason,
                            user: 'David K Kelly',
                        }),
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            overlay.remove();
                            // Refresh the model detail view
                            showModelDetail(modelId);
                        } else {
                            err.textContent = data.message || 'Update failed';
                            err.style.display = 'block';
                            confirmBtn.disabled = false;
                            confirmBtn.textContent = 'Confirm Change';
                        }
                    })
                    .catch(function(e) {
                        err.textContent = 'Network error: ' + e.message;
                        err.style.display = 'block';
                        confirmBtn.disabled = false;
                        confirmBtn.textContent = 'Confirm Change';
                    });
                };

                footer.appendChild(cancelBtn);
                footer.appendChild(confirmBtn);

                dialog.appendChild(hdr);
                dialog.appendChild(body);
                dialog.appendChild(footer);
                overlay.appendChild(dialog);

                // Close on overlay click
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) overlay.remove();
                });

                document.body.appendChild(overlay);
            }
