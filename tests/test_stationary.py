"""Tests for src/stationary.py."""
import numpy as np
import pytest

from src.stationary import StationaryParams, admissibility, stationary_reservation_prices


def test_admissibility_natural_omega_holds():
    for gamma in (0.01, 0.1, 0.5):
        p = StationaryParams(sigma=2.0, gamma=gamma, q_max=10, omega=None)
        q = np.arange(-10, 11, dtype=float)
        assert admissibility(q, p).all()


def test_admissibility_fails_for_too_small_omega():
    p = StationaryParams(sigma=2.0, gamma=0.5, q_max=10, omega=1e-6)
    q = np.array([10.0])
    assert not admissibility(q, p).any()


def test_stationary_skew_signs():
    """Positive q -> both reservation prices below s; negative q -> above."""
    p = StationaryParams(sigma=2.0, gamma=0.5, q_max=10, omega=None)
    q = np.array([-5.0, 0.0, 5.0])
    ra, rb = stationary_reservation_prices(100.0, q, p)
    # Centre check (q=0): r^a > s > r^b
    assert ra[1] > 100.0 > rb[1]
    # Positive inventory shifts both downward
    assert ra[2] < ra[1] and rb[2] < rb[1]
    # Negative inventory shifts both upward
    assert ra[0] > ra[1] and rb[0] > rb[1]


def test_stationary_monotonicity_in_q():
    """On the interior grid |q| < q_max both stationary reservation prices
    decrease in q (long inventory pushes both ask and bid quotes downward)."""
    p = StationaryParams(sigma=2.0, gamma=0.1, q_max=10, omega=None)
    q = np.arange(-9, 10, dtype=float)  # interior: log-arg strictly positive
    ra, rb = stationary_reservation_prices(100.0, q, p)
    assert np.all(np.isfinite(ra)) and np.all(np.isfinite(rb))
    assert np.all(np.diff(ra) < 0)
    assert np.all(np.diff(rb) < 0)


def test_stationary_raises_on_bad_omega():
    p = StationaryParams(sigma=2.0, gamma=0.5, q_max=10, omega=1e-9)
    q = np.array([10.0])
    with pytest.raises(AssertionError):
        stationary_reservation_prices(100.0, q, p)


def test_larger_omega_dampens_skew():
    """Larger omega reduces inventory-driven quote skew (interior grid)."""
    base = StationaryParams(sigma=2.0, gamma=0.1, q_max=10, omega=None)
    big = StationaryParams(sigma=2.0, gamma=0.1, q_max=10, omega=base.omega_value * 10)
    q = np.arange(-9, 10, dtype=float)
    ra1, rb1 = stationary_reservation_prices(100.0, q, base)
    ra2, rb2 = stationary_reservation_prices(100.0, q, big)
    assert np.nanmax(np.abs(ra1 - rb1)) > np.nanmax(np.abs(ra2 - rb2))
