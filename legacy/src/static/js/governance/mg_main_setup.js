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
            // Map control button (standalone, top-right)
            // ================================================================
            function addMapControl() {
                function findMap() {
                    var mapKey = Object.keys(window).find(function(k) { return k.startsWith('map_'); });
                    if (mapKey) return window[mapKey];
                    return null;
                }

                function tryAdd() {
                    var map = findMap();
                    if (!map) {
                        setTimeout(tryAdd, 500);
                        return;
                    }

                    var GovernanceControl = L.Control.extend({
                        options: { position: 'topright' },
                        onAdd: function() {
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = 'Regulatory Compliance';
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:white;';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {
                                L.DomEvent.preventDefault(e);
                                showMgPanel();
                            });
                            return container;
                        }
                    });

                    new GovernanceControl().addTo(map);
                }

                setTimeout(tryAdd, 1000);
            }

            // Global API
            window.showModelGovernance = showMgPanel;
            window.MG = {
                show: showMgPanel,
                hide: hideMgPanel,
                showDetail: showModelDetail,
                switchDetailTab: switchDetailTab,
                switchDocsSection: switchDocsSection,
                openEdit: openEditModal,
                toggleSort: mgToggleSort,
                setFilter: mgSetFilter,
                setDateFilter: mgSetDateFilter,
                clearFilters: mgClearFilters,
                switchMrcTab: switchMrcSubTab,
                showMeeting: showMrcMeeting,
                switchMeetingTab: switchMeetingTab,
                showNewMeetingForm: showNewMeetingForm,
                createMeeting: createMeeting,
                uploadMeetingDoc: uploadMeetingDoc,
                addNewMeetingDoc: addNewMeetingDoc,
                removeNewMeetingDoc: removeNewMeetingDoc,
                showAgendaForm: showAgendaForm,
                saveAgendaItem: saveAgendaItem,
                deleteAgendaItem: deleteAgendaItem,
                showMinuteForm: showMinuteForm,
                saveMinuteItem: saveMinuteItem,
                deleteMinuteItem: deleteMinuteItem,
                showParticipantForm: showParticipantForm,
                saveParticipant: saveParticipant,
                deleteParticipant: deleteParticipant,
                showDecisionForm: showDecisionForm,
                saveDecision: saveDecision,
                deleteDecision: deleteDecision,
                showActionForm: showActionForm,
                saveAction: saveAction,
                deleteAction: deleteAction,
                downloadMeetingPdf: downloadMeetingPdf,
                toggleBcbs239Principle: toggleBcbs239Principle,
                showBcbs239EditForm: showBcbs239EditForm,
                saveBcbs239Principle: saveBcbs239Principle,
                downloadBcbs239Pdf: downloadBcbs239Pdf,
                toggleVqQuestion: toggleVqQuestion,
                showVqEditForm: showVqEditForm,
                saveVqQuestion: saveVqQuestion,
                showRiskOverrideForm: showRiskOverrideForm,
                saveRiskOverride: saveRiskOverride,
                clearRiskOverride: clearRiskOverride,
                refreshRiskRating: refreshRiskRating,
                showRaciEditRole: showRaciEditRole,
                saveRaciRole: saveRaciRole,
                toggleRaciActivity: toggleRaciActivity,
                showRaciEditActivity: showRaciEditActivity,
                saveRaciActivity: saveRaciActivity,
                showRaciEditEscalation: showRaciEditEscalation,
                saveRaciEscalation: saveRaciEscalation,
                sortBib: window.MG && window.MG.sortBib,
                showBibForm: window.MG && window.MG.showBibForm,
                submitBibRef: window.MG && window.MG.submitBibRef,
                editBibRef: window.MG && window.MG.editBibRef,
                deleteBibRef: window.MG && window.MG.deleteBibRef,
                exportBibtex: window.MG && window.MG.exportBibtex,
                uploadDocument: window.MG && window.MG.uploadDocument,
                downloadDocument: window.MG && window.MG.downloadDocument,
                deleteDocument: window.MG && window.MG.deleteDocument,
            };

            // Add map control button on load
            addMapControl();

            console.log('Model Governance panel ready');
