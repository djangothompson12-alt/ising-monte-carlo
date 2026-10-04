# One small materials-imaging pilot — fill in before analysing a new dataset

*Working template. Completing it does not create an endorsement, a lab
deployment or a prediction from the Kawasaki model. Ask the image owner to
check the problem definition and sharing terms before using their files.*

## First conversation before any data transfer

Start with one public or owner-approved binary mask, not a request for a large
confidential dataset. Ask whether the owner actually uses a correlation-based
feature length, and whether changing numerical image resolution is a relevant
decision. If not, record that answer rather than asking for a favourable quote.

The initial request can be limited to: “Would this comparison answer a useful
measurement question for you? If so, could we agree one mask, its calibration
and a meaningful comparison before I run it?” This is a discussion draft, not
permission to contact anyone. Student approval is required before sending.

Keep the first deliverable small: one report with all native/2x/4x rows, the
declared choices and one paragraph of limitations. Do not ask for endorsement
as a condition of helping. Ask permission separately before recording a
person's name, quoting their assessment or including their files in a release.

## The problem the image owner actually has

- Organisation / contact (keep private unless they approve naming):
- Material and feature of interest:
- What decision uses this image measurement? What is measured today?
- Would a change in a 2D correlation half-height length matter to that
  decision? If not, stop or define a different, owner-approved measurement.
- What size of change would matter in the owner's units, and why?

## Data and permissions

- Source, licence / written sharing permission, and any export limits:
- Specimen or experiment IDs; which records are truly independent?
- Imaging method; original physical pixel size and its source:
- Is this a binary **phase mask** or a calibrated quantitative **composition
  map**? A phase area fraction is not normally bulk chemical composition; the
  current tool accepts only the former and cannot test elemental mass balance.
- Are pixels square (equal calibrated x/y spacing)? If not, stop: the current
  one-scale estimator does not support that image.
- Who produced and checked the binary masks? What exactly is foreground?
- If there are multiple times: are the same features/fields registered, and
  is the physical scale the same? If not, do **not** fit a growth rate.
- Where will raw images/masks stay? What may appear in a review report?

## Fixed comparison, decided before opening the new result table

- Primary masks and one rectangular field per image, with reason for each:
- Primary native measurement and 2×/4× comparison:
- Exact 50:50 block tie rule (foreground or background):
- Handling of a missing half-height crossing: report *unresolved*, not zero.
- Partner's existing reference method, if any; whether it measures the same
  feature as this 2D correlation length:
- Stop criterion if phase area fraction, field coverage, units or segmentation
  are not trustworthy:
- What result would count as useful, unhelpful or misleading **to the owner**?

## Analysis record — complete after running

- Date, tool/source version, input hashes and output manifest:
- All planned masks and their three rows, including unresolved rows:
- Any departures from the fixed choices above, marked exploratory:
- Did the owner recognise the measured feature as the one they use? Their
  words, with permission to quote (yes/no):
- What criticism did they make? What changed in response? What did not work?

The student should be able to explain the measurement and failure cases in
his own words. AI-assisted code and report preparation must be disclosed.
One specimen with many slices is still one specimen; a public-image replay
is still not independent laboratory use. Do not call this a validated alloy
predictor, a commercial deployment or an academic endorsement.
Use the [external-pilot decision document](CONSERVATION_AWARE_EXTERNAL_PILOT_2026-09-19.md)
before interpreting any phase-fraction change as a conservation result.
