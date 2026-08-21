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
"""Collect what a fit knows about itself and post it once, on exit."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import urllib.request
from typing import Any

DEFAULT_URL = os.environ.get("MODELRISK_URL", "http://127.0.0.1:5015")
TOKEN_HEADER = os.environ.get("INGEST_TOKEN_HEADER", "X-Ingest-Token")
TOKEN = os.environ.get("MODELRISK_INGEST_TOKEN", "")
PRODUCER_VERSION = "1.0"


def _commit() -> str:
    """The exact code. A branch name is not a version, so this is the SHA or nothing."""
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, timeout=5)
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                               text=True, timeout=5)
        if sha.returncode:
            return ""
        # A dirty tree is reported as such: a commit that does not describe what ran
        # is worse than no commit, because it looks like it does.
        return sha.stdout.strip() + (" (uncommitted changes)" if dirty.stdout.strip() else "")
    except Exception:
        return ""


def _environment() -> str:
    """Library versions. A scikit-learn or TensorFlow minor release can change
    estimator behaviour without your code changing at all."""
    out = [f"python {platform.python_version()}"]
    for name in ("sklearn", "xgboost", "lightgbm", "statsmodels", "numpy", "pandas",
                 "tensorflow", "torch"):
        try:
            module = __import__(name)
            out.append(f"{name} {getattr(module, '__version__', '?')}")
        except Exception:
            continue
    return ", ".join(out)


class TrainingRun:
    """One fit, collecting what it knows and posting it once."""

    def __init__(self, ml_application_id: str, fit_id: str, url: str = DEFAULT_URL):
        self.ml_application_id = ml_application_id
        self.fit_id = fit_id
        self.url = url.rstrip("/")
        self.fields: dict[str, Any] = {}
        self._started = time.time()

    # --- what the owner's code tells us -------------------------------------
    def data(self, **kw) -> "TrainingRun":
        """Snapshot, row and feature counts, and how the data was prepared."""
        self.fields.update(kw)
        return self

    def split(self, method: str, proportions: str = "", **kw) -> "TrainingRun":
        self.fields.update({"split_method": method, "split_proportions": proportions, **kw})
        return self

    def fit(self, estimator: Any = None, seed: Any = None, **kw) -> "TrainingRun":
        """Hyperparameters AS FITTED, taken off the estimator rather than from the
        call site: the defaults you did not pass are still the values it ran with."""
        if estimator is not None and hasattr(estimator, "get_params"):
            try:
                self.fields["hyperparameters"] = json.dumps(
                    {k: str(v) for k, v in estimator.get_params().items()}, sort_keys=True)
            except Exception:
                pass
        if seed is not None:
            self.fields["random_seed"] = str(seed)
        self.fields.update(kw)
        return self

    def score(self, metric: str, train: Any = None, cv: Any = None,
              test: Any = None, **kw) -> "TrainingRun":
        """The three numbers, not one. The train-test gap IS the overfitting evidence."""
        self.fields["primary_metric"] = metric
        for key, value in (("metric_train", train), ("metric_cv", cv), ("metric_test", test)):
            if value is not None:
                self.fields[key] = str(value)
        self.fields.update(kw)
        return self

    # --- posting -------------------------------------------------------------
    def _collect(self) -> dict[str, Any]:
        gathered = dict(self.fields)
        gathered.setdefault("code_commit", _commit())
        gathered.setdefault("environment", _environment())
        gathered.setdefault("run_hardware", platform.platform())
        gathered.setdefault("run_duration", f"{time.time() - self._started:.1f}s")
        gathered.setdefault("run_date", time.strftime("%Y-%m-%d"))
        return {k: v for k, v in gathered.items() if v not in (None, "")}

    def _provenance(self) -> dict[str, Any]:
        """Stamped on every stored event: it is the audit trail for a value nobody
        typed, and the answer to "where did this number come from?"."""
        return {
            "source_repo": os.environ.get("MODELRISK_SOURCE_REPO", os.path.basename(os.getcwd())),
            "commit": _commit().split(" ")[0] or "unknown",
            "producer": "modelrisk/capture",
            "producer_version": PRODUCER_VERSION,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def post(self) -> dict[str, Any]:
        body = {
            "schema_version": "v1",
            "artifact": "ml-training-run",
            "provenance": self._provenance(),
            "payload": {"ml_application_id": self.ml_application_id,
                        "fit_id": self.fit_id, "fields": self._collect()},
        }
        headers = {"Content-Type": "application/json"}
        if TOKEN:
            headers[TOKEN_HEADER] = TOKEN
        request = urllib.request.Request(
            f"{self.url}/api/ingest/ml-training-run",
            data=json.dumps(body).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def __enter__(self) -> "TrainingRun":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Posts even when the fit raised: a fit that fell over is a fact about the
        # fit, and a train recorded as incomplete beats one nobody knows happened.
        # A failure to post never masks the original exception.
        try:
            self.post()
        except Exception:
            if exc_type is None:
                raise
        return False


def capture(ml_application_id: str, fit_id: str, url: str = DEFAULT_URL) -> TrainingRun:
    return TrainingRun(ml_application_id, fit_id, url)
