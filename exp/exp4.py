"""
Experiment 4: Infinite-horizon stationary reservation prices verification.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.stationary import StationaryParams, admissibility, stationary_reservation_prices

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)

GAMMAS = (0.01, 0.1, 0.5)
Q_MAX = 10
S0 = 100.0


def run() -> pd.DataFrame:
    q_grid = np.arange(-Q_MAX, Q_MAX + 1, dtype=float)
    rows = []
    fig, axes = plt.subplots(1, len(GAMMAS), figsize=(15, 4), sharey=False)
    for ax, gamma in zip(axes, GAMMAS):
        params = StationaryParams(sigma=2.0, gamma=gamma, q_max=Q_MAX, omega=None)
        omega = params.omega_value
        ok = admissibility(q_grid, params)
        assert ok.all(), f"Admissibility failed for gamma={gamma}"
        ra, rb = stationary_reservation_prices(S0, q_grid, params)
        for q, a, b in zip(q_grid, ra, rb):
            rows.append({
                "gamma": gamma, "q": int(q), "omega": omega,
                "r_a_bar": float(a), "r_b_bar": float(b),
                "r_a_minus_s": float(a - S0), "s_minus_r_b": float(S0 - b),
                "r_avg": 0.5 * float(a + b),
                "skew_a_minus_b": float(a - b),
            })
        ax.plot(q_grid, ra - S0, "o-", label=r"$\bar r^a - s$")
        ax.plot(q_grid, S0 - rb, "s-", label=r"$s - \bar r^b$")
        ax.set_title(f"γ = {gamma},  ω = {omega:.3g}")
        ax.set_xlabel("Inventory q")
        ax.set_ylabel("Distance from mid")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "exp4_stationary_reservation.png", dpi=140)
    plt.close(fig)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "exp4_stationary_summary.csv", index=False)

    # Sensitivity: vary omega
    sens_rows = []
    gamma = 0.1
    base = 0.5 * gamma**2 * 2.0**2 * (Q_MAX + 1) ** 2
    for mult in (1.0, 2.0, 5.0, 10.0):
        params = StationaryParams(sigma=2.0, gamma=gamma, q_max=Q_MAX, omega=base * mult)
        ra, rb = stationary_reservation_prices(S0, q_grid, params)
        sens_rows.append({
            "omega_mult": mult,
            "omega": params.omega_value,
            "max_abs_skew": float(np.max(np.abs(ra - rb))),
            "max_r_a_minus_s": float(np.max(np.abs(ra - S0))),
        })
    sens_df = pd.DataFrame(sens_rows)
    sens_df.to_csv(RESULTS_DIR / "exp4_omega_sensitivity.csv", index=False)

    return df


if __name__ == "__main__":
    df = run()
    print(df.head(10).to_string(index=False))
