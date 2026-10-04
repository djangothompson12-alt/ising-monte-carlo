# Academic challenge audit: time windows, length definitions and the real question

**AI-assisted working audit, 22 September 2026.** This document is designed to
make the study harder to overclaim. It is not a systematic review, proof of
novelty or student-approved manuscript text.

## Bottom-line verdict

Low sweep counts are not intrinsically better for measuring a growth law. They
are useful for measuring early transients and for stress-testing how an image
operator changes a finite-window fit. Very late measurements are not
intrinsically better either: once domains become a substantial fraction of the
box, finite-size saturation can flatten the curve and reduce the number of
independent domains. An asymptotic growth-law claim needs evidence for an
intermediate scaling regime between those limits.

The completed project does not yet identify that regime uniquely. It has
strong evidence that fitted effective exponents change with window, box size,
observable and observation operator. Those are legitimate findings if they are
reported as a measurement audit rather than as a new universal exponent.

## Why each current time window exists

| Window | Defensible purpose | What it cannot establish |
|---|---|---|
| 1,000–20,000 sweeps | A frozen early finite-window benchmark used by the new-seed image-operation test. All compared operators use the same snapshots and time mask. | Late-stage or asymptotic growth. The start at 1,000 has not independently been established as the onset of dynamical scaling. |
| 1,000–200,000 sweeps | A broad comparison with the earlier campaign and a test of sensitivity to including early data. | A pure power-law regime if initial-length and transient effects remain. |
| 20,000–1,000,000 sweeps | A later long-span measurement on the completed multi-size extension. At L=128 it moves the symmetric estimate towards one third. | Freedom from finite-size effects, or proof of an exponent from one observable. |
| 1,000–4,500,000 and 200,000–4,500,000 sweeps | Predeclared windows for the separate 40-run, T=0.6Tc, L=128 paper-inspired comparison. They provide long time spans and separate a broad fit from a later-start fit. | The source paper's multi-size finite-size collapse; only one lattice size is present. |

The short image benchmark should therefore be described as an **early
finite-window metrology test**, not as the main estimate of the physical growth
law.

## What would justify a scaling window

A specialist could reasonably expect several checks rather than a convenient
start and end time:

1. The choice is fixed before inspecting which exponent it produces.
2. The domain scale is larger than microscopic/interface-noise scales.
3. The measured length remains well below its box-limited value.
4. Large lattice sizes agree at matched times before smaller sizes depart.
5. A local effective exponent becomes approximately stable rather than merely
   increasing across the selected interval.
6. Rescaled correlation functions and structure factors show credible dynamic
   scaling over a declared range.
7. More than one defensible operational length shows compatible long-time
   behaviour, even if their amplitudes differ.
8. Treatment of the nonzero initial length is declared and tested rather than
   fitted until one third appears.

The present project has partial evidence for items 1, 3, 4 and 7. Its candidate
z=3 display is not a demonstrated quantitative collapse, and the exact scaling
onset remains unresolved.

## Questions an academic is likely to ask

| Challenge | Current defensible answer | Remaining weakness / next test |
|---|---|---|
| Why begin at 1,000 sweeps? | It is a frozen comparison boundary that excludes the most microscopic checkpoints and supplies a common image-operator window. | It is not independently proven to be the scaling onset. Show it as a sensitivity boundary, not a physical transition. |
| Why include early data at all? | The research question concerns how finite-window inference and image processing behave in accessible data, where transients matter. | Do not use the result as the asymptotic growth exponent. |
| Why not fit only the latest data? | Late data have fewer independent domains and can be box affected; some late nominal windows also fail the declared fivefold time-span rule. | Use multi-size departure and local-slope diagnostics to identify a late but unsaturated interval. |
| Why use a straight log-log slope? | It is transparent and directly exposes window dependence. | A nonzero initial length biases it. Compare a fixed measured subtraction and the source paper's finite-size formulation without optimising an offset. |
| Why use C(r)=0.5? | It is an explicit, reproducible characteristic length and has precedent in phase-ordering studies. Connected normalisation removes the fixed m^2 background off criticality. | The threshold is operational, not unique. Compare chord, positive-lobe and structure-factor measures on the same trajectories. |
| Why use connected correlation for Model B but not Model A? | Model B conserves m exactly, so m^2 is a constant composition background. Model A's changing m contains real ordering information; changing its historical raw observable would not be a neutral correction. | State that these are deliberately different observables rather than pretending they are directly identical. |
| Why average x and y? | The controlled campaign is isotropic, Jx=Jy=1. Directional values are retained before averaging. | An anisotropic study must analyse directions separately and account for the changed critical temperature. |
| Why majority filtering and chord length? | They provide a paper-inspired comparison to Majumder and Das on a separate matched campaign. | Pass count, simultaneous/sequential filtering and chord weighting are not fully specified in the short paper. Call it paper-inspired until reviewed. |
| Why these lattice sizes? | 32, 64, 96 and 128 permit matched-time size comparisons while the 128 box supplies the longest unsaturated range in the extension. | This is not the same size/replica design as the reference paper, and the smallest boxes lose useful late data. |
| Why 16 or 40 trajectories? | Whole independent trajectories quantify stochastic run-to-run variation; 40 matches the reference paper's stated L=128 ensemble count. | More replicas reduce sampling uncertainty but do not remove systematic observable, window or model uncertainty. |
| Why T=0.65Tc and T=0.6Tc? | The 0.65Tc study is the frozen project campaign; the separate 0.6Tc campaign matches a key reference setting more closely. | Temperature changes mobility and thermal interface noise. Results from the campaigns cannot be merged as if identical. |
| Why 2D? | It is a controlled, computationally accessible universality model with exact equilibrium reference results. | It is not a quantitative model of a 3D alloy, elastic coherency, crystal orientation or dislocations. |
| Why should a materials engineer care? | Real coarsening conclusions depend on how microstructural length and phase geometry are measured; the tool exposes a bounded metrology failure mode. | Genuine usefulness requires an owner-defined real imaging question and external evaluation, not a generic claim about alloys. |

## Research question to take forward

The project should not lead with "why is my exponent below one third?" because
finite-time corrections, finite size and estimator dependence are established
topics. It also should not lead with "thresholding changes the exponent",
which has close experimental and image-metrology prior art.

The strongest bounded question supported by the completed work is:

> **When conserved 2D Kawasaki trajectories are observed through different
> defensible domain-length and image-processing operations, which parts of a
> fitted finite-window growth exponent are stable, and does disagreement
> decrease in a later, predeclared time window before finite-size saturation?**

This has two linked tests:

1. **Physics/measurement convergence:** on the 40-run symmetric T=0.6Tc
   campaign, compare the native connected-correlation half-height with the
   predeclared majority-filtered chord length on identical snapshots and in
   fixed early/broad/later windows.
2. **Materials-image observation control:** on the fresh T=0.65Tc cohort, test
   whether preserving apparent phase fraction after resolution reduction is
   sufficient to preserve a fitted finite-window exponent across bicontinuous
   and droplet morphologies.

The contribution would be an openly reproducible negative/positive benchmark
showing where these measurements agree and fail, not a new growth law. The
novelty remains provisional until a specialist checks the closest literature.

## Evidence that would change the conclusion

- If the two lengths approach a constant ratio and their paired exponent
  difference narrows in later unsaturated windows, that supports convergence
  toward one-scale behaviour without proving one third.
- If their ratio remains time dependent, the fitted exponent difference is
  mathematically expected; investigate morphology/filter effects rather than
  declaring different physical laws.
- If small and large boxes diverge at matched time, finite-size effects are
  implicated for the smaller box.
- If all large boxes drift together while remaining far below one third,
  finite-time, temperature, initial-length or observable effects remain more
  plausible than box size alone.
- If a reviewer identifies equivalent prior work, recast the output as a
  reproducible educational replication and external metrology tool rather than
  an original physics paper.

## Literature boundary used for this audit

- A. J. Bray, *Theory of phase-ordering kinetics*, Advances in Physics 43,
  357–459 (1994), https://doi.org/10.1080/00018739400101505.
- S. Majumder and S. K. Das, *Domain coarsening in two dimensions: conserved
  dynamics and finite-size scaling*, Physical Review E 81, 050102(R) (2010),
  https://doi.org/10.1103/PhysRevE.81.050102.
- S. Majumder and S. K. Das, *Diffusive domain coarsening: early-time dynamics
  and finite-size effects*, Physical Review E 84, 021110 (2011),
  https://arxiv.org/abs/1101.4524.
- S. Majumder and S. K. Das, *Temperature and composition dependence of
  kinetics of phase separation in solid binary mixtures*, PCCP 15 (2013),
  https://arxiv.org/abs/1305.2556.
- Ledesma-Alonso, Barbosa and Ortegón, Physical Review E 97, 023304 (2018),
  https://doi.org/10.1103/PhysRevE.97.023304.

This is a bounded challenge map. It cannot certify originality, and it should
be one of the documents sent to a specialist for criticism.
