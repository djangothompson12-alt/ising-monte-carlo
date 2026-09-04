# CLAUDE.md

Project-level guidance for working in this repository. See `README.md` for
the full physics writeup and user-facing docs; this file is oriented at
quickly getting a Claude session productive in the code.

## Repository shape

Two independent Ising-model implementations share this repo, each fully
self-contained in its own directory:

- **`model_a/` ("Model A")** — non-conserved order parameter (Metropolis
  single-spin-flip dynamics): `ising_engine.py` (Numba engine), `visualizer.py`,
  `main.py`, `plot_kinetics.py`, plus its own `results/`/`figures/` output
  dirs. `index.html` (standalone browser demo, no server) reimplements the
  same physics in JavaScript and stays at the repo root since it's a static
  asset with no Python dependency. `manuscript/` (a revtex4-2 PRL-format
  paper, compiled with `pdflatex`) also stays at the root, covering both models.
- **`model_b/` ("Model B")** — conserved order parameter (Kawasaki spin-exchange
  dynamics). Fully standalone: does not import from or depend on anything
  outside `model_b/`.
- **`comparative_analysis.py`** (repo root) — the one script that
  legitimately spans both models: reads the CSV each model's own kinetics
  script already produces and plots their domain-growth scaling side by
  side. See "`comparative_analysis.py`" below.

Both `model_a/` and `model_b/` were previously flattened into the repo root
(`model_a/`'s files lived directly at the root) before being split out for
symmetry with `model_b/`'s already-established self-contained layout --
if you're looking at history predating that move, `ising_engine.py` etc.
were at the top level.

Model B is the actively-developed part as of this writing.

## `model_a/` in detail

| File | Purpose |
|---|---|
| `ising_engine.py` | Numba JIT-compiled Metropolis single-spin-flip core + observable calculation (magnetization, energy, specific heat, susceptibility) and the domain-size/entropy-production quench-kinetics helpers. |
| `visualizer.py` | Publication-quality figure generation (matplotlib): `plot_phase_transitions`, `plot_spin_domains`, and the shared `_apply_publication_style` rcParams helper. |
| `main.py` | CLI entry point: runs a temperature sweep, saves `results/observables.csv` + `figures/fig1_phase_transitions.png` / `fig2_spin_domains.png`. |
| `plot_kinetics.py` | Runs a quench, saves `results/quench_kinetics.csv` + `figures/fig3_kinetics_entropy.png` (domain growth `L(t) ~ t^(1/2)` fit + entropy production). |
| `concentration_sweep.py` | Control/contrast for `model_b/concentration_sweep.py`: fits the growth exponent across the same concentrations under non-conserved dynamics. Saves `results/concentration_exponent_sweep.csv` + `figures/fig_concentration_exponent.png`. |

Run with:
```bash
python model_a/main.py
python model_a/plot_kinetics.py
python model_a/concentration_sweep.py
```
(or `cd model_a && python main.py` / etc).

`QuenchConfig.concentration` (default 0.5) sets the initial up-spin
fraction. Because single-spin-flip dynamics doesn't conserve magnetization,
an off-critical initial bias here is transient — the minority phase
eventually gets absorbed rather than surviving as a stable droplet
population (contrast with Model B below). It's still a meaningful control:
curvature-driven wall motion coarsens at the same `t^(1/2)` rate regardless
of which phase started as the minority, for as long as that phase survives.

## `model_b/` in detail

| File | Purpose |
|---|---|
| `kawasaki_engine.py` | Numba JIT-compiled Kawasaki Monte Carlo core. Anisotropic couplings `Jx`, `Jy`; conserves total magnetization exactly. Physics-only, no UI dependencies — retained unchanged through the Streamlit→Solara migration and every subsequent layout revision; the ΔE formula and exact conservation were independently verified against a brute-force Hamiltonian recomputation and haven't needed to change since. |
| `plot_kawasaki_kinetics.py` | Batch CLI (renamed from `run_simulation.py` for parity with `model_a/plot_kinetics.py`): runs a quench, saves `results/kawasaki_kinetics.csv` + `figures/fig_anisotropic_kinetics.png`. |
| `live_visualizer.py` | Native desktop dashboard (matplotlib + Tk, `FuncAnimation`). No Streamlit/Solara dependency. |
| `solara_app.py` | **Web dashboard, built on [Solara](https://solara.dev/)** (`import solara`). Renamed from `app.py` during the model_a/model_b directory split. Migrated off Streamlit specifically for zero-flicker reactive rendering (see "Plotly" below) — do not reintroduce `streamlit` here. |

Run the web dashboard with:
```bash
solara run model_b/solara_app.py
```
(Solara apps use the `solara` CLI, not `python solara_app.py`.) Default port `8765`.

### `solara_app.py` architecture

- **State**: `solara.use_reactive()` for the four sidebar controls (anisotropy
  ratio, quench temperature, lattice size, sweeps/frame). A `SimState` class,
  instantiated once per browser session via `solara.use_memo(..., [sim_key])`
  (a fresh instance whenever `L`/`Jy`/`T_final`/an explicit Reset counter
  changes), holds the lattice array, the four history lists, and the three
  live `FigureWidget` references as **plain (non-reactive) attributes** —
  only `state.metrics` (a small `SimMetrics` dataclass: sweep count, energy,
  concentration) and `state.running` are `solara.reactive()`.
- **Live updates bypass Solara's render cycle almost entirely.** A
  `solara.lab.use_task` background async task (tied to `SimState`'s identity,
  auto-cancelled on reset/param change) advances the simulation on every
  `FRAME_INTERVAL` tick (~20 Hz) and, instead of publishing through reactive
  fields, mutates `state.lattice`/history lists directly and pushes the new
  values straight onto the already-mounted `FigureWidget`s' own traits
  (`widget.data[i].x = ...`, wrapped in `widget.batch_update()`). Only
  `state.metrics` goes through an actual reactive publish, throttled to
  every `_METRICS_UPDATE_EVERY_N_TICKS` ticks (~5 Hz) — that's the only
  thing that still needs a Solara re-render (the numeric readout row).
- **Why not just publish reactive state every tick (simpler, and what this
  app used to do):** it crashes. Continuously driving a `@solara.component`
  re-render at animation speed — regardless of whether the background work
  is a `solara.use_thread`, an asyncio `use_task`, one reactive field per
  tick or six, or splitting the fast-changing state into its own component —
  eventually races reacton's own render scheduler and raises `RuntimeError:
  Too many renders triggered, your render loop does not stop`. This was
  confirmed present even in the very first pre-Solara-lab version of this
  file (i.e. it's not something introduced by any later refactor) and is a
  real fragility in Solara 1.61.0's `auto_subscribe_force_update_counter`
  machinery when a component's render body has a continuously-changing
  reactive dependency, not an app bug fixable by rearranging *which*
  reactive fields get published or how often. The only fix that eliminated
  it (rather than just reducing how often it surfaced) was to stop routing
  the animation through Solara's reactive/render system altogether and
  patch the persistent widgets' ipywidgets traits directly instead — which
  is also the standard, native way live-updating `FigureWidget`s are done
  in plain Jupyter, with or without a React-like framework involved.
- **`_LiveFigure`, not `solara.FigurePlotly`**: a small local component
  (`_LiveFigure`) mounts each `go.FigureWidget` once per `SimState` (keyed
  on the `state` object's identity) and hands the live widget reference back
  via an `on_ready` callback stored onto `state`; `solara.FigurePlotly` isn't
  used for the three live charts because its own reactive-diffing
  (`fig_widget.add_traces(fig.data)` then trim to the tail slice, re-run via
  `use_effect` on every prop change) is *also* what caused the double-legend
  bug below — the app builds a fresh `go.Figure` every tick (not through
  `_LiveFigure`, only for the one-time initial mount), and `FigurePlotly`'s
  add-then-trim churn couldn't reliably keep the frontend's legend DOM in
  sync with that at animation speed.
- **`FigureWidget.data` can only be reassigned a permutation of a *subset*
  of its own current traces** — plotly.py raises `ValueError` on a plain
  `widget.data = [fresh_trace, ...]`. `_LiveFigure`'s mount effect clears
  first (`widget.data = ()`, a valid empty subset) and then
  `widget.add_traces(...)`, exactly mirroring what `solara.FigurePlotly`
  does internally, since that clear-then-add step turned out not to be
  optional cosmetic churn but the only way plotly.py permits populating a
  `FigureWidget`'s traces at all after construction. This same effect
  re-fires on Reset (keyed on the new `SimState`'s identity) so the
  survives-across-resets widget instance doesn't accumulate a second copy
  of the traces alongside the first.
- **Stable trace `uid`s** (`uid="domain-lx"`, `"domain-ly"`, `"entropy-sdot"`,
  `"lattice-heatmap"`) on every trace built by `build_domain_figure` /
  `build_entropy_figure` / `build_lattice_figure`: without them, a brand
  new `go.Scatter()` gets a fresh random `uid` on every construction, and
  Plotly.js's frontend legend reconciliation doesn't reliably recognize it
  as "the same trace, updated" across a widget patch — this was the direct
  cause of a double-legend bug (`Lx(t)`, `Ly(t)` each appearing twice) seen
  before these were added.
- **Critical gotcha (still applies to the two remaining reactive fields,
  `state.metrics` and `state.running`)**: Solara's reactive change-detection
  short-circuits to "unchanged" on Python object identity (`a is b`).
  Mutating a value in place and reassigning the *same* object will
  **silently fail to trigger a re-render**. `SimMetrics` is a fresh
  dataclass instance published each throttled tick, never mutated in place.
- **Plotly / `anywidget`**: `go.FigureWidget` (ipywidgets-based) is what
  makes any of the above possible — it's the same persistent-widget
  mechanism `solara.FigurePlotly` is built on, just driven directly here
  instead of through Solara's component tree. Requires the `anywidget`
  package (a transitive need of Plotly's `FigureWidget`, not obvious from
  Plotly's own dependency list — surfaced by testing, not by reading docs).
- **Modebar hidden**: `widget._config = {"displayModeBar": False}`, set once
  in `_LiveFigure`'s mount effect. `solara.FigurePlotly` has no public way
  to pass Plotly's `config` through (its signature doesn't accept one, and
  `go.FigureWidget(config=...)` raises at construction) — only reachable by
  holding the raw widget reference, which is another reason the live charts
  bypass `FigurePlotly` here.

### Layout

Deliberately **not** `solara.Sidebar()`: that component renders into
`AppLayout`'s navigation-drawer portal, which floats/overlays the main
content by default (Vuetify's `v-navigation-drawer`) rather than reliably
pushing it aside. Instead, `Page()` uses a plain two-column flexbox built
from `solara.Row`/`solara.Column`:

- Left column: fixed `width: 280px; flex-shrink: 0` — the controls sidebar,
  ending in a collapsible `solara.Details` for the materials-science context.
- Right column: `flex-grow: 1; min-width: 0` — main content (title, metrics,
  charts). Can't overlap the left column by construction.

Sized to fit inside one 1080p viewport with no vertical scrolling. The
right column's `LiveDashboard` component (see architecture notes above) is:
- A single horizontal metrics bar (sweep count, energy, concentration, Jx/Jy).
- Below that, `solara.Columns([1, 1])`: a **fixed 340×340px** `Card` for the
  lattice heatmap (Plotly figure itself also set to
  `width=340, height=340, autosize=False` — the figure and its wrapping Card
  must stay in sync or the box stops being square, and this is the one panel
  that's deliberately *not* responsive, since a 1:1 aspect ratio has to be
  pixel-exact) in the left slot, and the domain-growth / entropy-production
  charts **stacked vertically** (each a `Card` sized to `_CHART_HEIGHT + 60`
  = 260px, `_CHART_HEIGHT = 200`) in the right slot.
- Both line-plot `Card`s use `autosize=True` on their Plotly figure and a
  flexible container width, so they respond to window/column resizing
  rather than staying a fixed pixel size — the square lattice panel is the
  one deliberate exception.

All three Plotly figures use explicit (log-space, for the two line plots)
axis ranges rather than autorange, so the charts render fully-formed —
correct axes, gridlines, labels — from the very first frame (`t=0`, before
Start is ever clicked), not just once enough data points exist. The line
charts' x-axis range is extended live (`widget.layout.xaxis.range = ...`,
inside the same `batch_update()` as the data update) as `sweep_count` grows,
rather than ever left on autorange.

### Materials Science & Engineering panel

Condensed to three direct, physically-grounded bullets (not long-form prose)
— each ties a real, named materials phenomenon to the specific simulated
quantity that demonstrates it, rather than a generic analogy: Spinodal
Phase Separation (`L(t) ~ t^(1/3)`), Directional Precipitate Rafting
(`J_x != J_y`), and Trajectory Entropy Production Rate. Written in plain
prose (an explicit later request moved it off LaTeX/formal notation), unlike
the sidebar's slider labels and metric tiles, which do use inline LaTeX.

**Confirmed** (contradicts an earlier note in this file that used to sit
here): `solara.Markdown` genuinely runs inline `$...$` through a real KaTeX
renderer — verified via a live probe app and by inspecting the rendered
DOM (`class="katex"`, real `<math>`/MathML output), not literal dollar-sign
text. This is *not* true of `solara.Text`, which escapes raw HTML instead
of rendering it (also verified live) — that's why the sidebar's LaTeX
labels (`_metric`/`_slider_label`, `markdown=True`) go through
`solara.Markdown`, not `solara.Text`. One correctness gotcha that follows
from this: a markdown-mode label must never be passed through Python's
`.upper()` — case-folding LaTeX source is unsafe in general (e.g. `\alpha`
-> `\ALPHA` is not a valid command and silently breaks the render).

See `_MATERIALS_SCIENCE_MARKDOWN` in `solara_app.py` for the exact text rendered in
the UI's `Details` panel.

## Testing without a browser

This environment has no browser access. Verification for `solara_app.py` relies on:
1. `python -m py_compile model_b/solara_app.py`
2. Headless component render — catches real bugs (e.g. a missing `anywidget`
   dependency surfaced exactly this way) before ever starting a server:
   ```python
   import sys; sys.path.insert(0, "model_b")
   import solara_app, reacton
   box, rc = reacton.render(solara_app.Page(), handle_error=False)  # raises on error
   rc.close()
   ```
3. A real `solara run` server + `curl` for an HTTP/health check and a log scan.

None of these confirm actual rendered pixel layout — only that the component
tree, reactive wiring, and Plotly figure specs are structurally correct. Flag
that limitation rather than claiming visual confirmation that wasn't done.

## Dependencies

`requirements.txt` covers both Model A and Model B. Notable pins/notes live
as inline comments there (e.g. numba's dropped x86_64 macOS wheels past
0.62.1 on Intel Macs; the Solara version this was tested against).
