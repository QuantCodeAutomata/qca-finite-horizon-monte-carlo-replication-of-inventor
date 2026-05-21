"""
Infinite-horizon stationary reservation prices (paper's auxiliary model).

Custom — Context7 found no library equivalent (paper-specific closed-form
formulas for stationary indifference reservation prices under discounted
exponential utility).

Formulas:
    r^a_bar(s,q) = s + (1/gamma) * ln(1 + (1 - 2q)*gamma^2*sigma^2 / (2*omega - gamma^2 q^2 sigma^2))
    r^b_bar(s,q) = s + (1/gamma) * ln(1 + (-1 - 2q)*gamma^2*sigma^2 / (2*omega - gamma^2 q^2 sigma^2))

Admissibility: omega > 0.5 * gamma^2 * sigma^2 * q^2 for every inventory q used.
Natural choice with inventory bound q_max: omega = 0.5 * gamma^2 * sigma^2 * (q_max+1)^2.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class StationaryParams:
    sigma: float = 2.0
    gamma: float = 0.1
    q_max: int = 10
    omega: float | None = None  # if None, use the natural choice

    @property
    def omega_value(self) -> float:
        if self.omega is not None:
            return float(self.omega)
        return 0.5 * self.gamma**2 * self.sigma**2 * (self.q_max + 1) ** 2


def admissibility(q: np.ndarray, params: StationaryParams) -> np.ndarray:
    """Return boolean array indicating omega > 0.5*gamma^2*sigma^2*q^2."""
    threshold = 0.5 * params.gamma**2 * params.sigma**2 * q**2
    return params.omega_value > threshold


def stationary_log_arguments(
    q: np.ndarray, params: StationaryParams
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (denom, arg_a, arg_b) used inside the stationary log formulas."""
    g, sig = params.gamma, params.sigma
    omega = params.omega_value
    denom = 2.0 * omega - g**2 * q**2 * sig**2
    arg_a = 1.0 + (1.0 - 2.0 * q) * g**2 * sig**2 / denom
    arg_b = 1.0 + (-1.0 - 2.0 * q) * g**2 * sig**2 / denom
    return denom, arg_a, arg_b


def stationary_reservation_prices(
    s: float, q: np.ndarray, params: StationaryParams
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute (r^a_bar, r^b_bar) over an inventory grid q.

    Admissibility (denom > 0) is asserted for every q. The log-domain restriction
    (arg > 0) only holds strictly in the *interior* |q| < q_max for the natural
    omega choice: at q = +q_max the bid argument vanishes (r^b -> -inf) and at
    q = -q_max the ask argument vanishes (r^a -> +inf). We return NaN at those
    boundaries rather than raise, so callers can still inspect the interior grid.
    """
    g = params.gamma
    denom, arg_a, arg_b = stationary_log_arguments(q, params)
    assert np.all(denom > 0), "Admissibility violated: 2*omega - gamma^2*q^2*sigma^2 must be > 0"
    with np.errstate(divide="ignore", invalid="ignore"):
        ra = np.where(arg_a > 0, s + (1.0 / g) * np.log(np.clip(arg_a, 1e-300, None)), np.nan)
        rb = np.where(arg_b > 0, s + (1.0 / g) * np.log(np.clip(arg_b, 1e-300, None)), np.nan)
    return ra, rb
