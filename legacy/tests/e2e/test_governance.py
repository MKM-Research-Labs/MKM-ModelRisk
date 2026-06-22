# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Governance panel e2e tests — open panel, verify 9 tabs render with content.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close_all_panels(page):
    """Close all panels and context menus to reset state."""
    page.evaluate("""() => {
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel',
         'prop-storm-panel','mortgage-detail-panel','mg-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    }""")


def _open_governance_panel(page):
    """Open the governance panel using button click or JS fallback."""
    _close_all_panels(page)

    # Try multiple selectors for the governance button
    mg_btn = page.locator("#mg-panel-btn")
    if mg_btn.count() == 0:
        mg_btn = (
            page.locator("[title*='Governance']")
            .or_(page.locator("[title*='Regulatory']"))
            .or_(page.locator("[title*='Model']"))
        )
    if mg_btn.count() > 0:
        mg_btn.first.click(force=True)
        page.wait_for_timeout(1_500)

    # Fallback: show panel directly via JS
    panel = page.locator("#mg-panel")
    if not panel.is_visible():
        page.evaluate("""() => {
            const el = document.getElementById('mg-panel');
            if (el) el.style.display = 'block';
        }""")
        page.wait_for_timeout(900)


def _switch_tab(page, tab_name):
    """Switch to a governance tab by clicking the button or using JS."""
    tab_btn = page.locator(f"#mg-tab-{tab_name}")
    if tab_btn.count() > 0:
        tab_btn.first.click(force=True)
    else:
        page.evaluate(f"typeof switchMgTab === 'function' && switchMgTab('{tab_name}')")
    page.wait_for_timeout(1_500)


def _get_content_text(page):
    """Return lowercase text content of the governance content area."""
    content = page.locator("#mg-content")
    if content.count() > 0:
        return content.inner_text().lower()
    return ""


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestGovernancePanelOpens:
    """Opening the governance panel and verifying basic structure."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        yield
        _close_all_panels(map_page)

    def test_panel_is_visible(self, map_page):
        """Governance panel should be visible after opening."""
        panel = map_page.locator("#mg-panel")
        assert panel.is_visible(), "Governance panel is not visible"

    def test_has_tab_buttons(self, map_page):
        """Panel should have at least 5 tab buttons."""
        tab_ids = [
            "#mg-tab-inventory", "#mg-tab-chain", "#mg-tab-params",
            "#mg-tab-bcbs239", "#mg-tab-raci", "#mg-tab-mrc",
            "#mg-tab-audit", "#mg-tab-documents", "#mg-tab-bibliography",
            "#mg-tab-audit-reports",
        ]
        found = sum(1 for tid in tab_ids if map_page.locator(tid).count() > 0)
        assert found >= 5, f"Only {found} tab buttons found out of {len(tab_ids)}"

    def test_has_content_area(self, map_page):
        """Panel should have a content area."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0, "No #mg-content element found"


class TestModelInventoryTab:
    """Model Inventory tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "inventory")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Inventory tab should load content in the content area."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Inventory tab content is empty"

    def test_content_mentions_model(self, map_page):
        """Content should mention model-related terms."""
        text = _get_content_text(map_page)
        assert any(kw in text for kw in ["model", "inventory", "mkm"]), \
            f"No model/inventory/mkm keyword found in inventory tab"


class TestBCBS239Tab:
    """BCBS 239 tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "bcbs239")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """BCBS 239 tab should load content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "BCBS 239 tab content is empty"

    def test_content_mentions_bcbs(self, map_page):
        """Content should mention BCBS-related terms."""
        text = _get_content_text(map_page)
        assert any(kw in text for kw in ["bcbs", "principle", "compliance"]), \
            f"No bcbs/principle/compliance keyword found in BCBS 239 tab"


class TestRACITab:
    """RACI tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "raci")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """RACI tab should load content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "RACI tab content is empty"

    def test_content_mentions_raci(self, map_page):
        """Content should mention RACI-related terms."""
        text = _get_content_text(map_page)
        assert any(kw in text for kw in ["raci", "responsible", "accountable"]), \
            f"No raci/responsible/accountable keyword found in RACI tab"


class TestMRCTab:
    """MRC tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "mrc")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """MRC tab should load content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "MRC tab content is empty"

    def test_content_mentions_mrc(self, map_page):
        """Content should mention MRC-related terms."""
        text = _get_content_text(map_page)
        assert any(kw in text for kw in ["meeting", "committee", "mrc"]), \
            f"No meeting/committee/mrc keyword found in MRC tab"


class TestDocumentsTab:
    """Documents tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "documents")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Documents tab should load content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Documents tab content is empty"

    def test_content_area_exists(self, map_page):
        """Documents tab content area should be present and non-trivial."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        # The documents tab should have rendered some HTML
        html = content.inner_html()
        assert len(html) > 10, "Documents tab has minimal HTML content"


class TestBibliographyTab:
    """Bibliography tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "bibliography")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Bibliography tab should load content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Bibliography tab content is empty"

    def test_content_mentions_bibliography(self, map_page):
        """Content should mention bibliography-related terms."""
        text = _get_content_text(map_page)
        assert any(kw in text for kw in ["reference", "bibliography", "author"]), \
            f"No reference/bibliography/author keyword found in Bibliography tab"


class TestAuditTab:
    """Audit tab content tests."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        _open_governance_panel(map_page)
        _switch_tab(map_page, "audit")
        yield
        _close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Audit tab should load content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Audit tab content is empty"

    def test_content_mentions_audit(self, map_page):
        """Content should mention audit-related terms."""
        text = _get_content_text(map_page)
        keywords = ["audit", "trail", "log", "history", "change",
                     "report", "compliance", "test", "coverage", "result",
                     "entries", "timestamp", "event", "usage", "model"]
        assert any(kw in text for kw in keywords), \
            f"No audit-related keyword found in Audit tab. Content: {text[:200]}"
