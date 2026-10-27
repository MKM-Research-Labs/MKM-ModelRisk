"""GEV tail-event pilot: scipy vs independent 50-digit closed form, plus Wolfram oracles.

Convention: standard climatological GEV with shape xi (xi > 0 Frechet / heavy tail).
    F(x) = exp(-(1 + xi*(x - mu)/sigma)^(-1/xi)),  xi != 0
    F(x) = exp(-exp(-(x - mu)/sigma)),            xi == 0
scipy.stats.genextreme uses c = -xi (sign flipped), a frequent source of error.
Wolfram MaxStableDistribution[mu, sigma, xi] uses the same sign as xi here.
"""
import json
import mpmath as mp
import numpy as np
from scipy.stats import genextreme

mp.mp.dps = 50

CASES = {
    "gumbel": (100.0, 20.0, 0.0),
    "frechet_moderate": (100.0, 20.0, 0.2),
    "frechet_heavy": (100.0, 20.0, 0.5),
    "weibull_bounded": (100.0, 20.0, -0.2),
    "near_zero_shape": (100.0, 20.0, 1e-9),
}
RETURN_PERIODS = [10, 100, 200, 1000, 10000]


def return_level_ref(mu, sigma, xi, T):
    """Exact return level at 50 digits: x_T = F^-1(1 - 1/T)."""
    mu, sigma, xi = mp.mpf(mu), mp.mpf(sigma), mp.mpf(xi)
    y = -mp.log(1 - 1 / mp.mpf(T))  # reduced variate, precise for large T
    if xi == 0:
        return mu - sigma * mp.log(y)
    return mu + sigma / xi * mp.expm1(-xi * mp.log(y))


def return_level_scipy(mu, sigma, xi, T):
    return float(genextreme.isf(1.0 / T, -xi, loc=mu, scale=sigma))


def run():
    rows = []
    for name, (mu, sigma, xi) in CASES.items():
        for T in RETURN_PERIODS:
            ref = return_level_ref(mu, sigma, xi, T)
            sp = return_level_scipy(mu, sigma, xi, T)
            rel = abs((mp.mpf(sp) - ref) / ref)
            rows.append({
                "case": name, "mu": mu, "sigma": sigma, "xi": xi, "T": T,
                "ref_50dp": mp.nstr(ref, 20), "scipy": repr(sp),
                "rel_err": float(rel),
                "wolfram": (f"N[Quantile[MaxStableDistribution[{mu}, {sigma}, {xi}], "
                            f"1 - 1/{T}], 20]" if xi != 0 else
                            f"N[Quantile[GumbelDistribution[{mu}, {sigma}], 1 - 1/{T}], 20]"),
            })
    # sign-convention trap: what you get if xi is passed straight into scipy
    mu, sigma, xi = CASES["frechet_moderate"]
    trap = {
        "correct_c=-xi": return_level_scipy(mu, sigma, xi, 1000),
        "wrong_c=+xi": float(genextreme.isf(1e-3, xi, loc=mu, scale=sigma)),
    }
    return rows, trap


if __name__ == "__main__":
    rows, trap = run()
    print(f"{'case':18}{'T':>7}{'reference (20 sf)':>26}{'scipy':>22}{'rel err':>11}")
    for r in rows:
        print(f"{r['case']:18}{r['T']:>7}{r['ref_50dp']:>26}{float(r['scipy']):>22.12f}{r['rel_err']:>11.1e}")
    print("\nSign trap, 1-in-1000 level for xi=0.2:", trap)
    worst = max(rows, key=lambda r: r["rel_err"])
    print(f"Worst scipy rel err: {worst['rel_err']:.2e} ({worst['case']}, T={worst['T']})")
    with open("gev_pilot_oracles.json", "w") as f:
        json.dump(rows, f, indent=1)
