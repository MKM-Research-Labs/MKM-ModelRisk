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
"""Estimators and ML Application vocabulary (coding rule R1).

Two admin-managed lists, both seeded and both the adopter's to curate.

``ESTIMATOR_LIST`` is the menu of off-the-shelf ML engines. One row per source +
estimator -- scikit-learn's ``GradientBoostingRegressor`` is one row, XGBoost's
``XGBRegressor`` another -- carrying the versions available for it. NOT one row per
version: that is a cartesian product which grows without bound and leaves each row
meaning nothing on its own. An ML Application picks the row and then the version,
so the menu lives here and the choice lives on the record.

``source`` is a field rather than an assumption. Production gradient boosting is
more often XGBoost or LightGBM than scikit-learn's own implementation, and
regression is frequently statsmodels or R, so an estate hardcoded to one library
would be wrong on its first day. It is deliberately NOT the ``vendor`` list: a
vendor is a firm with a contract and due diligence behind it, and an open-source
library is not that.

``versions`` and ``notes`` seed EMPTY on purpose. The estimator names are
universal and we can state them; which versions an institution actually runs is a
fact about their environment, and seeding our guesses would put releases in their
register that nothing in their estate uses.

``ML_APPLICATION_QUESTION_LIST`` is the ML questionnaire, parallel to
``REVIEW_QUESTION_LIST`` and deliberately not shared with it: an ML Application is
asked different questions, and the two sets have to move independently. Same
mechanism, same copy-at-registration snapshot, different content.
"""
from __future__ import annotations

ESTIMATOR_LIST = "estimator"
ML_APPLICATION_QUESTION_LIST = "ml_application_questions"

# The menu of industry norms, seeded on a fresh install. Scope is classical /
# statistical ML -- regression and the learning families around it. LLMs and
# agentic AI are out of scope by design and are not to be added here.
DEFAULT_ESTIMATORS = (
    {"value": "LinearRegression", "source": "scikit-learn", "notes": "Ordinary least squares."},
    {"value": "LogisticRegression", "source": "scikit-learn", "notes": "Binary / multinomial classification."},
    {"value": "Ridge", "source": "scikit-learn", "notes": "L2-penalised linear regression."},
    {"value": "Lasso", "source": "scikit-learn", "notes": "L1-penalised; performs feature selection."},
    {"value": "ElasticNet", "source": "scikit-learn", "notes": "Combined L1/L2 penalty."},
    {"value": "DecisionTreeRegressor", "source": "scikit-learn", "notes": "Single tree; interpretable, high variance."},
    {"value": "RandomForestRegressor", "source": "scikit-learn", "notes": "Bagged trees, regression."},
    {"value": "RandomForestClassifier", "source": "scikit-learn", "notes": "Bagged trees, classification."},
    {"value": "GradientBoostingRegressor", "source": "scikit-learn", "notes": "Boosted trees, regression."},
    {"value": "GradientBoostingClassifier", "source": "scikit-learn", "notes": "Boosted trees, classification."},
    {"value": "HistGradientBoostingRegressor", "source": "scikit-learn", "notes": "Histogram-based boosting for larger data."},
    {"value": "XGBRegressor", "source": "XGBoost", "notes": "Gradient boosting, regression."},
    {"value": "XGBClassifier", "source": "XGBoost", "notes": "Gradient boosting, classification."},
    {"value": "LGBMRegressor", "source": "LightGBM", "notes": "Leaf-wise boosting, regression."},
    {"value": "LGBMClassifier", "source": "LightGBM", "notes": "Leaf-wise boosting, classification."},
    {"value": "OLS", "source": "statsmodels", "notes": "Least squares with inference diagnostics."},
    {"value": "GLM", "source": "statsmodels", "notes": "Generalised linear models."},
    {"value": "Logit", "source": "statsmodels", "notes": "Logistic regression with inference diagnostics."},
)

# The ML questionnaire seeded on a fresh install. Ten rather than nine: SR 26-2 has
# nine because SR 26-2 has nine, and padding or truncating a questionnaire an
# assessor reads closely is worse than an uneven count. An adopter rewords these,
# drops what does not apply and adds its own, exactly as with the SR 26-2 set.
#
# On performance: the question deliberately says "against which metric" rather than
# naming one. Area under the curve is a CLASSIFICATION metric; a regression model
# has RMSE, MAE and R-squared, and half this estate is regression.
ML_APPLICATION_QUESTIONS = (
    {"short_label": "Use Case",
     "question": "What decision does this model inform, and what is it explicitly not to be used for?"},
    {"short_label": "Algorithm Choice",
     "question": "Why this estimator rather than a simpler or alternative one?"},
    {"short_label": "Training Data",
     "question": "What was it trained on, over what period, and is that population still representative?"},
    {"short_label": "Data Leakage",
     "question": "Could any feature encode information that would not be available at prediction time?"},
    {"short_label": "Out-of-Sample Performance",
     "question": "How does it perform on data it was not trained on, and against which metric?"},
    {"short_label": "Benchmarking",
     "question": "How does it compare with a simple baseline a reviewer would recognise?"},
    {"short_label": "Overfitting and Stability",
     "question": "How were hyperparameters selected, and how stable is performance across resamples and over time?"},
    {"short_label": "Explainability",
     "question": "Can an individual prediction be explained to someone affected by it?"},
    {"short_label": "Drift and Monitoring",
     "question": "What would show that it has stopped working, and who is watching for it?"},
    {"short_label": "Weaknesses and Misinterpretation",
     "question": "Where does it fail, and how might its output be misread by a consumer?"},
)

# Both lists follow the shapes already established in _reference.py: ``display`` is
# what a dropdown shows and what a record stores, so the estimator name is the key.
# Estimator names are distinctive across libraries in practice (GradientBoostingRegressor
# is scikit-learn's, XGBRegressor is XGBoost's), so the name alone identifies a row.
ML_REFERENCE_SPECS = {
    ESTIMATOR_LIST: {"label": "Estimator", "id_prefix": "EST", "display": "value", "fields": [
        {"key": "value", "label": "Estimator", "type": "text", "required": True},
        {"key": "source", "label": "Source", "type": "text", "required": True},
        {"key": "versions", "label": "Available versions (comma-separated)", "type": "text"},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]},
    # Same shape as REVIEW_QUESTION_LIST -- ``short_label`` is the topic shown in bold
    # above the question, exactly as a record's own copy renders it.
    ML_APPLICATION_QUESTION_LIST: {"label": "ML Application questions", "id_prefix": "MLQ",
                                   "display": "short_label", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text", "required": True},
        {"key": "question", "label": "Question", "type": "textarea", "required": True},
    ]},
}

ML_REFERENCE_LISTS = (ESTIMATOR_LIST, ML_APPLICATION_QUESTION_LIST)
