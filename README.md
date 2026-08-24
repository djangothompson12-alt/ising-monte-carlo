# 2D Ising Model Monte Carlo Engine

**🔴 [Live Demo](https://djangothompson12-alt.github.io/ising-monte-carlo/)** — real-time Metropolis dynamics running in-browser via HTML5 Canvas, with live Chart.js plots of magnetization and energy.

A from-scratch, Numba-accelerated Metropolis Monte Carlo simulation of the two-dimensional square-lattice Ising model, built to generate quantitative thermodynamic data (order parameter, energy, specific heat, and susceptibility) across the ferromagnetic phase transition.

This engine was developed as the computational component of a research paper examining statistical-mechanical entropy and its relationship to philosophical treatments of time (eternalism / the "block universe" view). The code below is self-contained physics and simulation infrastructure; it makes no philosophical claims on its own.

<p align="center">
  <img src="figures/fig1_phase_transitions.png" width="700" alt="Phase transition observables vs. temperature">
</p>

<p align="center">
  <img src="figures/fig2_spin_domains.png" width="700" alt="Spin domain snapshots across the phase transition">
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

## Repository structure

```
.
├── index.html          # Standalone live demo (Canvas + Chart.js, no build step)
├── ising_engine.py     # Numba-jitted Metropolis MC core + observable calculation
├── visualizer.py       # Publication-quality figure generation (matplotlib)
├── main.py             # CLI entry point: runs the sweep, saves data + figures
├── requirements.txt
├── figures/             # Generated PNGs (fig1, fig2)
└── results/             # Generated observables.csv
```

### Live demo (`index.html`)

A self-contained, single-file browser simulation — open `index.html` directly (or visit the [live demo](https://djangothompson12-alt.github.io/ising-monte-carlo/)) to run Metropolis dynamics interactively at ~60 FPS. It reimplements the same physics as `ising_engine.py` (including an external field term $H = -J\sum_{\langle i,j\rangle}\sigma_i\sigma_j - H\sum_i \sigma_i$) directly in JavaScript, rendered with an HTML5 Canvas pixel buffer, with live [Chart.js](https://www.chartjs.org/) plots of magnetization and energy. Sliders control temperature, external field, lattice size, and sweeps per frame — no build step or server required.

- **`ising_engine.py`** — `SimulationConfig` (lattice size, temperature range, equilibration/sampling sweeps), the JIT-compiled Metropolis sweep and energy/magnetization kernels, and `run_temperature_sweep` / `sample_snapshot` for producing sweep-level and single-temperature results.
- **`visualizer.py`** — `plot_phase_transitions` (4-panel $|M|$, $E$, $C_v$, $\chi$ vs. $T$) and `plot_spin_domains` (lattice snapshots at representative temperatures).
- **`main.py`** — orchestrates a full run: temperature sweep → `results/observables.csv` → `figures/fig1_phase_transitions.png` and `figures/fig2_spin_domains.png`.

## Installation

Requires Python 3.10–3.13.

```bash
git clone https://github.com/<your-username>/ising-monte-carlo.git
cd ising-monte-carlo
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Note (Intel macOS only):** numba's PyPI wheels for `x86_64` macOS stop at version `0.62.1`; on Intel Macs, pin with `pip install "numba==0.62.1"` before installing the rest of `requirements.txt`. Apple Silicon, Linux, and Windows are unaffected.

## Usage

Run the full pipeline with default parameters ($L=24$, $T \in [1.2, 3.6]$, 40 temperature points):

```bash
python main.py
```

This prints progress to stdout, writes `results/observables.csv`, and generates both figures in `figures/`. A full run at the defaults completes in well under a minute on a modern laptop (Numba JIT-compiles the Metropolis kernel on first call).

Customize the simulation via CLI flags:

```bash
python main.py \
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
from ising_engine import SimulationConfig, run_temperature_sweep, sample_snapshot

config = SimulationConfig(L=32, t_min=1.5, t_max=3.0, n_temperatures=30)
result = run_temperature_sweep(config)   # result.temperatures, .magnetization, .energy, ...

lattice = sample_snapshot(T=2.269, config=config, seed=0)  # (L, L) array of +-1
```

## Verification

The generated `fig1_phase_transitions.png` shows the expected signatures of a second-order phase transition: $\langle |M| \rangle$ drops from near 1 to near 0 across $T_c$, $\langle E \rangle$ rises smoothly, and both $C_v$ and $\chi$ peak sharply near $T_c \approx 2.269$ — consistent with Onsager's exact solution. `fig2_spin_domains.png` shows a single dominant magnetic domain at $T = 1.5$, scale-spanning clusters at $T \approx T_c$, and fine-grained disorder at $T = 3.5$.

## License

MIT
