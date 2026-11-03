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
**What this list is NOT.** It is no longer the whole questionnaire an ML Application is
asked. Five questions — use case, human oversight, who could be disadvantaged,
explainability, and what would show it had stopped working — are asked of any
application of a model and live in ``_questions_common.py``; a record is copied those
first and these beneath them. What is left here is what is particular to a fitted estimator, which is the argument this module has always made and now makes
precisely: the PROCESSES stay separate, and the questions that are genuinely the same
question stop being asked twice in two wordings.
"""
from __future__ import annotations

from config.governance._ml_training import (ML_TRAINING_LISTS, ML_TRAINING_VOCABULARIES)
from config.governance._vocabulary import status_vocabulary_spec

ESTIMATOR_LIST = "estimator"
# The features an ML Application is fitted on, as a register rather than a vocabulary:
# each entry is a thing with properties -- what type it is, where it comes from, how it
# is derived -- not a word with a label.
#
# It earns its keep beyond A.4's dropdown. A feature used by several ML Applications is
# the ML estate's version of "two models share a data source", and the same
# correlated-failure question follows from it: a feature that turns out to be wrong, or
# to have leaked, is wrong everywhere it is used at once. That question is only
# askable if the uses are recorded against one entry rather than typed into fifty.
FEATURE_LIST = "feature"
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

# The ML questionnaire seeded on a fresh install: these seven, asked after the five
# common questions (_questions_common.py), so twelve in all. Twelve rather than
# nine: SR 26-2 has nine because SR 26-2 has nine, and padding or truncating a
# questionnaire an assessor reads closely is worse than an uneven count. An adopter
# rewords these, drops what does not apply and adds its own, exactly as with the
# SR 26-2 set.
#
# On performance: the question deliberately says "against which metric" rather than
# naming one. Area under the curve is a CLASSIFICATION metric; a regression model
# has RMSE, MAE and R-squared, and half this estate is regression.
ML_APPLICATION_QUESTIONS = (
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
    {"short_label": "Weaknesses and Misinterpretation",
     "question": "Where does it fail, and how might its output be misread by a consumer?"},
)

# Both lists follow the shapes already established in _reference.py: ``display`` is
# what a dropdown shows and what a record stores, so the estimator name is the key.
# Estimator names are distinctive across libraries in practice (GradientBoostingRegressor
# is scikit-learn's, XGBRegressor is XGBoost's), so the name alone identifies a row.
FEATURE_TYPES = ("Numeric", "Categorical", "Boolean", "Datetime", "Text", "Derived")

ML_REFERENCE_SPECS = {
    ESTIMATOR_LIST: {"label": "Estimator", "id_prefix": "EST", "display": "value", "fields": [
        {"key": "value", "label": "Estimator", "type": "text", "required": True},
        {"key": "source", "label": "Source", "type": "text", "required": True},
        {"key": "versions", "label": "Available versions (comma-separated)", "type": "text"},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]},
    # Same shape as REVIEW_QUESTION_LIST -- ``short_label`` is the topic shown in bold
    # above the question, exactly as a record's own copy renders it.
    # Not seeded. An institution's features are its own, and a starter list of ours
    # would be somebody else's model described in their register.
    FEATURE_LIST: {"label": "Feature", "id_prefix": "FT", "display": "value", "fields": [
        {"key": "value", "label": "Feature", "type": "text", "required": True},
        {"key": "data_type", "label": "Type", "type": "choice", "options": FEATURE_TYPES},
        {"key": "data_source", "label": "Source", "type": "text", "reference": "data_source"},
        {"key": "derivation", "label": "How it is derived", "type": "textarea"},
    ]},
    ML_APPLICATION_QUESTION_LIST: {"label": "ML Application questions", "id_prefix": "MLQ",
                                   "display": "short_label", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text", "required": True},
        {"key": "question", "label": "Question", "type": "textarea", "required": True},
    ]},
}

# The training enumerations are vocabularies like any other -- stored value, shown
# label, editable in Admin. Folded in here so they reach REFERENCE_SPECS through the
# same merge the Estimator list does.
ML_REFERENCE_SPECS.update({
    name: status_vocabulary_spec(label, prefix, hint)
    for name, (label, prefix, _words, hint) in ML_TRAINING_VOCABULARIES.items()
})

ML_REFERENCE_LISTS = ((ESTIMATOR_LIST, FEATURE_LIST, ML_APPLICATION_QUESTION_LIST)
                      + ML_TRAINING_LISTS)
