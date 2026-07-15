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
"""Render bibliography references as BibTeX (pure)."""
from __future__ import annotations

_FIELD_MAP = (("authors", "author"), ("title", "title"), ("year", "year"),
              ("journal", "journal"), ("url", "url"), ("notes", "note"))


def to_bibtex(references: list[dict]) -> str:
    """Render references as a BibTeX document."""
    entries = []
    for ref in references:
        key = (ref.get("item_id") or "ref").replace("-", "")
        lines = [
            f"  {bib} = {{{ref[key_in]}}}"
            for key_in, bib in _FIELD_MAP
            if ref.get(key_in)
        ]
        entries.append("@misc{" + key + ",\n" + ",\n".join(lines) + "\n}")
    return "\n\n".join(entries) + "\n" if entries else ""
