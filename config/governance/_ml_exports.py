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
"""Re-exports for the ML area, so the package ``__init__`` does not carry them.

``config/governance/__init__.py`` is a pure aggregate (coding rule R4: packages
re-export, they do not compute) and it had grown to the 300-line file limit (R2)
purely by being long. Each area's exports now gather here first, so adding one is a
change to this module rather than a squeeze against the gate.
"""
from config.governance._ml import (  # noqa: F401
    DEFAULT_ESTIMATORS,
    ESTIMATOR_LIST,
    ML_APPLICATION_QUESTIONS,
    ML_APPLICATION_QUESTION_LIST,
    ML_TRAINING_LISTS,
    ML_TRAINING_VOCABULARIES,
)
from config.governance._ml_application import (  # noqa: F401
    ML_APPLICATION_COLLECTION_SPECS,
    ML_APPLICATION_EDITABLE_FIELDS,
    ML_APPLICATION_FIELD_CHOICES,
    ML_APPLICATION_FIELD_SPECS,
    ML_APPLICATION_ID_PREFIX,
    ML_APPLICATION_REGISTER_FIELDS,
    ML_APPLICATION_REGISTER_OPTIONAL,
    ML_REVIEW_QUESTIONS_COLLECTION,
)
from config.governance._ml_review_policy import (  # noqa: F401
    DEFAULT_ITEM_POLICY,
    ML_REVIEW_ITEM_SOURCES,
    ML_REVIEW_POLICY_AGGREGATE,
    ML_REVIEW_POLICY_NOUN,
    QUESTION_GROUP_KEY,
    QUESTION_GROUP_LABEL,
    QUESTION_ITEM_SOURCE,
    TRAINING_ITEM_SOURCE,
    default_review_policy,
    item_group_labels,
    policy_item_id,
    resolve_item,
    split_item_id,
    training_policy_items,
)
from config.governance._ml_training import (  # noqa: F401
    ML_TRAINING_COLLECTION_SPEC,
    TRAINING_FIELD_SPECS,
    TRAINING_RUNS_COLLECTION,
    TRAINING_SECTIONS,
)

__all__ = [
    "DEFAULT_ESTIMATORS", "ESTIMATOR_LIST", "ML_APPLICATION_QUESTIONS",
    "ML_APPLICATION_QUESTION_LIST", "ML_TRAINING_LISTS", "ML_TRAINING_VOCABULARIES",
    "ML_APPLICATION_COLLECTION_SPECS", "ML_APPLICATION_EDITABLE_FIELDS",
    "ML_APPLICATION_FIELD_CHOICES", "ML_APPLICATION_FIELD_SPECS",
    "ML_APPLICATION_ID_PREFIX", "ML_APPLICATION_REGISTER_FIELDS",
    "ML_APPLICATION_REGISTER_OPTIONAL",
    "ML_REVIEW_QUESTIONS_COLLECTION", "ML_TRAINING_COLLECTION_SPEC",
    "TRAINING_FIELD_SPECS", "TRAINING_RUNS_COLLECTION", "TRAINING_SECTIONS",
    "DEFAULT_ITEM_POLICY", "ML_REVIEW_ITEM_SOURCES", "ML_REVIEW_POLICY_AGGREGATE",
    "ML_REVIEW_POLICY_NOUN", "QUESTION_GROUP_KEY", "QUESTION_GROUP_LABEL",
    "QUESTION_ITEM_SOURCE", "TRAINING_ITEM_SOURCE", "default_review_policy",
    "item_group_labels", "policy_item_id", "resolve_item", "split_item_id",
    "training_policy_items",
]
