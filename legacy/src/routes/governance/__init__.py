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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Model Risk Governance API routes.

Provides endpoints for model inventory, audit trail, and governance workflow.
Supports the Model Risk Committee dashboard and validation team reporting.
"""

from .blueprint import governance_bp  # noqa: F401

# Import sub-modules to register their routes on governance_bp.
from . import models      # noqa: E402, F401
from . import audit       # noqa: E402, F401
from . import mrc         # noqa: E402, F401
from . import mrc_crud    # noqa: E402, F401
from . import mrc_pdf     # noqa: E402, F401
from . import compliance  # noqa: E402, F401
from . import documents   # noqa: E402, F401
from . import bibliography    # noqa: E402, F401
from . import audit_reports  # noqa: E402, F401
from . import test_report    # noqa: E402, F401
from . import lineage        # noqa: E402, F401
