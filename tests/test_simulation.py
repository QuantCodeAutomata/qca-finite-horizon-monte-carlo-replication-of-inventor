"""Unit tests for the Monte Carlo simulation engine."""
import numpy as np
import pytest

from src.simulation import (
    SimulationConfig,
    inventory_strategy,
    simulate_paths,
    symmetric_constant_strategy,
    symmetric_full_strategy,
)
from src.strategies import ModelParams


@pytest.fixture
def small_params():
    return ModelParams(sigma=2.0, gamma=0.1, k=1.5, A=140.0, T=1.0)


def test_simulate_basic_shapes(small_params):
    cfg = SimulationConfig(seed=0, n_paths=50)
    res, sample = simulate_paths(inventory_strategy, small_params, cfg, record_one_path=True)
    assert res.terminal_profit.shape == (50,)
    assert res.terminal_inventory.shape == (50,)
    assert sample is not None
    n_steps = int(round(small_params.T / cfg.dt))
    assert sample["t"].shape == (n_steps + 1,)


def test_reproducibility(small_params):
    cfg = SimulationConfig(seed=7, n_paths=100)
    r1, _ = simulate_paths(inventory_strategy, small_params, cfg)
    r2, _ = simulate_paths(inventory_strategy, small_params, cfg)
    np.testing.assert_allclose(r1.terminal_profit, r2.terminal_profit)
    np.testing.assert_allclose(r1.terminal_inventory, r2.terminal_inventory)


def test_lambda_dt_violation_is_logged(small_params):
    """The paper allows the Bernoulli approximation but requires logging
    violations of lambda*dt > 1; verify the diagnostic counter exists."""
    cfg = SimulationConfig(seed=1, n_paths=200)
    res, _ = simulate_paths(inventory_strategy, small_params, cfg)
    assert "n_lambda_dt_exceeds_one" in res.diagnostics
    # symmetric_constant variant has constant spread => no violations possible
    res2, _ = simulate_paths(symmetric_constant_strategy, small_params, cfg)
    assert res2.diagnostics["n_lambda_dt_exceeds_one"] == 0


def test_inventory_strategy_controls_inventory_variance(small_params):
    """Paper claim: inventory strategy has lower std(final q) than symmetric."""
    cfg_inv = SimulationConfig(seed=42, n_paths=500)
    cfg_sym = SimulationConfig(seed=43, n_paths=500)
    inv, _ = simulate_paths(inventory_strategy, small_params, cfg_inv)
    sym, _ = simulate_paths(symmetric_full_strategy, small_params, cfg_sym)
    std_inv = np.std(inv.terminal_inventory, ddof=1)
    std_sym = np.std(sym.terminal_inventory, ddof=1)
    assert std_inv < std_sym, f"std_inv={std_inv:.2f} >= std_sym={std_sym:.2f}"


def test_inventory_strategy_lower_pnl_variance(small_params):
    """Paper claim: inventory strategy reduces terminal P&L variance."""
    cfg_inv = SimulationConfig(seed=100, n_paths=500)
    cfg_sym = SimulationConfig(seed=101, n_paths=500)
    inv, _ = simulate_paths(inventory_strategy, small_params, cfg_inv)
    sym, _ = simulate_paths(symmetric_full_strategy, small_params, cfg_sym)
    std_inv = np.std(inv.terminal_profit, ddof=1)
    std_sym = np.std(sym.terminal_profit, ddof=1)
    assert std_inv < std_sym


def test_summary_keys(small_params):
    cfg = SimulationConfig(seed=2, n_paths=30)
    res, _ = simulate_paths(symmetric_constant_strategy, small_params, cfg)
    summary = res.summary()
    for k in ("mean_profit", "std_profit", "mean_final_q", "std_final_q", "avg_spread"):
        assert k in summary
    assert summary["std_profit"] >= 0
    assert summary["std_final_q"] >= 0


def test_avg_spread_constant_variant_matches_formula():
    import math
    for gamma in (0.01, 0.1, 0.5):
        p = ModelParams(sigma=2.0, gamma=gamma, k=1.5, A=140.0, T=1.0)
        cfg = SimulationConfig(seed=11, n_paths=20)
        res, _ = simulate_paths(symmetric_constant_strategy, p, cfg)
        expected = (2 / gamma) * math.log(1 + gamma / 1.5)
        assert abs(res.avg_realized_spread - expected) < 1e-10


def test_edge_case_single_path(small_params):
    cfg = SimulationConfig(seed=5, n_paths=1)
    res, sample = simulate_paths(inventory_strategy, small_params, cfg, record_one_path=True)
    assert res.terminal_profit.shape == (1,)
    assert np.isfinite(res.terminal_profit[0])
    assert sample is not None
