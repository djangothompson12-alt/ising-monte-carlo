# Preparation and verification — 10 September 2026

Completed locally:

- Controlled observation study on all 64 long-run replicas plus eight new
  L=128, 20,000-sweep replicas; no repeated seeds across these ensembles.
  See [measurement-study results](MEASUREMENT_STUDY_RESULTS.md).
- Five original CC-BY-4.0 AlGe TIFF slices and metadata retrieved with bounded
  range requests. Member CRC/local SHA-256 checked; full archive MD5 not checked.
  QA identified registration/intensity/metadata issues. No experimental exponent
  or validated phase-size measurement is reported.
- Portable private evidence pack: `research/runs/evidence_pack_v2/` and its ZIP
  (approximately 41 MB). Version 2 adds the dashboard source required by the
  export provenance test; the first pack is retained as an audit trail.
  Archive CRC and file SHA-256 checks pass.
  HTML figure index visually inspected; all six linked images loaded.

- 24 pilot replicas, their bootstrap/window analysis and plotted diagnostics.
- Four-observable paired reanalysis of all 24 pilot replicas, with immutable
  analysis inventories, actual retained time bounds, six diagnostic figures
  and [a results note](PILOT_ESTIMATOR_RESULTS.md). This post-pilot analysis is
  exploratory; it does not modify the simulation kernels.
- Resumable long-run infrastructure and all 64 long-run replicas completed
  within the six-hour cap. Primary analysis and four figures inspected; see
  [the overnight results](OVERNIGHT_RESULTS.md). No extension was launched.
- Isolated-string frequency/force calculation, WAV peak measurement, specimen-
  separated comparison and prediction/residual plots; no physical measurements.
- Paused dashboard raw ZIP exports, unclipped local slopes and anisotropic Tc.
- Prospective protocols, a review brief, writing guide, release checklist and
  targeted outreach drafts. Nothing sent, submitted, committed or published.
- Corrections to the Fe–Cr composition convention, overstatements about an
  established asymptotic exponent, and causal claims from droplet histograms.

Verification actually performed by the coding assistant:

- All 33 unittest checks pass, including new synthetic power laws/audio,
  uncertainty propagation checked by Monte Carlo, reproducible seeded replicas,
  conservation, heat bookkeeping and export preservation of NaN/negative values.
- Metrology checks cover Parseval normalisation, a known sinusoidal wavelength,
  sign/translation/offset invariance, correlation integrals, periodic interface
  counts, the original engine threshold and paired slope differences.
- Finite-window image tests check FFT versus explicit valid-pair sums, no
  periodic edge pairing, direction resolution, mean-preserving block averaging,
  pixel scale, invariances, input guards, no source mutation and explicit image
  import calibration/provenance. The same suite also passes from the pack's
  isolated source directory using the tested numerical environment.
- The synthetic comparison plot renders and refuses to overwrite an existing
  output. Synthetic inputs are confined to tests, not experimental results.
- Pilot figures inspected visually; the z=3 panel is not a demonstrated collapse.
- Solara launched locally and exercised through Start/Pause. Raw ZIP link
  present with a .zip filename and embedded ZIP payload. ZIP contents tested
  independently. The in-app browser did not expose a file-download completion
  event; verify the saved file in your normal browser before relying on downloads.
- Review brief inspected in the browser; phase diagram and pilot plots inspected.
- Python syntax compilation and git diff whitespace checks pass.

An hourly follow-up, bounded to eight checks, detected completion and ran the
primary analysis. It was paused after the completion report. No engines
were changed and nothing was published by the scheduled task.

Still required for the optional tennis project: equipment/safety review and
physical data. For the primary Kawasaki paper, the priorities are
independent student understanding and reproduction, external review, and a
fresh LaTeX build/page inspection. The tracked manuscript PDF is stale.
No physical Fe–Cr time/length mapping has been justified or implemented.
Prior-art benchmark reconciliation and experimental specimen masking,
segmentation, calibration and registration remain outstanding. Source metadata
declares MIT, but a standalone LICENSE file is missing; clarify before release.
