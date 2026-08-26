# CLAUDE.md

Project-level guidance for working in this repository. See `README.md` for
the full physics writeup and user-facing docs; this file is oriented at
quickly getting a Claude session productive in the code.

## Repository shape

Two independent Ising-model implementations share this repo:

- **Root ("Model A")** — non-conserved order parameter (Metropolis single-spin-flip
  dynamics): `ising_engine.py` (Numba engine), `visualizer.py`, `main.py`,
  `plot_kinetics.py`, `index.html` (standalone browser demo, no server), and
  `manuscript/` (a revtex4-2 PRL-format paper, compiled with `pdflatex`).
- **`model_b/` ("Model B")** — conserved order parameter (Kawasaki spin-exchange
  dynamics). Fully standalone: does not import from or depend on anything in
  the repo root.

Model B is the actively-developed part as of this writing.

## `model_b/` in detail

| File | Purpose |
|---|---|
| `kawasaki_engine.py` | Numba JIT-compiled Kawasaki Monte Carlo core. Anisotropic couplings `Jx`, `Jy`; conserves total magnetization exactly. Physics-only, no UI dependencies — retained unchanged through the Streamlit→Solara migration and every subsequent layout revision; the ΔE formula and exact conservation were independently verified against a brute-force Hamiltonian recomputation and haven't needed to change since. |
| `run_simulation.py` | Batch CLI: runs a quench, saves `results/kawasaki_kinetics.csv` + `figures/fig_anisotropic_kinetics.png`. |
| `live_visualizer.py` | Native desktop dashboard (matplotlib + Tk, `FuncAnimation`). No Streamlit/Solara dependency. |
| `app.py` | **Web dashboard, built on [Solara](https://solara.dev/)** (`import solara`). Migrated off Streamlit specifically for zero-flicker reactive rendering (see "Plotly" below) — do not reintroduce `streamlit` here. |

Run the web dashboard with:
```bash
solara run model_b/app.py
```
(Solara apps use the `solara` CLI, not `python app.py`.) Default port `8765`.

### `app.py` architecture

- **State**: `solara.use_reactive()` for the four sidebar controls (anisotropy
  ratio, quench temperature, lattice size, sweeps/frame). A `SimState` class
  bundles the lattice array and four history lists as `solara.reactive()`
  fields, instantiated once per browser session via
  `solara.use_memo(..., [sim_key])` — a fresh instance is created whenever
  `L`/`Jy`/`T_final`/an explicit Reset counter changes.
- **Live updates**: a background thread via `solara.use_thread` (tied to
  `SimState`'s identity, so it's auto-cancelled on reset/param change)
  advances the simulation while `state.running.value` is `True` and publishes
  new values to the reactive fields.
- **Critical gotcha**: Solara's reactive change-detection short-circuits to
  "unchanged" on Python object identity (`a is b`). Mutating the lattice
  array or a history list in place and reassigning the *same* object will
  **silently fail to trigger a re-render**. Always publish a fresh
  `.copy()` (arrays) or a new list via concatenation (`old + [new]`), never
  `.append()` followed by reassigning the same list.
- **Plotly (the actual zero-flicker mechanism)**: `solara.FigurePlotly` holds
  a persistent ipywidgets `FigureWidget` and patches `.layout`/`.data` in
  place on every re-render — constructing a fresh `go.Figure` each tick
  (which this app does) is fine and does not itself cause flicker; the
  framework handles the in-place patch via ipywidgets' binary/diff sync
  protocol rather than replacing a static `<img>` on every update (which is
  what Streamlit's `st.pyplot`/image-based charts do, and why that approach
  visibly flickered before the migration). Requires the `anywidget` package
  (a transitive need of Plotly's `FigureWidget`, not obvious from Plotly's
  own dependency list — surfaced by testing, not by reading docs).

### Layout

Deliberately **not** `solara.Sidebar()`: that component renders into
`AppLayout`'s navigation-drawer portal, which floats/overlays the main
content by default (Vuetify's `v-navigation-drawer`) rather than reliably
pushing it aside. Instead, `Page()` uses a plain two-column flexbox built
from `solara.Row`/`solara.Column`:

- Left column: fixed `width: 300px; flex-shrink: 0` — the controls sidebar.
- Right column: `flex-grow: 1; min-width: 0` — main content (title, metrics,
  charts). Can't overlap the left column by construction.

Chart grid inside the right column:
- Top row: lattice heatmap in a **fixed 380×380px** `Card` (Plotly figure
  itself also set to `width=380, height=380, autosize=False` — the figure
  and its wrapping Card must stay in sync or the box stops being square,
  and this is the one panel that's deliberately *not* responsive, since a
  1:1 aspect ratio has to be pixel-exact) next to the directional
  domain-growth plot in a `flex-grow: 1` `Card`.
- Below that row, full-width: the entropy-production plot in its own `Card`.
- Both line-plot `Card`s (domain-growth, entropy) use `autosize=True` on
  their Plotly figure and a flexible container width, so they respond to
  window/column resizing rather than staying a fixed pixel size — the
  square lattice panel is the one deliberate exception.

All three Plotly figures use explicit (log-space, for the two line plots)
axis ranges rather than autorange, so the charts render fully-formed —
correct axes, gridlines, labels — from the very first frame (`t=0`, before
Start is ever clicked), not just once enough data points exist.

### Materials Science & Engineering panel

Intentionally condensed to three direct, physically-grounded bullets (not
long-form prose) — each ties a real, named materials phenomenon to the
specific simulated quantity that demonstrates it, rather than a generic
analogy:
- **Binary Alloy Spinodal Decomposition** — `L(t) ~ t^(1/3)` (Lifshitz–Slyozov
  coarsening); this simulation is essentially the standard lattice-gas model
  of a quenched A/B alloy, not just an analogy to one.
- **Directional Precipitate Rafting** — `Jx != Jy` introducing spatial bias,
  mirroring γ′ rafting under stress in Ni-based superalloys.
- **Thermodynamic Irreversibility** — the entropy production rate `S_dot(t)`
  linking microstructural coarsening kinetics to the thermodynamic arrow of
  time.

See `_MATERIALS_SCIENCE_MARKDOWN` in `app.py` for the exact text rendered in
the UI's `Details` panel.

## Testing without a browser

This environment has no browser access. Verification for `app.py` relies on:
1. `python -m py_compile model_b/app.py`
2. Headless component render — catches real bugs (e.g. a missing `anywidget`
   dependency surfaced exactly this way) before ever starting a server:
   ```python
   import sys; sys.path.insert(0, "model_b")
   import app, reacton
   box, rc = reacton.render(app.Page(), handle_error=False)  # raises on error
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
