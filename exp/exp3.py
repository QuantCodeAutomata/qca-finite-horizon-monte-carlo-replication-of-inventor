"""
Experiment 3: Analytical verification of finite-horizon theory.

Uses sympy for symbolic verification and numpy for numerical spot checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.theory import (
    exponential_intensity_foc_symbolic,
    frozen_inventory_value_symbolic,
    limiting_behaviour_checks,
    numerical_spot_checks,
    reservation_prices_symbolic,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def run() -> dict:
    out = {}
    # --- 1. Frozen inventory value function ---
    fi = frozen_inventory_value_symbolic()
    diff_simplified = sp.simplify(fi["diff"])
    out["frozen_value_match"] = bool(diff_simplified == 0)
    out["v_closed_form"] = str(fi["v_closed"])

    # --- 2. Reservation prices from indifference ---
    rp = reservation_prices_symbolic()
    out["reservation_a_matches_paper"] = bool(sp.simplify(rp["diff_a"]) == 0)
    out["reservation_b_matches_paper"] = bool(sp.simplify(rp["diff_b"]) == 0)
    out["average_reservation_matches"] = bool(sp.simplify(rp["diff_avg"]) == 0)
    out["r_a_expression"] = str(rp["r_a"])
    out["r_b_expression"] = str(rp["r_b"])
    out["r_average_expression"] = str(rp["r_avg"])

    # --- 3. Exponential intensity FOC simplification ---
    foc = exponential_intensity_foc_symbolic()
    out["foc_term_matches_paper"] = bool(sp.simplify(foc["diff"]) == 0)
    out["foc_term_expression"] = str(foc["foc_term"])

    # --- 4. Numerical spot checks ---
    rows = numerical_spot_checks()
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "exp3_spot_checks.csv", index=False)
    out["max_spread_err"] = float(df["spread_err"].max())
    out["max_midpoint_err"] = float(df["midpoint_err"].max())

    # --- 5. Limiting behaviour ---
    lim = limiting_behaviour_checks()
    out["limits"] = lim

    # --- Plot: quote distances vs t for various q (gamma=0.1) ---
    _plot_quote_distance_curves()

    # Save a markdown report
    with (RESULTS_DIR / "exp3_report.md").open("w") as f:
        f.write("# Experiment 3 — Theoretical Verification\n\n")
        for key, val in out.items():
            if isinstance(val, dict):
                f.write(f"\n## {key}\n\n")
                for k, v in val.items():
                    f.write(f"- {k}: {v}\n")
            else:
                f.write(f"- **{key}**: {val}\n")
    return out


def _plot_quote_distance_curves() -> None:
    sigma, gamma, k, T = 2.0, 0.1, 1.5, 1.0
    ts = np.linspace(0, T, 100)
    fig, ax = plt.subplots(figsize=(9, 5))
    for q in (-3, 0, 3):
        liq = np.log(1 + gamma / k) / gamma
        risk = gamma * sigma**2 * (T - ts)
        delta_a = liq + (1 - 2 * q) * risk / 2
        delta_b = liq + (1 + 2 * q) * risk / 2
        ax.plot(ts, delta_a, label=f"δ^a (q={q})")
        ax.plot(ts, delta_b, "--", label=f"δ^b (q={q})")
    ax.set_xlabel("t")
    ax.set_ylabel("Quote distance")
    ax.set_title("Finite-horizon quote distances vs t (γ=0.1, σ=2, k=1.5)")
    ax.legend(ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "exp3_quote_distances.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    res = run()
    for k, v in res.items():
        print(f"{k}: {v}")
