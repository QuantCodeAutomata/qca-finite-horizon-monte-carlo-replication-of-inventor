"""
Quote-placement strategies for the finite-horizon Avellaneda-Stoikov model.

Custom — Context7 found no library equivalent (paper's closed-form quote formulas
are model-specific; no skfolio/pyportfolioopt/vectorbt equivalent exists).

References (paper notation):
    delta^a_t = (1/gamma) * ln(1 + gamma/k) + ((1 - 2 q_t) gamma sigma^2 (T - t)) / 2
    delta^b_t = (1/gamma) * ln(1 + gamma/k) + ((1 + 2 q_t) gamma sigma^2 (T - t)) / 2
    r(s, q, t) = s - q gamma sigma^2 (T - t)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class ModelParams:
    """Container for the model parameters used by all quoting strategies."""

    sigma: float = 2.0
    gamma: float = 0.1
    k: float = 1.5
    A: float = 140.0
    T: float = 1.0

    def __post_init__(self) -> None:
        assert self.sigma > 0, "sigma must be positive"
        assert self.gamma > 0, "gamma must be positive"
        assert self.k > 0, "k must be positive"
        assert self.A > 0, "A must be positive"
        assert self.T > 0, "T must be positive"


def reservation_price(
    s: float | np.ndarray,
    q: float | np.ndarray,
    t: float,
    params: ModelParams,
) -> float | np.ndarray:
    """Finite-horizon reservation price r(s,q,t) = s - q*gamma*sigma^2*(T-t)."""
    return s - q * params.gamma * params.sigma**2 * (params.T - t)


def inventory_quote_distances(
    q: float | np.ndarray,
    t: float,
    params: ModelParams,
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    """Inventory-based ask/bid distances delta^a, delta^b (paper's closed-form)."""
    g, sig, k, T = params.gamma, params.sigma, params.k, params.T
    liq = math.log(1.0 + g / k) / g  # constant liquidity component (1/gamma)*ln(1+gamma/k)
    risk = g * sig**2 * (T - t)
    delta_a = liq + (1.0 - 2.0 * q) * risk / 2.0
    delta_b = liq + (1.0 + 2.0 * q) * risk / 2.0
    return delta_a, delta_b


def symmetric_quote_distances_full(
    t: float, params: ModelParams
) -> Tuple[float, float]:
    """Variant A: full time-dependent spread, centred on mid-price.

    delta^{a,sym} = delta^{b,sym} = 0.5 * (gamma*sigma^2*(T-t) + (2/gamma)*ln(1+gamma/k)).
    """
    g, sig, k, T = params.gamma, params.sigma, params.k, params.T
    half = 0.5 * (g * sig**2 * (T - t) + (2.0 / g) * math.log(1.0 + g / k))
    return half, half


def symmetric_quote_distances_constant(
    t: float, params: ModelParams
) -> Tuple[float, float]:
    """Variant B: constant liquidity component only (matches paper's reported spread)."""
    g, k = params.gamma, params.k
    half = (1.0 / g) * math.log(1.0 + g / k)
    return half, half


def total_spread_inventory(t: float, params: ModelParams) -> float:
    """Closed-form identity: delta^a + delta^b = gamma*sigma^2*(T-t) + (2/gamma)*ln(1+gamma/k)."""
    g, sig, k, T = params.gamma, params.sigma, params.k, params.T
    return g * sig**2 * (T - t) + (2.0 / g) * math.log(1.0 + g / k)


def intensity_exponential(delta: float | np.ndarray, params: ModelParams) -> float | np.ndarray:
    """Exponential execution intensity lambda(delta) = A * exp(-k * delta)."""
    return params.A * np.exp(-params.k * delta)
