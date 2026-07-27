# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Client aggregate: register/edit/retire external clients, their org tree and links."""
from src.governance.client.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    record_client_pack,
    register_client,
    remove_collection_item,
    retire_client,
    update_client_field,
    update_collection_item,
)
from src.governance.client.pack import PACK_NAME, build_client_pack, pack_manifest
from src.governance.client.projection import (
    get_client,
    list_clients,
    rebuild_client_view,
)

__all__ = [
    "AGGREGATE_TYPE",
    "register_client",
    "update_client_field",
    "retire_client",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "record_client_pack",
    "get_client",
    "list_clients",
    "rebuild_client_view",
    "build_client_pack",
    "pack_manifest",
    "PACK_NAME",
]
