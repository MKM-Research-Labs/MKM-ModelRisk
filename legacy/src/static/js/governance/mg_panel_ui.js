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
            // Panel expand / restore
            // ================================================================
            function toggleMgExpand() {
                if (!mgPanel) return;
                mgExpanded = !mgExpanded;
                var expandBtn = document.getElementById('mg-expand-btn');
                if (mgExpanded) {
                    mgPanel.style.width = 'calc(100vw - 40px)';
                    mgPanel.style.height = 'calc(100vh - 40px)';
                    if (expandBtn) expandBtn.innerHTML = '&#x2750;';
                    if (expandBtn) expandBtn.title = 'Restore';
                } else {
                    mgPanel.style.width = MG_W;
                    mgPanel.style.height = MG_H;
                    if (expandBtn) expandBtn.innerHTML = '&#x26F6;';
                    if (expandBtn) expandBtn.title = 'Expand';
                }
            }

            // ================================================================
            // Panel creation
            // ================================================================
            function createPanel() {
                if (mgPanel) return mgPanel;

                mgPanel = document.createElement('div');
                mgPanel.id = 'mg-panel';
                mgPanel.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:' + MG_W + ';height:' + MG_H + ';background:white;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.3);z-index:2000;display:none;flex-direction:column;font-family:Arial,Helvetica,sans-serif;overflow:hidden;transition:width 0.2s,height 0.2s;';

                // Header
                var header = document.createElement('div');
                header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-bottom:1px solid #eee;flex-shrink:0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:12px;';

                var title = document.createElement('span');
                title.id = 'mg-title';
                title.textContent = 'Regulatory Compliance';
                title.style.cssText = 'font-size:14px;font-weight:700;color:#333;';

                // Tab buttons
                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid #ddd;border-radius:4px;overflow:hidden;';

                var tabs = [
                    {id: 'inventory', label: 'Inventory'},
                    {id: 'chain', label: 'Model Chain'},
                    {id: 'bcbs239', label: 'BCBS 239'},
                    {id: 'raci', label: 'RACI'},
                    {id: 'mrc', label: 'MRC'},
                    {id: 'audit', label: 'Audit Trail'},
                    {id: 'documents', label: 'Documents'},
                    {id: 'bibliography', label: 'Bibliography'},
                    {id: 'audit-reports', label: 'Audit Reports'},
                    {id: 'lineage', label: 'Data Lineage'},
                    {id: 'field-lineage', label: 'Field Lineage'},
                ];
                tabs.forEach(function(t) {
                    var btn = document.createElement('button');
                    btn.id = 'mg-tab-' + t.id;
                    btn.textContent = t.label;
                    btn.style.cssText = 'padding:3px 12px;font-size:11px;border:none;cursor:pointer;' +
                        (t.id === 'inventory' ? 'background:#1976d2;color:white;' : 'background:white;color:#333;');
                    btn.onclick = (function(tabId) { return function() { switchMgTab(tabId); }; })(t.id);
                    toggleWrap.appendChild(btn);
                });

                leftHeader.appendChild(title);
                leftHeader.appendChild(toggleWrap);

                // Back button (hidden by default)
                var backBtn = document.createElement('button');
                backBtn.id = 'mg-back-btn';
                backBtn.textContent = '\u2190 Back to Models';
                backBtn.style.cssText = 'display:none;padding:6px 14px;font-size:12px;font-weight:500;border:1px solid #1976d2;border-radius:4px;cursor:pointer;background:#e3f2fd;color:#1976d2;margin-left:12px;';
                backBtn.onclick = function() { showInventory(); };
                leftHeader.appendChild(backBtn);

                var rightHeader = document.createElement('div');
                rightHeader.style.cssText = 'display:flex;align-items:center;gap:2px;';

                var expandBtn = document.createElement('button');
                expandBtn.id = 'mg-expand-btn';
                expandBtn.innerHTML = '&#x26F6;';
                expandBtn.title = 'Expand';
                expandBtn.style.cssText = 'border:none;background:none;font-size:18px;cursor:pointer;color:#666;padding:0 6px;line-height:1;';
                expandBtn.onclick = toggleMgExpand;

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText = 'border:none;background:none;font-size:24px;cursor:pointer;color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hideMgPanel;

                rightHeader.appendChild(expandBtn);
                rightHeader.appendChild(closeBtn);

                header.appendChild(leftHeader);
                header.appendChild(rightHeader);

                // Content area
                var content = document.createElement('div');
                content.id = 'mg-content';
                content.style.cssText = 'flex:1;overflow-y:auto;padding:0;';

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'mg-stats-bar';
                statsBar.style.cssText = 'padding:8px 16px;border-top:1px solid #eee;display:flex;gap:20px;font-size:11px;color:#666;background:#f9f9f9;border-radius:0 0 8px 8px;';

                mgPanel.appendChild(header);
                mgPanel.appendChild(content);
                mgPanel.appendChild(statsBar);
                document.body.appendChild(mgPanel);
                return mgPanel;
            }
