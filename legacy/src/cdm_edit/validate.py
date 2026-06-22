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

"""Server-side validation + coercion of an edited CDM field value.

The authoritative check applied on commit: a value is coerced to the field's
CDM type, menu values must be one of the allowed options, and numeric values
must satisfy the bounds from constraints.py. Returns (ok, value, error).
"""

from .constraints import field_spec

_TRUE = {"true", "yes", "1", "y", "t"}
_FALSE = {"false", "no", "0", "n", "f"}


def validate_value(path, descriptor, raw):
    """Validate/coerce ``raw`` for the field ``descriptor`` at ``path``.

    Returns (ok, coerced_value, error_message). ``error_message`` is None on
    success.
    """
    spec = field_spec(path, descriptor)
    cdm_type = descriptor.get("type")

    if raw is None or raw == "":
        # Clearing a value is allowed (the field becomes empty).
        return True, None, None

    if cdm_type == "menu":
        options = descriptor.get("options", [])
        if raw not in options:
            return False, None, "must be one of: " + ", ".join(map(str, options))
        return True, raw, None

    if cdm_type == "boolean":
        if isinstance(raw, bool):
            return True, raw, None
        s = str(raw).strip().lower()
        if s in _TRUE:
            return True, True, None
        if s in _FALSE:
            return True, False, None
        return False, None, "must be true or false"

    if cdm_type in ("integer", "decimal"):
        try:
            value = int(raw) if cdm_type == "integer" else float(raw)
        except (TypeError, ValueError):
            return False, None, "must be a number"
        lo, hi = spec.get("min"), spec.get("max")
        if lo is not None and value < lo:
            return False, None, f"must be ≥ {lo}"
        if hi is not None and value > hi:
            return False, None, f"must be ≤ {hi}"
        return True, value, None

    if cdm_type == "date":
        s = str(raw).strip()
        ok = (len(s) == 10 and s[4] == "-" and s[7] == "-"
              and s[:4].isdigit() and s[5:7].isdigit() and s[8:].isdigit())
        if not ok:
            return False, None, "must be a date (YYYY-MM-DD)"
        return True, s, None

    return True, str(raw), None
