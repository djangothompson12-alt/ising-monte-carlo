# Write a paper you can defend

Start with one question: **When can a finite 2D Kawasaki run appear to coarsen
slower because of time/size limits or the way its domains are measured?**
Composition is a controlled comparison, not by itself a novelty claim. Keep
the tennis study separate until it has
its own data and a clear result. The two projects can share a motivation without
claiming to share a physical model.

## A workable paper structure

1. **Question.** Explain phase separation, conservation of composition and why
   a measured short-time exponent need not be the asymptotic exponent. Use a
   real alloy as motivation, not as a claim of calibration.
2. **Model.** State the Hamiltonian, Metropolis acceptance rule, Kawasaki exchange,
   temperature and sweep definitions, lattice geometry and boundary conditions.
3. **Thermodynamics.** Derive the regular-solution map; label the mean-field
   spinodal and distinguish it from the exact 2D critical temperature.
4. **Measurement.** Explain the two correlation definitions and their intentional
   asymmetry. Define threshold length, cluster radius, fits and uncertainties.
5. **Results.** Start with raw trajectories. Then show time-window and lattice-size
   sensitivity, composition and morphology. Compare the symmetric 0.6 Tc
   literature-method benchmark only after its planned runs and method audit are
   complete. Include the connected-correlation and structure-factor scaling
   diagnostic, clearly distinguishing overlap over a narrow range from a full
   collapse. Show the predeclared 0.65 Tc windows and the observation-operator
   reliability map. Report failed or unresolved fits.
6. **Limits.** Separate finite time from finite size; discuss estimator effects,
   2D versus 3D, and why classical 3D LSW is a reference rather than an exact
   distribution for the lattice clusters. Do not claim merger mechanisms from
   a histogram alone.
7. **Conclusion.** Say what was measured, what remains unresolved, and which next
   measurement could settle it. No admissions language in the paper.

Use the current main.tex as working material, not a finished account of your
understanding. Its PDF is stale until LaTeX is rebuilt. The long campaign's
results have not been inserted into the manuscript automatically. See
`docs/FIVE_WORKSTREAMS_STATUS_2026-09-13.md` before writing any result from the
new workstreams: several are protocols or exploratory figures, not completed
evidence. Any future real-image analysis needs owner permission, phase and ROI
review, and comparable ageing metadata first.

## Your first writing session

Without looking at an AI answer, write 150–250 words explaining why exchange
moves conserve composition but spin flips do not. Then explain why a spinodal
is not simply the boundary between “droplets” and “stripes”. List anything you
cannot yet justify. That list is the reading plan; it is not something to hide.

For each central figure, answer:

- What are the axes and units? What is measured rather than fitted?
- Which script and raw file generated it? Which seed or ensemble?
- What would the figure look like if the explanation were wrong?
- What uncertainty is shown, and what uncertainty is missing?
- What is the strongest claim the figure does **not** support?

Your strongest material is the work you can walk someone through: a bug caught,
an assumption checked, a prediction that failed and a revision that followed.
Do not add technical vocabulary just to sound older. “I expected X; the data
showed Y; I tested Z” is enough when all three are true and attributable.

## Tennis report, once measurements exist

Working title: *Testing an acoustic tension estimate in isolated tennis strings*.
Use the protocol's predeclared validation outcome. Include the rig photograph,
force calibration, example spectrum with mode labels, predicted-versus-measured
plot and signed residuals. Report unresolved modes and specimen variability.
The ideal-string equation is established; the contribution is the carefully
bounded evaluation, not inventing a tension meter.

## Before sharing

Read the underlying sources yourself, reconcile every quantitative claim with
its raw data, and update AI_USE_AND_CONTRIBUTIONS.md. A plain voice is compatible
with transparent assistance; hiding assistance is not a writing style.
