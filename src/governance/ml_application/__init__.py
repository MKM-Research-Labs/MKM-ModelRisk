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
"""The ML Application aggregate: a use case for an off-the-shelf estimator.

Kept apart from the model inventory because it changes at a different rate (see
docs/design/mlmodel.md), but built from the same machinery -- the shared
collection specs, the division's ratified risk policy, and the same committee
route -- so it evidences the same clauses without a second implementation of any
of it.
"""
from src.governance.ml_application.commands import (AGGREGATE_TYPE, add_collection_item,
                                                    reactivate_ml_application,
                                                    register_ml_application,
                                                    remove_collection_item,
                                                    retire_ml_application,
                                                    update_collection_item,
                                                    update_ml_application_field)
from src.governance.ml_application.projection import (get_ml_application,
                                                      list_ml_applications,
                                                      rebuild_ml_application_view)

__all__ = ["AGGREGATE_TYPE", "add_collection_item", "get_ml_application",
           "list_ml_applications", "reactivate_ml_application",
           "rebuild_ml_application_view", "register_ml_application",
           "remove_collection_item", "retire_ml_application",
           "update_collection_item", "update_ml_application_field"]
