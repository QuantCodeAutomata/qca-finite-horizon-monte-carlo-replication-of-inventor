"""Tests for src/theory.py — symbolic and numerical verification."""
import sympy as sp

from src.theory import (
    exponential_intensity_foc_symbolic,
    frozen_inventory_value_symbolic,
    limiting_behaviour_checks,
    numerical_spot_checks,
    reservation_prices_symbolic,
)


def test_frozen_inventory_value_matches_paper():
    fi = frozen_inventory_value_symbolic()
    assert sp.simplify(fi["diff"]) == 0


def test_reservation_prices_symbolic():
    rp = reservation_prices_symbolic()
    assert sp.simplify(rp["diff_a"]) == 0
    assert sp.simplify(rp["diff_b"]) == 0
    assert sp.simplify(rp["diff_avg"]) == 0


def test_exponential_intensity_foc():
    foc = exponential_intensity_foc_symbolic()
    assert sp.simplify(foc["diff"]) == 0


def test_numerical_spot_checks_spread_and_midpoint():
    rows = numerical_spot_checks()
    for r in rows:
        assert r["spread_err"] < 1e-10, f"spread mismatch at {r}"
        assert r["midpoint_err"] < 1e-10, f"midpoint mismatch at {r}"


def test_limiting_behaviour_gamma_small():
    lim = limiting_behaviour_checks()
    # r-s should shrink as gamma decreases
    assert abs(lim["r_minus_s_at_gamma=0.001"]) < abs(lim["r_minus_s_at_gamma=0.5"])


def test_limiting_behaviour_t_to_T():
    lim = limiting_behaviour_checks()
    # At t=T, delta^a should equal delta^b (no inventory skew left)
    assert abs(lim["delta_a_at_t=1.0"] - lim["delta_b_at_t=1.0"]) < 1e-10
