"""
Symbolic and numerical verification of the paper's finite-horizon theory.

Custom — Context7 confirms no library implements these utility-indifference /
HJB derivations specific to the Avellaneda-Stoikov paper. We use sympy for the
symbolic checks (Context7-confirmed for symbolic algebra).
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import sympy as sp


def frozen_inventory_value_symbolic() -> Dict[str, sp.Expr]:
    """Derive v(x,s,q,t)=E_t[-exp(-gamma(x+q S_T))] in closed form using sympy.

    Returns a dict with the closed-form value function and the integrand check.
    """
    x, s, q, t, T, sigma, gamma = sp.symbols("x s q t T sigma gamma", real=True, positive=False)
    z = sp.symbols("z", real=True)  # standard normal proxy via integral form

    # S_T = s + sigma*sqrt(T-t)*Z, Z ~ N(0,1)
    # v = E[-exp(-gamma*(x + q*S_T))]
    integrand = -sp.exp(-gamma * (x + q * (s + sigma * sp.sqrt(T - t) * z)))
    pdf = sp.exp(-z**2 / 2) / sp.sqrt(2 * sp.pi)
    v_integral = sp.integrate(integrand * pdf, (z, -sp.oo, sp.oo))
    v_closed = -sp.exp(-gamma * x) * sp.exp(-gamma * q * s) * sp.exp(
        gamma**2 * q**2 * sigma**2 * (T - t) / 2
    )
    diff = sp.simplify(v_integral - v_closed)
    return {"v_integral": v_integral, "v_closed": v_closed, "diff": diff}


def reservation_prices_symbolic() -> Dict[str, sp.Expr]:
    """Solve the indifference equations for r^a and r^b symbolically.

    v(x - r^b, s, q+1, t) = v(x, s, q, t)   ->  r^b
    v(x + r^a, s, q-1, t) = v(x, s, q, t)   ->  r^a
    """
    x, s, q, t, T, sigma, gamma, ra, rb = sp.symbols(
        "x s q t T sigma gamma ra rb", real=True
    )

    def v(xx, ss, qq, tt):
        return -sp.exp(-gamma * xx) * sp.exp(-gamma * qq * ss) * sp.exp(
            gamma**2 * qq**2 * sigma**2 * (T - tt) / 2
        )

    eq_b = sp.Eq(v(x - rb, s, q + 1, t), v(x, s, q, t))
    eq_a = sp.Eq(v(x + ra, s, q - 1, t), v(x, s, q, t))
    sol_b = sp.solve(eq_b, rb)[0]
    sol_a = sp.solve(eq_a, ra)[0]
    r_avg = sp.simplify((sol_a + sol_b) / 2)
    r_expected = s - q * gamma * sigma**2 * (T - t)
    diff_avg = sp.simplify(r_avg - r_expected)

    # Expected closed-form (paper):
    ra_expected = s + (1 - 2 * q) * gamma * sigma**2 * (T - t) / 2
    rb_expected = s + (-1 - 2 * q) * gamma * sigma**2 * (T - t) / 2
    diff_a = sp.simplify(sol_a - ra_expected)
    diff_b = sp.simplify(sol_b - rb_expected)
    return {
        "r_a": sol_a,
        "r_b": sol_b,
        "r_avg": r_avg,
        "diff_avg": diff_avg,
        "diff_a": diff_a,
        "diff_b": diff_b,
    }


def exponential_intensity_foc_symbolic() -> Dict[str, sp.Expr]:
    """Verify FOC simplification for lambda(delta) = A*exp(-k*delta).

    Generic FOC: s - r^b = delta^b - (1/gamma)*ln(1 - gamma*lambda^b/lambda^{b'})
    With exponential intensity, lambda'(delta) = -k*lambda(delta) => -lambda/lambda' = 1/k
    so the log term becomes (1/gamma)*ln(1 + gamma/k), independent of delta.
    """
    delta, gamma, k = sp.symbols("delta gamma k", positive=True)
    A = sp.symbols("A", positive=True)
    lam = A * sp.exp(-k * delta)
    lam_prime = sp.diff(lam, delta)
    # FOC: delta = (s - r^b) + (1/gamma)*ln(1 - gamma*lam/lam_prime)
    # With exponential intensity: lam/lam_prime = -1/k => 1 - gamma*(-1/k) = 1 + gamma/k
    term = (1 / gamma) * sp.log(1 - gamma * lam / lam_prime)
    expected = (1 / gamma) * sp.log(1 + gamma / k)
    # Force log expansion to reach canonical form
    diff = sp.simplify(sp.expand_log(term - expected, force=True))
    return {"foc_term": sp.simplify(term), "expected": expected, "diff": diff}


def numerical_spot_checks(
    s: float = 100.0,
    sigma: float = 2.0,
    k: float = 1.5,
    A: float = 140.0,
    T: float = 1.0,
) -> Dict[str, list]:
    """Numerical spot-checks of identities across q, t, gamma grids."""
    rows = []
    for gamma in (0.01, 0.1, 0.5):
        for q in (-5, -1, 0, 1, 5):
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                liq = np.log(1 + gamma / k) / gamma
                risk = gamma * sigma**2 * (T - t)
                delta_a = liq + (1 - 2 * q) * risk / 2
                delta_b = liq + (1 + 2 * q) * risk / 2
                r = s - q * gamma * sigma**2 * (T - t)
                spread = delta_a + delta_b
                spread_expected = gamma * sigma**2 * (T - t) + (2 / gamma) * np.log(1 + gamma / k)
                p_a = s + delta_a
                p_b = s - delta_b
                quote_mid = (p_a + p_b) / 2
                rows.append({
                    "gamma": gamma, "q": q, "t": t,
                    "delta_a": delta_a, "delta_b": delta_b,
                    "r": r, "spread": spread,
                    "spread_expected": spread_expected,
                    "spread_err": abs(spread - spread_expected),
                    "quote_mid": quote_mid,
                    "midpoint_err": abs(quote_mid - r),
                })
    return rows


def limiting_behaviour_checks(
    s: float = 100.0,
    sigma: float = 2.0,
    k: float = 1.5,
    T: float = 1.0,
) -> Dict[str, float]:
    """Limits: gamma -> 0 should remove reservation-price skew;
    t -> T should make finite-horizon spread collapse to constant component."""
    out = {}
    # Limit gamma -> 0: r -> s
    for gamma in (0.5, 0.1, 0.01, 0.001):
        q = 5
        t = 0.0
        r = s - q * gamma * sigma**2 * (T - t)
        out[f"r_minus_s_at_gamma={gamma}"] = r - s
    # Limit t -> T: time-dependent component vanishes
    gamma = 0.1
    q = 5
    for t in (0.0, 0.5, 0.9, 0.99, 1.0):
        liq = np.log(1 + gamma / k) / gamma
        risk = gamma * sigma**2 * (T - t)
        delta_a = liq + (1 - 2 * q) * risk / 2
        delta_b = liq + (1 + 2 * q) * risk / 2
        out[f"delta_a_at_t={t}"] = delta_a
        out[f"delta_b_at_t={t}"] = delta_b
    return out
