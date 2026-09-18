# A bounded materials-imaging pilot to discuss with a problem owner

*AI-assisted planning note, 17 September 2026. Not an offer that the current tool solves an industrial problem. No partner has agreed to this protocol.*

## One question

For a **particular microstructure measurement an imaging researcher already uses**, how much does the reported quantity change when the same approved images or masks are observed at a different spatial resolution or processed under another predeclared choice? The Kawasaki trajectories provide a controlled synthetic comparator, not a physical prediction for the partner's material.

The first conversation is to learn **what decision the measurement informs**. If it is not a domain or feature-length decision, this pilot may be irrelevant. The current threshold-only steel-image pilot failed a practical length-accuracy test; it must not be pitched as validated segmentation software.

## Smallest defensible collaboration

1. The owner identifies one material, one phase/feature, the existing reference measurement and what difference would matter in their workflow. The owner chooses whether any image/mask may leave their organisation. A public dataset is preferable for the first test.
2. For an image series, record specimen identity, timestamps, physical pixel/voxel scale, imaging modality, registration, common field of view, phase-label meaning and the independent experimental unit. For static images, **do not** fit a coarsening rate. If only unannotated raw images exist, this pilot first becomes a segmentation-validation study and should not proceed straight to a growth claim.
3. Freeze the reference mask/measurement and a small set of plausible observation variants **before** looking at which variant agrees best. Compare the partner's preferred outcome and, only if relevant, this project's correlation half-height length. Record unresolved lengths instead of replacing them with zero or half a frame.
4. Estimate variability over independent specimens/experiments where available. Repeated slices, crops and times from one specimen are paired observations, not independent replicas. Show both aggregate results and failures; report any tuning done on the same images as exploratory.
5. Give the owner a short reproducible table and visual examples, plus a direct question: did the audit change confidence in a measurement or reveal a useful control? Their answer may be “no.” Quote or name them only with permission.

The [one-page pilot record](MASK_AUDIT_PILOT_RECORD.template.md) turns these
questions into choices to write down **before** running the mask tool. It
also records a negative answer and the owner's actual criticism; it is not
an endorsement form.

## Possible first public-data route

Two leads are documented in the [dataset scout](EXTERNAL_DATASET_SCOUT_2026-09-17.md).
The [Al–Ge release](https://doi.org/10.17632/hj9njz3rxp.1) explicitly states
CC BY 4.0 and names segmented phases and voxel sizes. Four 60-nm ROI files
have now been downloaded and hashed, and one fixed interior-plane test was
run; [its unresolved early regions are reported](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md).
Same-feature registration and a physically meaningful common region have
**not** been established. Its
initial overview has a different voxel size from later scans, and its
[authors already measured 3D feature evolution and hardness](https://doi.org/10.1016/j.tmater.2023.100009).
The [Al–Cu 4D collection](https://doi.org/10.18126/M2CC73) is another
segmented time-series candidate, but its access and reuse conditions still
need checking; [Sun et al. 2017](https://doi.org/10.1016/j.actamat.2017.04.054)
already used spatial correlations on it. The Al–Cu series concerns
solid–liquid dendritic coarsening; the Al–Ge scans concern **solid-state
annealing** of an initially cast eutectic microstructure, including Ge
lamellae and precipitation. The latter is closer to the project's materials
motivation, but neither experiment is validated by this 2D, vacancy-free
Kawasaki model. A defensible first pilot would
ask a researcher to name **one existing measurement decision** and compare a
small, predeclared set of observation choices against the published or
owner-supplied reference. If the sources have already answered that exact
question, stop rather than relabel a reproduction as a discovery.
For Al–Ge, the first question to take to an imaging researcher is whether
any **population-specific** measurement audit would be useful. The source
paper separates Ge lamellae from later precipitates; our fixed all-Ge 2D
length combines them, so a four-stage trend of that length would not be a
replication of the paper's 3D quantities. The 195-minute reconstruction
received different artifact correction and the rotation stage changed;
cross-time comparability is a question, **not** evidence of a processing
artifact. No trend should be fitted from the five loose 2D feasibility
slices or from the fixed 44-plane observation test.

## Stop conditions

- Scale, registration, phase labels, source rights or specimen identity cannot be established.
- The proposed metric does not answer the owner's practical question.
- Changing masks produces disagreement so large that the physical conclusion is not robust; report that as a failure, not a deployment.
- A reviewer identifies directly equivalent prior work or a standard method that already makes this analysis redundant.

The outcome that would genuinely count toward external validation is a
specific independent critique, an approved and documented test, and a
problem owner's factual judgement of whether it was useful. An internship,
data download, conversation, preprint or institutional affiliation alone
does not supply that validation.
