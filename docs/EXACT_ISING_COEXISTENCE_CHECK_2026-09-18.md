# Exact 2D coexistence check for the phase-diagram section

*AI-assisted technical note, 18 September 2026. This checks the model against
known theory; it is not a new result, a real-alloy phase diagram, or prose to
paste into a student-authored paper without checking it.*

## Why this check matters

Our [regular-solution diagram](REGULAR_SOLUTION_BINODAL_2026-09-18.md) is a
Bragg–Williams approximation. It gets the distinction between coexistence
and local instability across, but its critical temperature is `4` for
`Jx=Jy=1`; the actual infinite square-lattice critical temperature is
`2/ln(1+sqrt(2)) ≈ 2.269`. We can therefore benchmark its **coexistence**
boundary against the known exact 2D result. Do not treat its spinodal as an
exact property of the Kawasaki lattice.

[Yang (1952)](https://doi.org/10.1103/PhysRev.85.808) first published the
exact spontaneous-magnetisation derivation. [Baxter's research/historical
analysis](https://arxiv.org/abs/1103.3347) gives the anisotropic form in a
readable equation (his Eqs. 2.1–2.2). [Pleimling and Selke (2000)](https://arxiv.org/pdf/cond-mat/0001178)
apply the isotropic formula to a **fixed-magnetisation 2D Ising lattice** and
explicitly identify it as the thermodynamic-limit coexistence boundary.
These are the sources to read before using this comparison in the report.

## Formula and interpretation

In the code's reduced units (`k_B=1`), for positive nearest-neighbour
couplings and `T<Tc`, define

`q(T) = [sinh(2Jx/T) sinh(2Jy/T)]^(-1)`.

The exact spontaneous magnetisation is `m0(T) = [1-q(T)^2]^(1/8)`; it is zero
at and above the exact `Tc`, defined by `sinh(2Jx/Tc)sinh(2Jy/Tc)=1`.
For the lattice-gas composition `c=(1+m)/2`, the two bulk coexisting
compositions are `c_low=(1-m0)/2` and `c_high=(1+m0)/2`. Thus an overall
fixed composition between them favours two-phase equilibrium **in the
thermodynamic limit**. That is an equilibrium statement, not a prediction
that a finite simulation has finished separating.

At the study's isotropic finish, `T=0.65Tc≈1.474970`, the formula gives
`m0≈0.987888`, `c_low≈0.006056` and `c_high≈0.993944`. All six previously
studied overall fractions (`0.06, 0.10, 0.15, 0.25, 0.35, 0.50`) fall between
those exact coexistence compositions. The central `0.15` and `0.50` extension
also does. **This does not label them all spinodally unstable**, nor does it
show whether droplets formed by nucleation or by another path.

| Overall `c` | Exact coexistence boundary `T` at this `c` | Mean-field binodal `T` | Mean-field spinodal `T` |
|---:|---:|---:|---:|
| 0.06 | 2.078 | 2.559 | 0.902 |
| 0.10 | 2.188 | 2.913 | 1.440 |
| 0.15 | 2.242 | 3.228 | 2.040 |
| 0.25 | 2.267 | 3.641 | 3.000 |
| 0.35 | 2.269 | 3.877 | 3.640 |

The exact-boundary column was obtained by numerically solving
`c_low(T)=c`, *not* by fitting simulation trajectories. At `c=.5`, the
exact boundary is the critical point `2.269`, versus mean field `4.000`.
See [the comparison figure](../figures/fig_exact_vs_meanfield_coexistence.png).

As an optional **equilibrium** lever-rule calculation, if bulk phases had
reached `c_low` and `c_high`, their high-composition area fraction would be
`phi=(c-c_low)/(c_high-c_low)`. At overall `c=.15`, this gives `phi≈0.146`.
It is not a measurement of droplet area, a guarantee of a particular shape,
or a fitted model parameter. In finite lattices, interfaces, thermal clusters,
droplet/stripe transitions and incomplete ageing complicate this simple
thermodynamic picture; [Pleimling and Selke](https://arxiv.org/pdf/cond-mat/0001178)
document finite-size effects even in their equilibrium study.

## What this changes in the report

- Call the orange/blue curves **regular-solution approximations**. Their
  metastable/unstable labels apply only to that free-energy approximation.
- Use the green curve as an exact infinite-lattice **coexistence boundary for
  the toy 2D Ising model**, not as an exact spinodal or an alloy phase diagram.
- State that the dilute compositions are inside the exact two-phase region at
  the final temperature, while *how* the finite system gets there remains a
  kinetic question. Do not equate the Yang coexistence result with a measured
  Kawasaki growth exponent.
- Keep `0.65Tc` tied to the exact `Tc` used by the engine. Do not substitute
  `0.65×4` from the mean-field guide.
- If comparing with Fe–Cr or another alloy, use independently measured
  thermodynamics and kinetic calibration. The exact solution is exact for
  this simplified lattice, **not** for Fe–Cr.

`tests/test_physics_invariants.py` checks the zero/critical-temperature
limits, a numerical benchmark at `0.65Tc`, symmetry under swapping `Jx,Jy`,
and mass balance. The figure was inspected visually. These checks test the
implementation of established theory, not the accuracy of the engine's
finite-time coarsening data.

## Questions for the student to answer before external review

1. Why can the mean-field `Tc=4` and exact `Tc≈2.269` both appear in this
   project without contradiction?
2. Why does being between `c_low` and `c_high` at the finish temperature
   establish an equilibrium two-phase preference but not a nucleation route?
3. How would you tell an engineer what this exact 2D curve cannot say about
   a real, three-dimensional Fe–Cr specimen?
