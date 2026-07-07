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
"""Product aggregate: register/rebind/edit/retire Product Valuation Models and query them."""
from src.governance.product.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    rebind_component,
    register_product,
    remove_collection_item,
    retire_product,
    update_collection_item,
    update_product_field,
)
from src.governance.product.projection import (
    derived_identifier,
    get_product,
    list_products,
    rebuild_product_view,
)

__all__ = [
    "AGGREGATE_TYPE",
    "register_product",
    "rebind_component",
    "update_product_field",
    "retire_product",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "derived_identifier",
    "get_product",
    "list_products",
    "rebuild_product_view",
]
