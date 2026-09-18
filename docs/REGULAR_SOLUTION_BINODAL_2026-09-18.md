# Adding coexistence to the model's phase-diagram guide

*AI-assisted derivation and verification note, 18 September 2026. This is a Bragg–Williams approximation, not an exact 2D Ising diagram or a Fe–Cr phase diagram. The student should rederive it before using it in submitted work.*

The existing [spinodal figure](../figures/fig_regular_solution_spinodal.png) shows where the symmetric regular-solution free energy loses **local** convexity. It cannot tell whether a composition just outside that curve is stable as one phase or is metastable with respect to separation. The new [binodal-and-spinodal figure](../figures/fig_regular_solution_binodal_spinodal.png) adds the **coexistence** boundary. This is the thermodynamic distinction behind a useful materials-science question; it is not a new physical law or a classifier of the simulation's microscopic mechanism.

## Derivation in the code's reduced units

For the square lattice mapped to a symmetric regular solution, `Ω=4(Jx+Jy)` and `c=(1+m)/2`. With `k_B=1` in the code,

`f(c,T)=T[c ln c+(1-c)ln(1-c)]+Ωc(1-c)`.

Symmetry gives `f(c,T)=f(1-c,T)`. A common tangent joining coexistence compositions `c` and `1-c` therefore has zero slope. Setting `f'(c,T)=T ln[c/(1-c)]+Ω(1-2c)=0` yields

`T_b(c)=Ω(1-2c)/ln[(1-c)/c]`, with its continuous value `T_b(1/2)=Ω/2`.

The already implemented spinodal is `T_s(c)=2Ωc(1-c)`. For `Jx=Jy=1`, `Ω=8` and both curves meet at mean-field `T=4` when `c=1/2`. This is **not** the exact 2D square-Ising critical value `T_c≈2.269` used to set the simulation's `0.65T_c` quench. The common-tangent construction and the binodal/spinodal distinction agree with the [University of Kiel thermodynamics teaching note](https://www.tf.uni-kiel.de/matwis/amat/td_kin_i/kap_1/backbone/r_se76.html); the repository derives the curve in its own coupling convention.

The formula was not accepted from appearance alone. `tests/test_physics_invariants.py` checks the critical and zero-temperature limits and, across 24 off-centre compositions, verifies equal free energies at `c` and `1-c`, zero chemical-potential slope, positive local curvature at coexistence, and a binodal temperature above the spinodal. The generated figure was visually inspected. These are algebra/implementation checks, not experimental validation.

## What the approximate map says at the actual isotropic finish temperature

The isotropic quench finishes at `0.65×2.269≈1.475` in reduced units:

| `c` | `T_s(c)` | `T_b(c)` | Bragg–Williams classification at `T=1.475` |
|---:|---:|---:|---|
| 0.06 | 0.902 | 2.559 | Between curves: metastable against phase separation in this approximation |
| 0.10 | 1.440 | 2.913 | Between curves; particularly close to the spinodal |
| 0.15 | 2.040 | 3.228 | Below spinodal: locally unstable in this approximation |
| 0.25 | 3.000 | 3.641 | Below spinodal |
| 0.35 | 3.640 | 3.877 | Below spinodal |
| 0.50 | 4.000 | 4.000 | Below the mean-field critical/spinodal temperature |

This classification is **only for the approximate free-energy curve**. It does not prove that the observed off-critical droplets nucleated, nor that the true 2D Ising system has a corresponding sharp dynamical spinodal. It also does not place a real Fe–Cr specimen on a measured phase diagram. [Published Fe–Cr work](https://doi.org/10.1002/adem.202100909) says the spinodal transition line is not firmly established and treats the 20 wt% Cr mechanism cautiously. The simulation's `c` is a site fraction, not the paper's weight percent Cr.

## How to use this without overclaiming

Put both curves in the thermodynamics section to show why **binodal, spinodal and observed morphology are different kinds of evidence**. The main kinetics study at `c=.15` and `.50` lies below this model's mean-field spinodal, while the older `.06`/`.10` composition sweep is between its two curves. Keep all fits in Monte Carlo sweeps and lattice sites. Any real-alloy comparison belongs in a separately sourced discussion, not on the same calibrated axes.
