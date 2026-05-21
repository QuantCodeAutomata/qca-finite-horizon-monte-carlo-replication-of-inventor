# Repository notes

- Paper: Avellaneda–Stoikov finite-horizon market making, with auxiliary
  infinite-horizon stationary appendix.
- Experiments use **synthetic** data only (no Massive / Yahoo). The `data/`
  directory exists for structural compatibility but stays empty.
- Mid-price simulation follows the paper's *discrete* mechanics:
  `±σ·√dt` Bernoulli increments, not exact Brownian motion.
- Execution arrivals: independent ask/bid Bernoulli with probability `λ·dt`.
- The paper's reported spread column (1.33, 1.29, 1.15 for γ = 0.01, 0.1, 0.5)
  matches `(2/γ)·ln(1+γ/k)` exactly, i.e. the *constant* liquidity component.
  Experiment 2 tests both interpretations.
- `src/` modules are deliberately library-light:
  Context7 confirmed no off-the-shelf library covers this paper's
  closed-form LOB market-making formulas.
- Symbolic verification uses sympy; numerical spot checks use numpy.
