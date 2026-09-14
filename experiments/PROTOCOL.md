# Can sound measure tension in a tennis string?

**Prospective protocol, 10 September 2026. No physical measurements collected.**
Review the apparatus with a physics teacher or technician before building it.

The question is not whether a string makes a higher note when it is tighter.
That is established physics. The useful question is how accurately a simple
acoustic estimate measures load in real tennis strings, and where the estimate
starts to fail. Compare two documented products, such as a nylon and a polyester
string, without assuming that one product represents its whole material class.

## What this has to do with the existing project

The Ising model studies phase ordering. It has no string elasticity, racket
geometry or polymer relaxation law. It cannot predict racket tension, spin,
comfort or injury risk. This experiment is a separate mechanics study using the
same approach: make an explicit model, test its assumptions, preserve raw data,
and report errors. Keep separate methods and results; do not call it experimental
validation of Kawasaki dynamics. A short second report is clearer than forcing
the two into one paper.

## Prediction to write down before recording

For a uniform, flexible string of vibrating length L, loaded linear mass density
μ, fixed ends and small transverse displacement:

    f₁ = (1 / 2L) √(F / μ)       F_acoustic = 4 μ L² f₁²

Here F is in newtons, L in metres, μ in kg/m and f₁ in hertz. Derivation:
force balance gives transverse wave speed √(F/μ); the fundamental wavelength is
2L. These are textbook equations, not a new theory. Sources:
[OpenStax: wave speed](https://openstax.org/books/university-physics-volume-1/pages/16-3-wave-speed-on-a-stretched-string)
and [fixed-end modes](https://openstax.org/books/university-physics-volume-1/pages/16-6-standing-waves-and-resonance).
The software tests check the algebra, inverse mapping and synthetic audio;
they do not validate real strings.

If independent input standard uncertainties are small, propagate them as:

    u_F/F = √[(u_μ/μ)² + (2u_L/L)² + (2u_f/f)²]

That is first-order propagation, not total error: bending stiffness, slipping
supports and imperfect mode identification can produce systematic bias. If
length and loaded density share a measurement, they are correlated; include
covariance or propagate the original measured quantities together instead.

## Minimum equipment and safety

- Spare string with product, gauge and batch recorded; preferably two products.
- A rigid, technician-approved low-load rig with well-defined vibrating supports.
- An independent load cell/force gauge, or calibrated masses with a supervised
  pulley arrangement. Friction means that hanging mg is not automatically the
  force in the vibrating segment; measure/check the discrepancy.
- Metre rule, a scale able to resolve the mass of a sufficiently long string,
  phone WAV recording, thermometer, and a laboratory notebook.

Start at loads around 1–5 N only if the technician approves the apparatus. This
is a low-load pilot, not a reproduction of a racket stringer's much higher load.
Do not improvise a full-tension racket rig, heat strings, load a racket frame
with hanging weights, or put your face in line with stretched string. Use eye
protection, retain hanging masses near the floor, and shield the recoil path.
The safe load limit belongs to the apparatus supervisor, not this document.

Measure μ by weighing a long, clean length and dividing by its measured length.
Do not infer it solely from the nominal gauge. Record resolution and calibration.
The formula needs **loaded** μ: track the extension of a marked material segment;
for conserved segment mass, μ_loaded = μ_unloaded/(1 + strain). Measure the
actual vibrating span, not the distance between arbitrary clamp edges.

## First session: learn whether the measurement works

1. Photograph and sketch the rig, mark the vibrating endpoints and material
   segment, and record temperature. Take a room-noise recording.
2. Use one pilot specimen of each product. At three safe loads, wait the same
   recorded settling time and measure actual force, loaded span and extension.
3. Calculate the predicted frequency **before** looking at the audio result.
4. Make at least three separate small plucks per condition. Keep microphone
   position fixed and prevent contact with the string. Save original WAV files.
5. Inspect the spectrum over a broad band. The loudest peak may be the second
   harmonic. Check lower modes, harmonic spacing and repeatability; the code
   deliberately does not choose the fundamental for you.
6. Repeat with a second vibrating length as a diagnostic: under controlled load
   and density, the fundamental should vary approximately as 1/L. Record any
   failure; do not narrow the search band to hide disagreeing modes.
7. Use the pilot to fix crop times, frequency search range, settling time and
   exclusion rules. Date these choices before collecting validation data.

## Validation session: test without retuning

Use at least five **new, independent string specimens per product**, three
approved load conditions each, and three plucks per condition. Randomise
specimen order and counterbalance load order; record earlier loading because
it can change later behaviour. Cuts from one reel are specimens, not independent
manufacturing batches. Do not generalise to all nylon/polyester from one product.

Primary outcome: mean absolute relative force error, first averaged over load
conditions within each validation specimen, then across specimens. Show all
signed residuals against force, product and specimen. Repeated plucks measure
repeatability, not additional independent samples. The current comparator uses
the **unfitted ideal-string baseline**. Any correction learned later needs its
own untouched validation specimens; do not fit and test on the same data.

Predeclare exclusions: broken/slipped specimen, clipped/corrupt recording, or
unresolved fundamental after the documented checks. Keep excluded files and
reasons. Report the unresolved-mode fraction as a result, rather than quietly
discarding difficult cases. Do not invent a success threshold after seeing errors.

## Optional follow-up: does the estimate track relaxation?

Only after the baseline works, hold string length fixed and independently log
force and frequency at 0, 1, 5, 15, 30 and 60 minutes. Use the same controlled
start procedure and record actual timestamps. Compare F(t)/F(0) with the acoustic
estimate, accounting for any measured length/density changes. A hanging constant
mass tests creep (extension under load), **not** stress relaxation at fixed
length. This distinction should be in your own explanation of the experiment.

For an intact racket, record frequency ratios only unless a separately validated
stringbed model is available. A coupled stringbed and frame are not a single
fixed-end string. Do not convert a racket's strongest audio peak directly to
newtons with this tool.

## Run the tools

From the repository root (example inputs below are illustrative, not measurements):

```bash
.venv311/bin/python -m experiments.string_lab predict --force-N 4 --length-m 0.5 --density-kg-m 0.002
.venv311/bin/python -m experiments.string_lab audio path/to/pluck.wav --start-s 0.1 --end-s 1.1 --low-Hz 20 --high-Hz 1000
.venv311/bin/python -m experiments.string_lab compare experiments/measurements.json --output experiments/results/session01.json --plot experiments/results/session01.png
```

The first example predicts 44.72 Hz. Check whether your recorder captures the
expected band before buying or building anything. FFT bin spacing is reported,
but it is not a complete frequency uncertainty.

Copy the empty template to a new measurement file and enter records with this
schema (nulls are placeholders and must be replaced with real measurements):

```json
{
  "record_id": "nylon-specimen01-load01",
  "specimen_id": "nylon-specimen01",
  "role": "pilot",
  "reference_force_N": null,
  "loaded_length_m": null,
  "loaded_linear_density_kg_m": null,
  "frequency_repeats_Hz": [],
  "fundamental_confirmed": false,
  "product": "",
  "temperature_C": null,
  "settling_time_s": null,
  "load_order": null,
  "audio_files": [],
  "notes": ""
}
```

Put records in a JSON array. Keep a notebook with uncertainties and rig checks;
the comparator does not replace that record. It rejects fewer than three
frequency repeats, unconfirmed modes, and shared pilot/validation specimens.

## How to position the results

A useful report can find that the estimate fails. Explain why, with independent
measurements and residuals. Do not claim to have invented acoustic tension
measurement. [Tennis Warehouse University's original test method](https://twu.tennis-warehouse.com/learning_center/stringtestmethod.php)
already distinguishes static and impact behaviour and uses a controlled string
test rig. [ITF technical resources](https://www.itftennis.com/en/about-us/organisation/publications-and-resources/tennis-tech/)
provide further context. Our low-load study is not equivalent to those tests.

For an outside reviewer, ask: “Are these boundary conditions and uncertainty
estimates adequate to test the acoustic tension estimate?” That is an answerable
question before any request for endorsement.
