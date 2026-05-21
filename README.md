# Avellaneda–Stoikov Finite-Horizon Market-Making Replication

Replication of the inventory-based versus symmetric market-making comparison
from the finite-horizon Avellaneda–Stoikov framework, plus three companion
experiments covering spread-ambiguity sensitivity, analytical verification of
the finite-horizon theory, and the auxiliary infinite-horizon stationary model.

## Structure

```
.
├── data/                # (empty — experiments use synthetic simulated data only)
├── src/
│   ├── strategies.py    # Quote-placement closed-form formulas
│   ├── simulation.py    # Discrete vectorised Monte Carlo engine
│   ├── theory.py        # Sympy/numerical verification of finite-horizon theory
│   └── stationary.py    # Infinite-horizon stationary reservation prices
├── exp/
│   ├── exp1.py          # Main MC replication (inventory vs symmetric full)
│   ├── exp2.py          # Symmetric-benchmark spread ambiguity sensitivity
│   ├── exp3.py          # Analytical verification of finite-horizon theory
│   ├── exp4.py          # Infinite-horizon stationary model verification
│   └── run_all.py       # Executes all four and assembles results/RESULTS.md
├── tests/               # pytest suites for src and exp adherence
└── results/             # Output tables, plots, RESULTS.md
```

## Reproduction

```bash
pip install -r requirements.txt
pytest -q
python -m exp.run_all
```

Outputs are written under `results/`:
- `exp1_summary.csv`, `exp1_sample_path.png`, `exp1_pnl_histograms.png`,
  `exp1_inventory_histograms.png`
- `exp2_summary.csv`, `exp2_spread_comparison.png`
- `exp3_spot_checks.csv`, `exp3_quote_distances.png`, `exp3_report.md`
- `exp4_stationary_summary.csv`, `exp4_omega_sensitivity.csv`,
  `exp4_stationary_reservation.png`
- `RESULTS.md` — consolidated findings

## Model parameters

- Mid-price: `S0 = 100`, `sigma = 2`, discrete `±sigma·√dt` moves
- Horizon: `T = 1`, `dt = 0.005` (200 steps)
- Execution intensity: `λ(δ) = A·exp(-k·δ)` with `A = 140`, `k = 1.5`
- Risk aversion: `γ ∈ {0.01, 0.1, 0.5}`
- 1000 Monte Carlo paths per (strategy, γ)

## Key formulas

```
r(s,q,t)   = s − q·γ·σ²·(T−t)
δ_a(q,t)   = (1/γ)·ln(1 + γ/k) + ((1 − 2q)·γ·σ²·(T−t))/2
δ_b(q,t)   = (1/γ)·ln(1 + γ/k) + ((1 + 2q)·γ·σ²·(T−t))/2
spread     = γ·σ²·(T−t) + (2/γ)·ln(1 + γ/k)
```

The symmetric benchmark has two interpretations tested in Experiment 2:
- Variant A (full time-dependent): `δ = ½·spread`
- Variant B (constant component): `δ = (1/γ)·ln(1+γ/k)` — matches the paper's
  reported spread numbers (1.33, 1.29, 1.15 for γ = 0.01, 0.1, 0.5).
