"""Unit tests for src/strategies.py — paper-formula adherence."""
import math

import numpy as np
import pytest

from src.strategies import (
    ModelParams,
    intensity_exponential,
    inventory_quote_distances,
    reservation_price,
    symmetric_quote_distances_constant,
    symmetric_quote_distances_full,
    total_spread_inventory,
)


@pytest.fixture
def params() -> ModelParams:
    return ModelParams(sigma=2.0, gamma=0.1, k=1.5, A=140.0, T=1.0)


def test_reservation_price_formula(params):
    """r(s,q,t) = s - q*gamma*sigma^2*(T-t)."""
    s, q, t = 100.0, 3.0, 0.4
    expected = s - q * params.gamma * params.sigma**2 * (params.T - t)
    assert math.isclose(reservation_price(s, q, t, params), expected)


def test_reservation_price_at_terminal(params):
    """r -> s at t = T."""
    s, q = 100.0, 5.0
    assert math.isclose(reservation_price(s, q, params.T, params), s)


def test_inventory_distances_spread_identity(params):
    """delta^a + delta^b = gamma*sigma^2*(T-t) + (2/gamma)*ln(1+gamma/k)."""
    for q in (-5.0, -1.0, 0.0, 2.0, 7.0):
        for t in (0.0, 0.3, 0.7, 1.0):
            da, db = inventory_quote_distances(q, t, params)
            assert math.isclose(da + db, total_spread_inventory(t, params), rel_tol=1e-12)


def test_inventory_quote_midpoint_equals_reservation(params):
    """(p^a + p^b)/2 = r(s,q,t)."""
    s = 100.0
    for q in (-3.0, 0.0, 4.0):
        for t in (0.0, 0.5, 0.99):
            da, db = inventory_quote_distances(q, t, params)
            mid = (s + da + s - db) / 2.0
            assert math.isclose(mid, reservation_price(s, q, t, params), rel_tol=1e-12)


def test_symmetric_full_centered_on_mid(params):
    """Variant A: delta_a == delta_b (centred on S_t)."""
    for t in (0.0, 0.4, 1.0):
        da, db = symmetric_quote_distances_full(t, params)
        assert math.isclose(da, db)


def test_symmetric_constant_matches_paper_spread():
    """Variant B total spread equals (2/gamma)*ln(1+gamma/k) at all t."""
    for gamma in (0.01, 0.1, 0.5):
        p = ModelParams(sigma=2.0, gamma=gamma, k=1.5, A=140.0, T=1.0)
        da, db = symmetric_quote_distances_constant(0.5, p)
        expected = (2 / gamma) * math.log(1 + gamma / 1.5)
        assert math.isclose(da + db, expected, rel_tol=1e-12)


def test_paper_spread_values_match_constant_formula():
    """Paper reports 1.33, 1.29, 1.15 for gamma = 0.01, 0.1, 0.5."""
    expected = {0.01: 1.33, 0.1: 1.29, 0.5: 1.15}
    for gamma, paper_val in expected.items():
        val = (2 / gamma) * math.log(1 + gamma / 1.5)
        assert abs(val - paper_val) < 0.01, f"gamma={gamma}: {val:.4f} vs paper {paper_val}"


def test_intensity_decreasing_in_delta(params):
    """lambda(delta) = A*exp(-k*delta) is strictly decreasing."""
    deltas = np.array([0.1, 0.5, 1.0, 2.0])
    lams = intensity_exponential(deltas, params)
    assert np.all(np.diff(lams) < 0)
    assert math.isclose(lams[0], params.A * math.exp(-params.k * 0.1))


def test_small_gamma_convergence_to_symmetric():
    """For small gamma, inventory and symmetric strategies should agree."""
    gamma = 1e-4
    p = ModelParams(sigma=2.0, gamma=gamma, k=1.5, A=140.0, T=1.0)
    q, t = 0.0, 0.0
    da_inv, db_inv = inventory_quote_distances(q, t, p)
    da_sym, db_sym = symmetric_quote_distances_full(t, p)
    assert math.isclose(da_inv, da_sym, rel_tol=1e-6)
    assert math.isclose(db_inv, db_sym, rel_tol=1e-6)


def test_inventory_skew_sign(params):
    """Positive q -> ask more aggressive (smaller delta^a) than bid."""
    s, t = 100.0, 0.0
    da_pos, db_pos = inventory_quote_distances(5.0, t, params)
    assert da_pos < db_pos
    da_neg, db_neg = inventory_quote_distances(-5.0, t, params)
    assert da_neg > db_neg


def test_model_params_validation():
    with pytest.raises(AssertionError):
        ModelParams(sigma=-1.0)
    with pytest.raises(AssertionError):
        ModelParams(gamma=0.0)
