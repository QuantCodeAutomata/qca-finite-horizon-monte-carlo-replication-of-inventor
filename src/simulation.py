"""
Discrete Monte Carlo simulation engine for the paper's finite-horizon LOB model.

Custom — Context7 found no library equivalent (paper-specific discrete event
LOB simulation; vectorbt operates on price series with signals, not on LOB
event arrivals).

Mechanics (exactly as the paper states for the simulation section):
    * Mid-price update: S_{t+dt} = S_t +/- sigma*sqrt(dt), each with prob 0.5
    * Ask/bid execution arrivals: independent Bernoulli with prob lambda*dt
    * On ask fill: q -> q-1, X -> X + (S_t + delta^a)
    * On bid fill: q -> q+1, X -> X - (S_t - delta^b)
    * Both fills in a single step are permitted (logged for diagnostics)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

import numpy as np

from .strategies import (
    ModelParams,
    intensity_exponential,
    inventory_quote_distances,
    reservation_price,
    symmetric_quote_distances_constant,
    symmetric_quote_distances_full,
)


@dataclass
class SimulationConfig:
    """Configuration for a single Monte Carlo run."""

    S0: float = 100.0
    q0: float = 0.0
    x0: float = 0.0
    dt: float = 0.005
    n_paths: int = 1000
    seed: Optional[int] = 42


@dataclass
class SimulationResult:
    """Aggregated terminal results and diagnostics across paths."""

    terminal_profit: np.ndarray
    terminal_inventory: np.ndarray
    avg_realized_spread: float
    diagnostics: Dict[str, float] = field(default_factory=dict)

    def summary(self) -> Dict[str, float]:
        """Return paper-style summary statistics."""
        return {
            "mean_profit": float(np.mean(self.terminal_profit)),
            "std_profit": float(np.std(self.terminal_profit, ddof=1)),
            "mean_final_q": float(np.mean(self.terminal_inventory)),
            "std_final_q": float(np.std(self.terminal_inventory, ddof=1)),
            "avg_spread": float(self.avg_realized_spread),
            **self.diagnostics,
        }


# Strategy function signature: (q_array, t_scalar, params) -> (delta_a, delta_b)
StrategyFn = Callable[[np.ndarray, float, ModelParams], Tuple[np.ndarray, np.ndarray]]


def inventory_strategy(
    q: np.ndarray, t: float, params: ModelParams
) -> Tuple[np.ndarray, np.ndarray]:
    """Inventory-based strategy quote distances (vectorised over paths)."""
    return inventory_quote_distances(q, t, params)


def symmetric_full_strategy(
    q: np.ndarray, t: float, params: ModelParams
) -> Tuple[np.ndarray, np.ndarray]:
    """Symmetric Variant A — full time-dependent spread, centred on mid."""
    a, b = symmetric_quote_distances_full(t, params)
    n = q.shape[0]
    return np.full(n, a), np.full(n, b)


def symmetric_constant_strategy(
    q: np.ndarray, t: float, params: ModelParams
) -> Tuple[np.ndarray, np.ndarray]:
    """Symmetric Variant B — constant liquidity component only."""
    a, b = symmetric_quote_distances_constant(t, params)
    n = q.shape[0]
    return np.full(n, a), np.full(n, b)


def simulate_paths(
    strategy: StrategyFn,
    params: ModelParams,
    cfg: SimulationConfig,
    record_one_path: bool = False,
) -> Tuple[SimulationResult, Optional[Dict[str, np.ndarray]]]:
    """Run Monte Carlo simulation in vectorised fashion across paths.

    Parameters
    ----------
    strategy
        Function (q, t, params) -> (delta_a, delta_b), vectorised over paths.
    params
        Model parameters.
    cfg
        Simulation configuration including seed and number of paths.
    record_one_path
        If True, additionally returns full time series of path index 0 for plotting.

    Returns
    -------
    result : SimulationResult
    sample_path : optional dict with keys t, S, r, p_a, p_b, q, X for path 0.
    """
    assert cfg.n_paths > 0, "n_paths must be positive"
    assert cfg.dt > 0, "dt must be positive"

    rng = np.random.default_rng(cfg.seed)
    n_steps = int(round(params.T / cfg.dt))
    sqrt_dt_sigma = params.sigma * np.sqrt(cfg.dt)

    N = cfg.n_paths
    S = np.full(N, cfg.S0, dtype=np.float64)
    q = np.full(N, cfg.q0, dtype=np.float64)
    X = np.full(N, cfg.x0, dtype=np.float64)

    # Diagnostics
    n_simul_fills = 0
    n_neg_distance = 0
    n_lambda_exceed = 0
    delta_min = np.inf
    delta_max = -np.inf
    spread_accum = 0.0  # average realised total quoted spread
    spread_count = 0

    sample = None
    if record_one_path:
        sample = {
            "t": np.zeros(n_steps + 1),
            "S": np.zeros(n_steps + 1),
            "r": np.zeros(n_steps + 1),
            "p_a": np.zeros(n_steps + 1),
            "p_b": np.zeros(n_steps + 1),
            "q": np.zeros(n_steps + 1),
            "X": np.zeros(n_steps + 1),
            "delta_a": np.zeros(n_steps + 1),
            "delta_b": np.zeros(n_steps + 1),
        }

    t = 0.0
    for step in range(n_steps):
        delta_a, delta_b = strategy(q, t, params)

        # Diagnostics on quote distances
        if isinstance(delta_a, np.ndarray):
            da_min, da_max = float(delta_a.min()), float(delta_a.max())
            db_min, db_max = float(delta_b.min()), float(delta_b.max())
            delta_min = min(delta_min, da_min, db_min)
            delta_max = max(delta_max, da_max, db_max)
            n_neg_distance += int(np.sum(delta_a < 0) + np.sum(delta_b < 0))
        else:
            delta_min = min(delta_min, float(delta_a), float(delta_b))
            delta_max = max(delta_max, float(delta_a), float(delta_b))
            if delta_a < 0:
                n_neg_distance += N
            if delta_b < 0:
                n_neg_distance += N

        # Track realised spread (average across paths at this step)
        spread_accum += float(np.mean(delta_a + delta_b))
        spread_count += 1

        # Intensities and Bernoulli execution probabilities
        lam_a = intensity_exponential(delta_a, params)
        lam_b = intensity_exponential(delta_b, params)
        p_a_event = lam_a * cfg.dt
        p_b_event = lam_b * cfg.dt
        n_lambda_exceed += int(np.sum(p_a_event > 1.0) + np.sum(p_b_event > 1.0))
        # Note: the paper does not clip; Bernoulli with p>1 is invalid, just logged.
        p_a_event = np.clip(p_a_event, 0.0, 1.0)
        p_b_event = np.clip(p_b_event, 0.0, 1.0)

        u_a = rng.random(N)
        u_b = rng.random(N)
        fill_a = u_a < p_a_event
        fill_b = u_b < p_b_event
        n_simul_fills += int(np.sum(fill_a & fill_b))

        # Record sample path step (pre-execution quotes for clarity)
        if record_one_path:
            sample["t"][step] = t
            sample["S"][step] = S[0]
            sample["r"][step] = reservation_price(S[0], q[0], t, params)
            da0 = float(delta_a[0] if isinstance(delta_a, np.ndarray) else delta_a)
            db0 = float(delta_b[0] if isinstance(delta_b, np.ndarray) else delta_b)
            sample["delta_a"][step] = da0
            sample["delta_b"][step] = db0
            sample["p_a"][step] = S[0] + da0
            sample["p_b"][step] = S[0] - db0
            sample["q"][step] = q[0]
            sample["X"][step] = X[0]

        # Apply executions: ask fill -> sell one share at p_a = S + delta_a
        # bid fill -> buy one share at p_b = S - delta_b
        if isinstance(delta_a, np.ndarray):
            X = X + fill_a * (S + delta_a) - fill_b * (S - delta_b)
        else:
            X = X + fill_a * (S + delta_a) - fill_b * (S - delta_b)
        q = q + fill_b.astype(np.float64) - fill_a.astype(np.float64)

        # Mid-price update: +/- sigma*sqrt(dt) with equal probability
        z = rng.integers(0, 2, size=N) * 2 - 1  # +/- 1
        S = S + z * sqrt_dt_sigma

        t += cfg.dt

    # Final recording at terminal time
    if record_one_path:
        sample["t"][n_steps] = t
        sample["S"][n_steps] = S[0]
        sample["r"][n_steps] = reservation_price(S[0], q[0], t, params)
        delta_a_T, delta_b_T = strategy(q, t, params)
        da0 = float(delta_a_T[0] if isinstance(delta_a_T, np.ndarray) else delta_a_T)
        db0 = float(delta_b_T[0] if isinstance(delta_b_T, np.ndarray) else delta_b_T)
        sample["delta_a"][n_steps] = da0
        sample["delta_b"][n_steps] = db0
        sample["p_a"][n_steps] = S[0] + da0
        sample["p_b"][n_steps] = S[0] - db0
        sample["q"][n_steps] = q[0]
        sample["X"][n_steps] = X[0]

    profit = X + q * S  # terminal mark-to-market
    avg_spread = spread_accum / max(spread_count, 1)

    diagnostics = {
        "n_simultaneous_fills": float(n_simul_fills),
        "n_negative_distance_events": float(n_neg_distance),
        "n_lambda_dt_exceeds_one": float(n_lambda_exceed),
        "delta_min": float(delta_min),
        "delta_max": float(delta_max),
        "inv_min": float(np.min(q)),
        "inv_max": float(np.max(q)),
    }
    result = SimulationResult(
        terminal_profit=profit,
        terminal_inventory=q,
        avg_realized_spread=avg_spread,
        diagnostics=diagnostics,
    )
    return result, sample
