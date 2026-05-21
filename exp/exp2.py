"""
Experiment 2: Symmetric-benchmark spread ambiguity sensitivity.

Compare two symmetric-benchmark variants against the unchanged inventory strategy:
    * Variant A: full time-dependent spread = 0.5*(gamma*sigma^2*(T-t) + (2/gamma)*ln(1+gamma/k))
    * Variant B: constant liquidity component = (1/gamma)*ln(1+gamma/k)
Match average realised spread to paper's reported numbers (1.33, 1.29, 1.15 for
gamma = 0.01, 0.1, 0.5 respectively under formula (2/gamma)*ln(1+gamma/k)).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation import (
    SimulationConfig,
    inventory_strategy,
    simulate_paths,
    symmetric_constant_strategy,
    symmetric_full_strategy,
)
from src.strategies import ModelParams

GAMMAS = (0.01, 0.1, 0.5)
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def paper_reported_constant_spread(gamma: float, k: float = 1.5) -> float:
    """The paper's reported spread column equals (2/gamma)*ln(1+gamma/k)."""
    return (2.0 / gamma) * math.log(1.0 + gamma / k)


def run() -> pd.DataFrame:
    rows = []
    for gamma in GAMMAS:
        params = ModelParams(sigma=2.0, gamma=gamma, k=1.5, A=140.0, T=1.0)
        # Common random numbers across the three strategies (same seed)
        seed = 1000 + int(gamma * 10000)
        cfg = SimulationConfig(seed=seed, n_paths=1000)

        inv_res, _ = simulate_paths(inventory_strategy, params, cfg)
        symA_res, _ = simulate_paths(symmetric_full_strategy, params, cfg)
        symB_res, _ = simulate_paths(symmetric_constant_strategy, params, cfg)

        for name, res in (
            ("inventory", inv_res),
            ("symmetric_full_A", symA_res),
            ("symmetric_constant_B", symB_res),
        ):
            s = res.summary()
            rows.append({
                "gamma": gamma,
                "strategy": name,
                "paper_reported_spread": paper_reported_constant_spread(gamma),
                **s,
            })

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "exp2_summary.csv", index=False)
    _plot_spread_comparison(df)
    return df


def _plot_spread_comparison(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.25
    gammas = sorted(df["gamma"].unique())
    x = np.arange(len(gammas))
    for i, name in enumerate(("inventory", "symmetric_full_A", "symmetric_constant_B")):
        sub = df[df["strategy"] == name].sort_values("gamma")
        ax.bar(x + (i - 1) * width, sub["avg_spread"].values, width, label=name)
    # overlay paper reported
    paper_vals = [paper_reported_constant_spread(g) for g in gammas]
    ax.plot(x, paper_vals, "k*", markersize=14, label="Paper reported spread (2/γ)ln(1+γ/k)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"γ={g}" for g in gammas])
    ax.set_ylabel("Average realised quoted spread")
    ax.set_title("Spread comparison: Variant A vs Variant B vs paper-reported")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "exp2_spread_comparison.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    df = run()
    print(df.to_string(index=False))
