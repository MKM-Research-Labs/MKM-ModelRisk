# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Document categories and bibliography field specs (coding rule R1)."""

# Per-model document categories (each a sub-tab on the model Docs tab). The
# Unit/Integration/Benchmark Test, Event Evidence and Remediation Evidence
# categories back the in-context upload panels on the Testing block and the
# Events / Remediation tabs (they still appear on the Docs tab too).
DOC_CATEGORIES = (
    "Core Documentation", "Test Results", "Analysis", "Monitoring",
    "Unit Test", "Integration Test", "Benchmark Test",
    "Event Evidence", "Remediation Evidence",
)

# Bibliography reference fields (top-level References tab + BibTeX export).
BIBLIOGRAPHY_SPEC = {"label": "References", "id_prefix": "REF", "fields": [
    {"key": "authors", "label": "Author(s)", "type": "text", "required": True},
    {"key": "year", "label": "Year", "type": "text"},
    {"key": "title", "label": "Title", "type": "text", "required": True},
    {"key": "journal", "label": "Journal / Publisher", "type": "text"},
    {"key": "category", "label": "Category", "type": "text"},
    {"key": "url", "label": "URL", "type": "text"},
    {"key": "notes", "label": "Notes", "type": "textarea"},
]}
BIBLIOGRAPHY_SPECS = {"references": BIBLIOGRAPHY_SPEC}
