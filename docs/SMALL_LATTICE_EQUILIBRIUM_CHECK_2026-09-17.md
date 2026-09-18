# A small exact check of the Kawasaki update rule

**AI-assisted verification note, 17 September 2026.** This checks equilibrium
behaviour in a tiny canonical sector. It is not a coarsening result, external
validation or a new materials prediction.

For a periodic 3×3 lattice with exactly four +1 spins, there are
`choose(9,4)=126` possible configurations. The new deterministic test
`tests/test_exact_small_lattice_balance.py` enumerates every one of them.
With anisotropic couplings `Jx=0.7`, `Jy=1.3` and inverse temperature
`β=0.4`, it builds the single-attempt nearest-neighbour exchange transition
matrix. For every proposed unequal-spin exchange it independently computes
the full before/after Hamiltonian and checks the engine's local energy-change
formula. The rows sum to one, and the exact fixed-composition Boltzmann
weights satisfy detailed balance and stationarity to absolute tolerance
`1e-14`. This is a check of the implemented *rule* at small size, not a proof
of finite-run sampling or the late-stage growth law.

A separate diagnostic actually runs the Numba sampler from three independent
seeds, with 2,000 burn-in sweeps and 4,000 energy samples per seed separated
by ten sweeps. The exact energy mean from all 126 configurations is
`−2.733913`; the sampled mean is `−2.731433`, a difference of `+0.002480`.
The estimated standard error of the mean from 100-sample batches is `0.02409`.
The pre-set screening tolerance was the larger of five such standard errors
and `0.03`, so this diagnostic passed. All sampled configurations retained
four +1 spins. The source hashes, seed-specific means and exact setup are in
`output/small_lattice_sampling_2026-09-17_v1.json` and the rerunnable code is
`research/check_small_lattice_sampling.py`.

The batch estimate is only a diagnostic of finite sampled trajectories; it
does not cover autocorrelation perfectly or establish the distribution at
all temperatures and compositions. These checks strengthen confidence in
the local exchange bookkeeping and basic equilibrium behaviour. They do not
decide whether a correlation half-height is an appropriate domain length,
whether a large quench has reached asymptotic coarsening, or how Monte Carlo
sweeps relate to real alloy ageing time.
