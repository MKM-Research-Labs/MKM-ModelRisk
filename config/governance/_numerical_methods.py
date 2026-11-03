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
"""The numerical-method catalogue: the off-the-shelf techniques a model is built with.

**Referenced, not governed.** A root-finder, a quadrature rule or a Sobol sequence is
not a model: it has no business purpose and makes no assumption about the world, so
it is never inventoried, validated or signed off in its own right. What IS governed is
how a particular model uses one -- the bump size, the path count, the tolerance -- and
that is the host model's assumption, recorded in its own assumptions and limitations.
This list exists so the model's documentation can name the methods it rests on, and
so "which models use Monte Carlo?" is a match on a defined id rather than on spelling.

Accordingly the model's ``numerical_methods`` collection is exempt from completeness
(an empty one is not a gap), triggers no change classification, and is asked about by
no review question. It appears on the model's Overview and in its dossier, and nowhere
else.

Seeded in families an adopter recognises, and like every other list it seeds a vacuum
and never reconciles a curated one: anything deleted in Admin stays deleted.
"""
from __future__ import annotations

NUMERICAL_METHOD_LIST = "numerical_method"
NUMERICAL_METHODS_COLLECTION = "numerical_methods"

# Families, in the order the seed lists them. A choice rather than free text so the
# catalogue groups cleanly; "Other" is last for the same reason as Data Source's.
NUMERICAL_METHOD_FAMILIES = (
    "Differentiation", "Root finding", "Optimisation", "Integration", "Simulation",
    "PDE / ODE", "Interpolation", "Linear algebra", "Transforms", "Other",
)

# ASCII names on purpose: they are printed into the LaTeX dossier.
_SEED = {
    "Differentiation": (
        ("Finite differences (bump and reprice)", "Sensitivities by perturbing an input and re-pricing."),
        ("Algorithmic differentiation (AAD)", "Exact derivatives propagated through the code."),
    ),
    "Root finding": (
        ("Brent's method", "Bracketed root-finder; robust default for implied quantities."),
        ("Newton-Raphson", "Derivative-based root-finder; fast but needs a good start."),
        ("Bisection", "Bracketed root-finder; slow, guaranteed to converge."),
    ),
    "Optimisation": (
        ("Levenberg-Marquardt", "Non-linear least squares; the usual calibration workhorse."),
        ("BFGS / L-BFGS", "Quasi-Newton minimisation."),
        ("Nelder-Mead", "Derivative-free simplex minimisation."),
        ("Differential evolution", "Global, population-based search."),
    ),
    "Integration": (
        ("Gauss-Legendre quadrature", "Fixed-node quadrature on a finite interval."),
        ("Gauss-Hermite quadrature", "Quadrature against a Gaussian weight."),
        ("Adaptive quadrature", "Error-controlled subdivision (Simpson, Gauss-Kronrod)."),
    ),
    "Simulation": (
        ("Monte Carlo (pseudo-random)", "Path simulation from a pseudo-random generator."),
        ("Quasi-Monte Carlo (Sobol)", "Low-discrepancy sequences in place of random draws."),
        ("Least-squares Monte Carlo", "Regression-based early exercise (Longstaff-Schwartz)."),
        ("Mersenne Twister", "Pseudo-random number generator."),
    ),
    "PDE / ODE": (
        ("Crank-Nicolson finite difference", "Second-order time stepping for diffusion PDEs."),
        ("Explicit / implicit finite difference", "First-order PDE time stepping."),
        ("Runge-Kutta", "ODE integration (RK4 and adaptive variants)."),
        ("Lattice / tree", "Binomial or trinomial tree."),
    ),
    "Interpolation": (
        ("Linear interpolation", "Piecewise linear between nodes."),
        ("Cubic spline", "Smooth piecewise cubic through the nodes."),
        ("Monotone convex (Hagan-West)", "Curve interpolation preserving positive forwards."),
    ),
    "Linear algebra": (
        ("LU decomposition", "General linear solve."),
        ("Cholesky decomposition", "Correlated draws from a positive-definite matrix."),
        ("Singular value decomposition", "Least squares and rank-deficient systems."),
        ("Principal component analysis", "Eigen-decomposition of a covariance matrix."),
    ),
    "Transforms": (
        ("Fast Fourier transform", "Characteristic-function pricing (Carr-Madan, COS)."),
    ),
    "Other": (("Other", ""),),
}

DEFAULT_NUMERICAL_METHODS: tuple[dict[str, str], ...] = tuple(
    {"value": name, "family": family, "notes": notes}
    for family in NUMERICAL_METHOD_FAMILIES for name, notes in _SEED[family]
)

NUMERICAL_REFERENCE_LISTS = (NUMERICAL_METHOD_LIST,)

NUMERICAL_REFERENCE_SPECS = {
    NUMERICAL_METHOD_LIST: {"label": "Numerical Method", "id_prefix": "NM", "display": "value", "fields": [
        {"key": "value", "label": "Method", "type": "text", "required": True},
        {"key": "family", "label": "Family", "type": "choice", "options": NUMERICAL_METHOD_FAMILIES},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]},
}

# One row per method the model uses. ``implementation`` says whose code (SciPy's
# brentq, QuantLib, in-house); ``note`` says where in the model it is used. The
# parameters -- bump size, path count -- are deliberately not here: they are the
# model's assumptions and belong in its assumptions register, where they are governed.
NUMERICAL_METHODS_SPEC = {"label": "Numerical methods", "id_prefix": "NUM", "fields": [
    {"key": "numerical_method", "label": "Method", "type": "text",
     "reference": NUMERICAL_METHOD_LIST, "strict_reference": True, "required": True},
    {"key": "implementation", "label": "Implementation", "type": "text"},
    {"key": "note", "label": "Where it is used", "type": "text"},
]}

__all__ = ["DEFAULT_NUMERICAL_METHODS", "NUMERICAL_METHODS_COLLECTION", "NUMERICAL_METHODS_SPEC",
           "NUMERICAL_METHOD_FAMILIES", "NUMERICAL_METHOD_LIST", "NUMERICAL_REFERENCE_LISTS",
           "NUMERICAL_REFERENCE_SPECS"]
