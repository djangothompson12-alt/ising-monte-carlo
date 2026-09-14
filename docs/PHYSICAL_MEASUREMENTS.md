# Which predictions can be tested outside the simulation?

## Ready for a first physical test: isolated tennis strings

`experiments/string_lab.py` predicts frequency in hertz from measured load,
loaded span and mass per unit length. After checking the fundamental, it can
infer force in newtons and compare it with an independent load measurement.
The protocol specifies new validation specimens and prospective analysis.
That is a testable mechanical model, **separate** from the Ising model.

The next experiment can ask whether the estimate tracks force relaxation at
fixed length. That needs a force gauge/load cell and a safe rig. Sound alone
does not independently validate an acoustic estimate.

## Useful now in the Ising work: dimensionless comparisons

The code measures directional correlation lengths, interface fractions,
morphology and effective growth exponents. A real image dataset could support
a comparison of similarly defined, normalised observables, but only after
matching the measurement method. A scattering peak wavelength is not the same
observable as a half-height correlation length. A 2D microscope section of a
3D material is not automatically a 2D physical system.

Ask an academic or industry contact for a public sequence of microstructure
images with scale, ageing times, composition, temperature, measurement method
and reuse permission. Agree the observable first. A single attractive image
or similar exponent is not validation. Image edges are generally not periodic;
the simulation's periodic cluster labels cannot simply be applied to microscopy
without adapting boundary handling.

## Not yet justified: Monte Carlo sweeps to Fe–Cr ageing hours

Choosing a lattice spacing only converts sites to a labelled length. A literature
diffusion coefficient alone does not establish how a Kawasaki sweep maps onto
physical time. The exchanges have no calibrated attempt frequency, vacancy
mechanism or composition-dependent physical mobility.

A defensible calibration would need a defined composition convention and
temperature, source values with validity ranges, and a justified coarse-graining
length. State whether sites represent atoms or coarse cells. Measure model
mobility for the same state and move rule. Match the energy/interfacial scale
consistently: a 2D interface is a line, unlike a 3D interface area. Finally,
separate calibration and validation datasets using the same observable, and
report model discrepancy as well as input uncertainty.

The [Xu et al. study](https://link.springer.com/article/10.1007/s11661-016-3800-4)
motivates careful measurement, but does not supply a clock for this simulator.
Its table uses weight percent, so alloy 35Cr is not matched to model c=0.35.
No numerical Fe–Cr time/length calibration has been implemented or claimed.

Ask a reviewer whether such a calibration is worth attempting or whether a
bounded dimensionless comparison would be more useful. The tennis experiment
can proceed independently while that question is reviewed.
