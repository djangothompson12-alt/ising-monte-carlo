# Three-dimensional field and resolution audit: first public example

This is a prospective measurement plan for a new exploratory analysis of
already inspected public data, not a preregistration. Earlier 2D failures and
the simulation results are known. No 3D length result has yet been inspected.

Use each of Fell's four hashed ROI TIFFs, in file order, independently.
Choose a 256-cubed box centred on page 169 and the Al/Ge centroid of that page.
Fix that box across z; do not follow the centroid plane by plane. This is a
declared specimen-centred crop, not cross-time registration. Retain each
failure if a box leaves the image or includes a label other than Al=2/Ge=3.
Never move a box to find more Ge or obtain a resolved length.

Compare the complete box with concentric 192-cubed and 128-cubed boxes.
For each box use native data, 2x and 4x arithmetic block means, then threshold
those means at 0.5 with exact ties assigned to Ge. Averaging preserves the
mean of each box; cropping may change it. Thresholded phase volume fraction
is geometrical and is not chemical composition.

Compute nonperiodic, pair-count-normalised covariance along z/y/x, using
each field's mean and variance and lags through half of each axis length.
Interpolate the half-height crossing and integrate to the first zero. Retain
all directional values and require all three to resolve for an overall mean.
For binary fields also pool complete interface-to-interface chords from all
three axes, excluding the boundary-touching runs and reporting that censoring.
These statistics are different lengths, not interchangeable particle radii.

Compare processed lengths with the native length of the SAME crop; compare
native cropped lengths with the native full box separately. Missing crossings
stay unresolved. Every crop/factor/stage is reported. No parameter is chosen
by its resulting length. The cropped volumes overlap and the four scans are
one specimen; do not calculate independent-specimen confidence intervals.

The first example tests static 3D measurement sensitivity. It neither fits a
growth exponent nor reproduces the authors' population-specific lamellar and
precipitate measurements. It does not establish that the selected box is
representative of the specimen or that a laboratory needs this tool.

Source: Jonas Fell, Mendeley Data v1, DOI 10.17632/hj9njz3rxp.1, CC BY 4.0.
Source metadata: research/results/alge_time_series_metadata_qa_2026-09-18/metadata_qa.json.
