# Ising coarsening: spin flips, atom swaps, and how we measure growth

**🔴 [Live Demo](https://djangothompson12-alt.github.io/ising-monte-carlo/)** — real-time Model A dynamics running in-browser via HTML5 Canvas, with live Chart.js plots of magnetization and energy.

This is an ongoing gap-year research project about how patterns grow after a sudden temperature drop. It began with two 2D Ising simulations:

- **Model A** flips one spin at a time using the Metropolis rule. Total magnetisation can change.
- **Model B** exchanges neighbouring spins using the Metropolis rule. The number of each spin type stays fixed, so it is a simple model of a binary mixture with conserved composition.

The original question was why the two models coarsen at different rates. The current, harder question is **how much a measured growth exponent depends on run length, lattice size and the way domain size is measured**. The expected late-time laws are $L(t)\propto t^{1/2}$ for non-conserved dynamics and, under the usual diffusion-controlled conditions, $L(t)\propto t^{1/3}$ for conserved dynamics. Our finite runs do not prove either asymptotic law. [Progress and limits](docs/PROGRESS_AND_LIMITS.md) gives the short account; the longer sections below explain the code and methods.

The completed 64-run Model B study found effective slopes near 0.26 in its later fit window for the larger lattices. Changing the fit window or the image-processing pipeline changes the fitted slope. That is a measurement result, **not** evidence that a real alloy follows a different growth law. The model has no calibrated mapping from Monte Carlo sweeps to hours or from lattice sites to micrometres. [Raw data and reproducibility](research/DATA_README.md) are documented separately. Development included substantial [AI assistance](AI_USE_AND_CONTRIBUTIONS.md); all scientific claims remain subject to student review.

*A terminology note, since it matters for precision:* the move-acceptance rule implemented for Model A throughout this codebase is **Metropolis** ($P_\text{accept} = \min(1, e^{-\beta\Delta E})$), not the Glauber rate function ($P_\text{accept} = 1/(1+e^{\beta\Delta E})$). Both are non-conserved single-spin-flip realizations in the Hohenberg–Halperin **Model A** universality class, but this repository calls the implemented dynamics Metropolis throughout.

<p align="center">
  <img src="model_a/figures/fig1_phase_transitions.png" width="700" alt="Phase transition observables vs. temperature">
</p>

<p align="center">
  <img src="model_a/figures/fig2_spin_domains.png" width="700" alt="Spin domain snapshots across the phase transition">
</p>

## Physics background

The model places a spin $\sigma_i \in \{-1, +1\}$ on every site of an $L \times L$ square lattice with periodic boundary conditions. The energy of a configuration is given by the Ising Hamiltonian

$$
H = -J \sum_{\langle i,j \rangle} \sigma_i \sigma_j
$$

where $J$ is the nearest-neighbor coupling constant (set to $J = 1$ throughout) and $\langle i,j \rangle$ denotes a sum over nearest-neighbor bonds, each counted once. For $J > 0$, aligned neighboring spins are energetically favored, producing ferromagnetic order at low temperature.

Configurations are sampled from the Boltzmann distribution $P(\sigma) \propto e^{-\beta H(\sigma)}$ (with $k_B \equiv 1$, $\beta = 1/T$) using single-spin-flip **Metropolis dynamics**: a randomly chosen spin is flipped with probability

$$
P(\text{accept}) = \min\left(1,\ e^{-\beta \Delta E}\right)
$$

where $\Delta E$ is the energy change of the flip. This update rule satisfies detailed balance with respect to the Boltzmann distribution, so long Markov chains of these moves converge to thermal equilibrium.

### Observables

At each temperature, after discarding an equilibration (burn-in) period, the simulation collects samples spaced by several sweeps (to reduce autocorrelation) and estimates four per-spin observables, where $N = L^2$:

**Magnetization** (order parameter):

$$
\langle |M| \rangle = \frac{1}{N}\left\langle \left| \sum_i \sigma_i \right| \right\rangle
$$

**Energy:**

$$
\langle E \rangle = \frac{1}{N} \langle H \rangle
$$

**Specific heat**, from energy fluctuations (fluctuation–dissipation theorem):

$$
C_v = \frac{1}{N T^2}\left( \langle H^2 \rangle - \langle H \rangle^2 \right)
$$

**Magnetic susceptibility**, from magnetization fluctuations:

$$
\chi = \frac{1}{N T}\left( \langle M^2 \rangle - \langle |M| \rangle^2 \right)
$$

$C_v$ and $\chi$ are both response functions and, in the thermodynamic limit, diverge at the critical temperature — the simulation reproduces this as sharp finite-size peaks. The exact critical temperature for this model (Onsager, 1944) is

$$
T_c = \frac{2}{\ln(1+\sqrt{2})} \approx 2.269\ (J/k_B)
$$

which is marked as a vertical reference line in the generated figures.

### Non-equilibrium quench kinetics

<p align="center">
  <img src="model_a/figures/fig3_kinetics_entropy.png" width="600" alt="Domain growth and bath entropy-flow kinetics after a temperature quench">
</p>

Quenching the lattice from a disordered high-temperature state ($T_{\text{initial}} = 5.0 \gg T_c$) to an ordered low-temperature state ($T_{\text{final}} = 1.5 < T_c$) leaves the system far from equilibrium: ordered patches appear and coarsen. For this **non-conserved** order parameter (single-spin-flip dynamics, no magnetization conservation), phase-ordering theory predicts curvature-driven interfacial motion obeying the **Lifshitz–Allen–Cahn growth law**

$$
L(t) \sim t^{1/2}
$$

The characteristic domain size $L(t)$ is extracted from the equal-time spatial spin-autocorrelation function

$$
C(r, t) = \langle \sigma_i(t)\, \sigma_{i+r}(t) \rangle
$$

(averaged over lattice sites and the two principal lattice directions) as the lattice distance $r$ at which $C(r, t)$ first decays to $1/2$, linearly interpolated between the bracketing integer separations. `run_quench_kinetics` (in `model_a/ising_engine.py`) averages this over many independent quench replicas and samples $C(r,t)$ at logarithmically spaced sweep counts, since the growth is expected to be a power law in time.

**Bath entropy flow.** The lattice is coupled to a heat bath at fixed $T_{\text{final}}$: every accepted Metropolis flip changes the system's energy by $\Delta E$, and by conservation of energy the bath absorbs heat $-\Delta E$ over that move. Summing accepted $\Delta E$ within each inter-checkpoint interval therefore gives the per-spin bath entropy-flow rate

$$
\dot{S}_{\mathrm{bath}}(t) = -\frac{1}{T}\frac{\langle \Delta E \rangle}{dt}.
$$

This is a useful dissipation proxy and is positive on average in the reported relaxation runs. It is **not by itself the total stochastic entropy-production rate**, which would also require the system's Shannon-entropy change. The result arrays retain the historical field name `entropy_production` for API compatibility.

## Repository structure

```
.
├── index.html                  # Model A live demo (Canvas + Chart.js, no build step)
├── comparative_analysis.py     # Reads both models' CSVs, plots L(t) scaling side by side
├── phase_diagram.py            # Regular-solution spinodal mapped from Model B couplings
├── requirements.txt
├── manuscript/                  # main.tex (revtex4-2 PRL format) + compiled main.pdf
├── figures/                      # fig_comparative_scaling.png (from comparative_analysis.py)
├── model_a/                    # Model A: non-conserved order parameter (Metropolis)
│   ├── ising_engine.py           # Numba-jitted Metropolis MC core + observable calculation
│   ├── visualizer.py              # Publication-quality figure generation (matplotlib)
│   ├── main.py                    # CLI entry point: runs the sweep, saves data + figures
│   ├── plot_kinetics.py           # Quench simulation + domain-growth/bath-flow plot
│   ├── ising_3d_engine.py          # Separate cubic-lattice Model A core
│   ├── plot_3d.py                  # Orthogonal-slice renderer for 3D Model A
│   ├── figures/                    # Generated PNGs (fig1, fig2, fig3)
│   └── results/                    # Generated observables.csv, quench_kinetics.csv
└── model_b/                    # Model B: conserved order parameter (Kawasaki) -- see below
    ├── kawasaki_engine.py         # Numba-jitted Kawasaki MC core, anisotropic couplings,
    │                                #   directional FFT correlations, bath heat bookkeeping
    ├── plot_kawasaki_kinetics.py  # Launcher: runs the quench, saves CSV + figure
    ├── kawasaki_3d_engine.py       # Separate anisotropic cubic-lattice Model B core
    ├── plot_3d.py                  # Orthogonal-slice renderer for 3D Model B
    ├── live_visualizer.py         # Native desktop dashboard (matplotlib + Tk)
    ├── solara_app.py              # Web dashboard (Solara)
    ├── figures/                    # fig_anisotropic_kinetics.png
    └── results/                    # kawasaki_kinetics.csv
```

### Live demo (`index.html`)

A self-contained, single-file browser simulation — open `index.html` directly (or visit the [live demo](https://djangothompson12-alt.github.io/ising-monte-carlo/)) to run Model A dynamics interactively at ~60 FPS. It reimplements the same physics as `model_a/ising_engine.py` (including an external field term $H = -J\sum_{\langle i,j\rangle}\sigma_i\sigma_j - H\sum_i \sigma_i$) directly in JavaScript, rendered with an HTML5 Canvas pixel buffer, with live [Chart.js](https://www.chartjs.org/) plots of magnetization and energy on locked axes matching the Matplotlib figures below. Sliders control temperature, external field, lattice size, and sweeps per frame; three preset buttons jump directly to a low-temperature quench, the critical point, and the high-temperature paramagnetic phase. A "Download Run Data (CSV)" button exports lattice size, sweep count, $M(t)$, $E(t)$, and an estimated domain size $L(t)$ for direct comparison against the Python pipeline's output. No build step or server required.

- **`model_a/ising_engine.py`** — `SimulationConfig` (lattice size, temperature range, equilibration/sampling sweeps), the JIT-compiled Metropolis sweep and energy/magnetization kernels, and `run_temperature_sweep` / `sample_snapshot` for producing sweep-level and single-temperature results.
- **`model_a/visualizer.py`** — `plot_phase_transitions` (4-panel $|M|$, $E$, $C_v$, $\chi$ vs. $T$) and `plot_spin_domains` (lattice snapshots at representative temperatures).
- **`model_a/main.py`** — orchestrates a full run: temperature sweep → `results/observables.csv` → `figures/fig1_phase_transitions.png` and `figures/fig2_spin_domains.png`.
- **`model_a/plot_kinetics.py`** — runs a $T_{\text{initial}} \to T_{\text{final}}$ quench via `ising_engine.run_quench_kinetics`, saves `results/quench_kinetics.csv`, fits a power law to the domain-growth scaling regime, and renders the two-panel `figures/fig3_kinetics_entropy.png` ($L(t)$ scaling fit on top, bath entropy-flow rate below).

## Installation

Requires Python 3.10–3.13.

```bash
git clone https://github.com/djangothompson12-alt/ising-monte-carlo.git
cd ising-monte-carlo
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Note (Intel macOS only):** numba's PyPI wheels for `x86_64` macOS stop at version `0.62.1`; on Intel Macs, pin with `pip install "numba==0.62.1"` before installing the rest of `requirements.txt`. Apple Silicon, Linux, and Windows are unaffected.

## Usage

Run the full pipeline with default parameters ($L=24$, $T \in [1.2, 3.6]$, 40 temperature points):

```bash
python model_a/main.py
```

This prints progress to stdout, writes `model_a/results/observables.csv`, and generates both figures in `model_a/figures/`. A full run at the defaults completes in well under a minute on a modern laptop (Numba JIT-compiles the Metropolis kernel on first call).

Customize the simulation via CLI flags:

```bash
python model_a/main.py \
  --L 32 \
  --t-min 1.0 --t-max 4.0 --n-temperatures 60 \
  --eq-sweeps 5000 --mc-sweeps 6000 --sample-interval 4 \
  --seed 7
```

| Flag | Default | Description |
|---|---|---|
| `--L` | 24 | Lattice dimension ($L \times L$ spins) |
| `--J` | 1.0 | Nearest-neighbor coupling |
| `--t-min`, `--t-max` | 1.2, 3.6 | Temperature sweep range |
| `--n-temperatures` | 40 | Number of temperature points |
| `--eq-sweeps` | 3000 | Equilibration (burn-in) sweeps per temperature |
| `--mc-sweeps` | 4000 | Sampling sweeps per temperature |
| `--sample-interval` | 4 | Sweeps between successive samples |
| `--seed` | 42 | Base random seed |
| `--domain-L` | 64 | Lattice size used only for the `fig2` spin-domain snapshots |

### Using the engine directly

```python
import sys
sys.path.insert(0, "model_a")
from ising_engine import SimulationConfig, run_temperature_sweep, sample_snapshot

config = SimulationConfig(L=32, t_min=1.5, t_max=3.0, n_temperatures=30)
result = run_temperature_sweep(config)   # result.temperatures, .magnetization, .energy, ...

lattice = sample_snapshot(T=2.269, config=config, seed=0)  # (L, L) array of +-1
```

### Quench kinetics

```bash
python model_a/plot_kinetics.py
```

Runs a $T=5.0 \to T=1.5$ quench (default: $L=128$, 16 independent replicas, 2000 sweeps), writes `model_a/results/quench_kinetics.csv` ($t$, $L(t)$ and its standard error, bath entropy-flow rate and its standard error), fits a declared finite window, and saves `model_a/figures/fig3_kinetics_entropy.png`. Fitting the currently committed CSV with the current code gives $\alpha = 0.4999$ from 19 checkpoints at 3–489 sweeps. An older draft stated 0.4841; that number is not the fit of this archived CSV and should not be reused without its original data and fit settings. Nearness to $1/2$ is a consistency check, not proof of an asymptotic law.

```python
import sys
sys.path.insert(0, "model_a")
from ising_engine import QuenchConfig, run_quench_kinetics

config = QuenchConfig(L=64, T_initial=5.0, T_final=1.5, n_replicas=8, max_sweeps=1000)
result = run_quench_kinetics(config)
# result.t, .domain_size, .domain_size_err, .entropy_production, .entropy_production_err
```

### Manuscript

[`manuscript/main.tex`](manuscript/main.tex) is a working draft, not a finished or peer-reviewed paper. The tracked [`manuscript/main.pdf`](manuscript/main.pdf) is older than that source. To rebuild it after checking the claims, use:

```bash
cd manuscript && pdflatex main.tex && pdflatex main.tex
```

(two passes, to resolve citations and cross-references).

### Exploratory 3D cubic lattices

The manuscript and all reported results remain two-dimensional. Separate,
exploratory 3D cubic-lattice engines have been added without changing the
validated 2D engines, visualisers or results. Both use six periodic nearest
neighbours. Model A uses Metropolis single-spin-flip dynamics; Model B uses
nearest-neighbour Kawasaki exchange and conserves total magnetisation exactly.

```bash
python model_a/plot_3d.py --L 32 --sweeps 200
python model_b/plot_3d.py --L 32 --sweeps 200 --Jx 1 --Jy 1 --Jz 1
```

Each command saves central `xy`, `xz`, and `yz` slices of a genuine 3D spin
volume. Model B has couplings `Jx`, `Jy`, and `Jz`; unlike the 2D anisotropic
model, its 3D critical-temperature surface has no exact Onsager condition, so
the 3D quench temperatures are explicit inputs. These are learning and future
development tools, not grounds for a 3D growth-law, alloy-prediction, or
experimental-validation claim until a separate 3D measurement protocol exists.

### Real-image measurement intake

`research/analyse_images.py` accepts only explicitly calibrated, documented
2D images and never guesses a segmentation threshold or fits an experimental
growth exponent. For a data owner or microscopist who supplies a justified
range of candidate thresholds, `research/segmentation_sensitivity.py` retains
every result instead of silently selecting the most favourable one:

```bash
python -m research.segmentation_sensitivity approved_image_manifest.json \
  --output research/runs/declared_threshold_sensitivity
```

The template contains placeholders, not real measurements. Registration, ROI
selection, phase identification and permissions must be supplied by the data
owner before a real dataset is analysed.

## Verification

The generated `fig1_phase_transitions.png` shows the expected signatures of a second-order phase transition: $\langle |M| \rangle$ drops from near 1 to near 0 across $T_c$, $\langle E \rangle$ rises smoothly, and both $C_v$ and $\chi$ peak near $T_c \approx 2.269$. `fig2_spin_domains.png` shows large ordered regions at $T = 1.5$, mixed-scale clusters near $T_c$, and fine-grained disorder at $T = 3.5$. In the archived Model A quench CSV, the selected finite-window fit is $\alpha = 0.4999$. The bath entropy-flow-rate estimate falls from about 0.297 at the first checkpoint to $9.76\times10^{-6}$ at the last; this is a decline in an interval-averaged rate, not cumulative heat loss or total entropy production.

## Model B: Conserved Kawasaki Dynamics & Anisotropy

> **Live demo:** the previous badge here pointed at a Streamlit Community Cloud deployment (`anisotropic-materials-sim.streamlit.app`). The web dashboard has since been rebuilt on Solara (see below), which that platform can't host — Streamlit Cloud only runs Streamlit apps, and `model_b/solara_app.py` no longer imports `streamlit` at all, so the old deployment will break once this change reaches it. No replacement deployment exists yet; run it locally with the instructions below in the meantime.

### In plain language

Model B is a 2D lattice-gas analogue of a binary mixture: a move swaps two neighbours, so it cannot create or destroy either component. Its unequal couplings can make patterns longer in one lattice direction. Real materials also develop directional microstructures, including precipitate rafting in some superalloys, but **the mechanism here is not the same**: this code has fixed bond anisotropy, not elastic strain, stress, rolling or real alloy diffusion. Those examples motivate questions; they are not validations of the model.

Model A (above: `model_a/`, plus `index.html` and `manuscript/` at the repo root) is the Hohenberg–Halperin classification's non-conserved case: single-spin-flip dynamics, in which the order parameter is *not* conserved. [`model_b/`](model_b/) is a fully standalone implementation of the complementary case, **Model B**: Kawasaki spin-exchange dynamics, in which total magnetization $\sum_i \sigma_i$ is exactly conserved. It does not import, modify, or depend on any file outside `model_b/`.

### Physics

Rather than flipping a single spin, a Kawasaki move picks a random nearest-neighbor pair and proposes to *exchange* them, with Metropolis acceptance $\min(1, e^{-\beta \Delta E})$. Swapping two equal spins is a no-op; swapping unlike spins conserves $\sum_i \sigma_i$ by construction. This module also generalizes the Hamiltonian to independent horizontal/vertical couplings,

$$
H = -J_x \sum_{\langle i,j \rangle_x} \sigma_i \sigma_j \;-\; J_y \sum_{\langle i,j \rangle_y} \sigma_i \sigma_j,
$$

so the two coarsening directions can be compared directly. The critical temperature generalizes Onsager's exact result to the anisotropic case as the root of $\sinh(2J_x/T_c)\sinh(2J_y/T_c) = 1$ (`anisotropic_critical_temperature`, solved numerically; reduces to $T_c = 2J/\ln(1+\sqrt2)$ when $J_x = J_y = J$), and is used to set the quench temperatures automatically ($T_{\text{initial}} = 3\,T_c$, $T_{\text{final}} = 0.65\,T_c$) whenever they aren't given explicitly.

Because the order parameter is conserved, interfaces cannot move by changing a spin in place; material must be transported, usually by diffusion in the late-stage picture. Curvature still matters because it affects interfacial chemical potential. Under the usual conditions the expected late-time **Lifshitz–Slyozov growth law** is $L(t) \sim t^{1/3}$, in contrast to Model A's $t^{1/2}$. The directional domain sizes $L_x(t)$ and $L_y(t)$ are extracted independently from $C_x(r,t)$ and $C_y(r,t)$, computed with a 2D FFT. The bath entropy-flow proxy $\dot{S}_{\mathrm{bath}}(t) = -\frac{1}{T}\langle \Delta E \rangle / dt$ is tracked from the energy change of accepted exchanges.

The exchange energy-change formula and magnetization conservation were both checked directly against an independent brute-force recomputation of the full lattice Hamiltonian before any production run (exact match, not just "close").

### Usage

```bash
python model_b/plot_kawasaki_kinetics.py
```

Default configuration: $L=96$, $J_x=1.0$, $J_y=0.5$ (so $T_c(J_x,J_y) \approx 1.641$, giving $T_{\text{initial}} \approx 4.923 \to T_{\text{final}} \approx 1.067$), 16 replicas, 10000 sweeps. This takes roughly a minute and a half on the same hardware as the Model A pipeline, and writes `results/kawasaki_kinetics.csv` ($t$, $L_x(t)$, $L_y(t)$, $\dot{S}(t)$, all with standard errors) plus `figures/fig_anisotropic_kinetics.png`.

```python
import sys
sys.path.insert(0, "model_b")
from kawasaki_engine import KawasakiConfig, run_quench_kinetics

config = KawasakiConfig(L=64, Jx=1.0, Jy=0.5, n_replicas=8, max_sweeps=4000)
result = run_quench_kinetics(config)
# result.t, .domain_size_x, .domain_size_y, .entropy_production, and their standard errors
```

### Results

At the default configuration, $L_x(t)$ grows visibly faster than $L_y(t)$ throughout the run (e.g. $L_x \approx 4.0$ vs. $L_y \approx 1.9$ lattice units by $t=10{,}000$ sweeps), correctly reflecting the stronger horizontal coupling $J_x > J_y$. The measured bath entropy-flow proxy falls from $\dot{S}_{\mathrm{bath}}(t{=}1) \approx 0.151$ to $\dot{S}_{\mathrm{bath}}(t{=}10{,}000) \approx 7.3\times 10^{-6}$ (per spin, $k_B$ units) — again over four orders of magnitude, as in Model A.

Fitting $L_x(t)$ and $L_y(t)$ over the same style of trimmed scaling regime used for Model A gives effective exponents $\alpha_x \approx 0.18$ and $\alpha_y \approx 0.14$ — both well below the asymptotic Lifshitz–Slyozov prediction of $1/3$. Long-lived pre-asymptotic corrections are a plausible explanation for this shortfall, and the measured domain sizes remain well below the estimator's maximum range. Those observations do not, however, rule out finite-size or fit-window effects. Systematic runs over several lattice sizes and longer times are therefore required before assigning the discrepancy uniquely to pre-asymptotic physics.

### Interactive dashboards

Two live-updating visualizers sit alongside the batch pipeline (`plot_kawasaki_kinetics.py`) above — both read live simulation state directly (plain Python / reactive variables), not the saved CSV/figure:

- **Native desktop dashboard** (`model_b/live_visualizer.py`, matplotlib + Tk): a lattice heatmap, directional domain-growth plot, and bath entropy-flow plot, animated with `FuncAnimation`.
- **Web dashboard** (`model_b/solara_app.py`, [Solara](https://solara.dev/)): the same three live panels in a browser, with sidebar sliders (rendered with inline LaTeX via `solara.Markdown`) for the anisotropy ratio $J_x/J_y$, quench temperature $T_f$, lattice size, and sweeps per frame, plus Start/Pause/Reset controls, live growth-exponent/interfacial-density readouts, and a "Materials Science & Engineering" expander covering the analogies above. A background `asyncio` task advances the simulation and patches the lattice/chart widgets' traits directly, bypassing Solara's own reactive re-render cycle for that hot path (continuously driving a component re-render at animation speed turned out to race Solara 1.61.0's render scheduler); only a throttled numeric-metrics readout still goes through an actual `solara.reactive()` publish.

Run the web dashboard locally with:

```bash
pip install -r requirements.txt   # includes solara
solara run model_b/solara_app.py
```

(Solara apps are launched via the `solara` CLI, not `python model_b/solara_app.py`.) This opens the dashboard in your browser at `http://localhost:8765`.

## Comparative analysis

[`comparative_analysis.py`](comparative_analysis.py) is the one script that spans both models: it reads the CSV each model's own kinetics script already produces (`model_a/results/quench_kinetics.csv`, `model_b/results/kawasaki_kinetics.csv`) and plots their domain-growth scaling side by side on matching log-log axes — Model A's $L(t)$ against the Lifshitz–Allen–Cahn $t^{1/2}$ prediction, Model B's $L(t)$ (averaged from $L_x(t)$ and $L_y(t)$, for a like-for-like comparison against Model A's single isotropic domain size) against the Lifshitz–Slyozov $t^{1/3}$ prediction. It does not re-run either simulation; run `model_a/plot_kinetics.py` and `model_b/plot_kawasaki_kinetics.py` first if the CSVs don't exist yet.

```bash
python comparative_analysis.py
```

Saves `figures/fig_comparative_scaling.png` at the repo root (distinct from each model's own `figures/` subdirectory, since this figure isn't specific to either one) and prints both fitted growth exponents to stdout. This is the figure that most directly answers the question the project set out to ask: the two panels, plotted on identical log-log axes, make the different growth exponents of conserved vs. non-conserved order-parameter kinetics a direct visual comparison rather than a claim to take on faith.

## Regular-solution phase diagram

```bash
python phase_diagram.py
```

For the conserved Model B lattice-gas interpretation, this writes
`figures/fig_regular_solution_spinodal.png`: the Bragg--Williams
regular-solution spinodal derived by bond counting from the implemented
couplings, $k_B T_s(c)=8(J_x+J_y)c(1-c)$. It marks the actual isotropic
concentration-sweep and anisotropic-baseline quench paths. The plot is
explicitly a mean-field thermodynamic guide, not the exact 2D Ising
coexistence curve; Model A is excluded because its Metropolis spin flips do
not conserve composition.

## Fe--Cr literature benchmark

```bash
python fecr_literature_benchmark.py
```

This reads the committed Model B concentration-sweep result at `c=0.35` and
writes `figures/fig_fecr_literature_benchmark.png`, comparing its effective
growth exponent with two published measures for Xu et al.'s alloy labelled
35Cr at 773 K. Their composition table uses weight percent, not model site
fraction; these are not composition-matched systems. The
figure labels the comparison as qualitative: a 2D lattice measured in Monte
Carlo sweeps is not calibrated to a 3D alloy aged in hours. Its purpose is to
motivate a shared finite-time/coarsening question, not to claim quantitative
prediction. Experimental values and DOI provenance are documented in the
script.

## Reproducibility and external review

The controlled observation benchmark is implemented and has been run on the
64 long-run replicas plus eight fresh-seed repeats. See
[measurement-study results](docs/MEASUREMENT_STUDY_RESULTS.md),
[the observation protocol](research/IMAGING_PROTOCOL.md), and
[the writing/evidence guide](docs/PAPER_EVIDENCE_GUIDE.md).
It tests sensitivity to field of view, blur, pixel averaging and segmentation;
it does not establish a new growth law or a universal measurement correction.
Five licensed original experimental slices have also been retrieved and audited,
but are not yet a validated experimental kinetics comparison.

```bash
python -m research.imaging_benchmark research/runs/overnight --output new_imaging_analysis
python -m research.analyse_images --help
python -m research.verify_study research/runs/overnight \
  --source-root research/frozen_sources/2026-09-10
```

For a **separate symmetric-literature benchmark**, first complete and save a
copy of `research/reference_benchmark.template.json`. It is deliberately
invalid until a real target citation and comparison decisions have been
recorded. The runner only accepts an isotropic `c=0.5` campaign, writes every
replica/timepoint rather than an exponent fit, and records hashes of the input
archives and declaration:

```bash
python -m research.reference_benchmark research/runs/overnight my_completed_declaration.json --output reference_measurements
```

This is a measurement-comparison preparation tool, not a claim that a paper
has been reproduced. One-pass majority filtering occurs only after a saved
snapshot and must not be put back into Kawasaki dynamics or substituted for
the primary off-critical connected-correlation analysis. See
`research/REFERENCE_BENCHMARK_PROTOCOL.md`.

New work: [start here](docs/START_HERE.md), [research design and report plan](research/STUDY_DESIGN.md), [finite-size campaign protocol](research/PROTOCOL.md),
[tennis-string experiment protocol](experiments/PROTOCOL.md), and
[one-page review brief](docs/review_brief.html). The tennis work is a separate
mechanics experiment, not validation of the Ising model. No physical string
measurements are included yet.

The Solara dashboard now offers **Export raw research data** when paused after
a run. Its ZIP contains unmodified directional lengths, signed heat flow,
parameters and a lattice snapshot. Display floors/smoothing are excluded.
Live trajectories are exploratory: initialization seed alone does not reproduce
the dynamics RNG. Use `python -m research.campaign` for seeded replica ensembles.
The live slope is no longer clipped to a theoretical range, and the reduced
temperature readout uses the anisotropic critical temperature.

For the new tools:

```bash
python -m research.campaign --plan research/plans/pilot.json --output research/runs/pilot --hours 1
python -m research.analyse_campaign research/runs/pilot
python -m research.compare_estimators research/runs/pilot --output research/runs/pilot/new_estimator_analysis
python -m experiments.string_lab --help
```

Most new campaign output remains git-ignored, but the completed main, pilot
and fresh observation-repeat archives in [the data guide](research/DATA_README.md)
are included in this snapshot. The 0.6Tc literature benchmark is incomplete
(7/40 planned runs), and the longer 0.65Tc extension has not started. The
tracked `manuscript/main.pdf` is **older than** `manuscript/main.tex`; use the
source as a working draft and rebuild and check a new PDF before sharing any
paper as a report.

Run the fast physics-contract checks with:

```bash
python -m unittest discover -s tests -v
```

The tests independently check energy bookkeeping, exact Kawasaki composition
conservation, periodic component labelling, LSW normalization, the exact
critical-temperature relation, and the regular-solution mapping. The same
suite runs in GitHub Actions on pushes and pull requests. `CITATION.cff`
provides software citation metadata, and `EXTERNAL_REVIEW.md` is a bounded
technical-review packet rather than a request for a general endorsement.
`AI_USE_AND_CONTRIBUTIONS.md` records the project's AI-assisted provenance and
the verification still required before an external release.

Public research progress and limitations are collected in
[the progress log](docs/PROGRESS_AND_LIMITS.md). Personal application and
outreach notes are deliberately kept out of this public research snapshot.

## License

MIT
