"""
Experiment 1: Finite-horizon Monte Carlo replication.

Inventory-based vs symmetric (Variant A — full time-dependent spread) strategies.
1000 paths per (strategy, gamma) over T=1, dt=0.005, sigma=2, A=140, k=1.5.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Allow running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation import (
    SimulationConfig,
    inventory_strategy,
    simulate_paths,
    symmetric_full_strategy,
)
from src.strategies import ModelParams


GAMMAS = (0.01, 0.1, 0.5)
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def run() -> pd.DataFrame:
    rows = []
    sample_paths = {}
    pnl_distributions = {}
    inv_distributions = {}
    for gamma in GAMMAS:
        params = ModelParams(sigma=2.0, gamma=gamma, k=1.5, A=140.0, T=1.0)
        cfg_inv = SimulationConfig(seed=42, n_paths=1000)
        cfg_sym = SimulationConfig(seed=43, n_paths=1000)

        inv_res, inv_sample = simulate_paths(
            inventory_strategy, params, cfg_inv, record_one_path=True
        )
        sym_res, _ = simulate_paths(symmetric_full_strategy, params, cfg_sym)

        inv_sum = inv_res.summary()
        sym_sum = sym_res.summary()
        rows.append({"gamma": gamma, "strategy": "inventory", **inv_sum})
        rows.append({"gamma": gamma, "strategy": "symmetric_full", **sym_sum})
        sample_paths[gamma] = inv_sample
        pnl_distributions[gamma] = {
            "inventory": inv_res.terminal_profit,
            "symmetric_full": sym_res.terminal_profit,
        }
        inv_distributions[gamma] = {
            "inventory": inv_res.terminal_inventory,
            "symmetric_full": sym_res.terminal_inventory,
        }

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "exp1_summary.csv", index=False)

    _plot_sample_path(sample_paths[0.1], gamma=0.1)
    _plot_pnl_histograms(pnl_distributions)
    _plot_inventory_histograms(inv_distributions)
    return df


def _plot_sample_path(sample, gamma: float) -> None:
    if sample is None:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(sample["t"], sample["S"], label="Mid price S_t", color="black", lw=1)
    ax.plot(sample["t"], sample["r"], label="Reservation price r_t", color="tab:blue", lw=1)
    ax.plot(sample["t"], sample["p_a"], label="Ask quote p^a_t", color="tab:red", lw=0.7, alpha=0.8)
    ax.plot(sample["t"], sample["p_b"], label="Bid quote p^b_t", color="tab:green", lw=0.7, alpha=0.8)
    ax.set_xlabel("Time t")
    ax.set_ylabel("Price")
    ax.set_title(f"Inventory strategy: sample path (gamma={gamma})")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "exp1_sample_path.png", dpi=140)
    plt.close(fig)


def _plot_pnl_histograms(pnl_dist) -> None:
    fig, axes = plt.subplots(1, len(GAMMAS), figsize=(15, 4), sharey=False)
    for ax, gamma in zip(axes, GAMMAS):
        inv = pnl_dist[gamma]["inventory"]
        sym = pnl_dist[gamma]["symmetric_full"]
        bins = 40
        ax.hist(inv, bins=bins, alpha=0.55, label="Inventory", color="tab:blue", density=True)
        ax.hist(sym, bins=bins, alpha=0.55, label="Symmetric (full)", color="tab:orange", density=True)
        ax.set_title(f"Terminal P&L  (gamma={gamma})")
        ax.set_xlabel("Profit")
        ax.set_ylabel("Density")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "exp1_pnl_histograms.png", dpi=140)
    plt.close(fig)


def _plot_inventory_histograms(inv_dist) -> None:
    fig, axes = plt.subplots(1, len(GAMMAS), figsize=(15, 4), sharey=False)
    for ax, gamma in zip(axes, GAMMAS):
        inv = inv_dist[gamma]["inventory"]
        sym = inv_dist[gamma]["symmetric_full"]
        bins = 40
        ax.hist(inv, bins=bins, alpha=0.55, label="Inventory", color="tab:blue", density=True)
        ax.hist(sym, bins=bins, alpha=0.55, label="Symmetric (full)", color="tab:orange", density=True)
        ax.set_title(f"Terminal Inventory  (gamma={gamma})")
        ax.set_xlabel("q_T")
        ax.set_ylabel("Density")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "exp1_inventory_histograms.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    df = run()
    print(df.to_string(index=False))
