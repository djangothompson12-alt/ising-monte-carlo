"""
app.py
======

Solara web dashboard for Model B (Kawasaki spin-exchange dynamics):
interactive controls for the anisotropy ratio, quench temperature, lattice
size, and sweeps-per-frame, with a live-updating lattice heatmap and
directional domain-growth / entropy-production plots.

Self-contained within `model_b/`: imports only the Numba-jitted kernels and
FFT-based correlation/domain-size helpers from `kawasaki_engine.py`
(unmodified) and does not touch anything in the repository root or
`manuscript/`.

Usage (Solara apps are launched via the `solara` CLI, not `python`):
    solara run model_b/app.py
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import plotly.graph_objects as go
import solara
import solara.lab
from plotly.graph_objs._figurewidget import FigureWidget as PlotlyFigureWidget

sys.path.insert(0, str(Path(__file__).parent))
from kawasaki_engine import (  # noqa: E402
    _axis_correlation_xy,
    _kawasaki_sweep,
    domain_size_from_correlation,
)

# --- Display constants ---
_SPIN_DOWN_COLOR = "#1f4e79"
_SPIN_UP_COLOR = "#f2f2f2"
_DOMAIN_LX_COLOR = "#1f4e79"
_DOMAIN_LY_COLOR = "#a63603"
_ENTROPY_COLOR = "#6a1b9a"
_CHART_MARGIN = dict(l=45, r=15, t=20, b=35)  # tightened for the 200px-tall stacked charts
_CHART_HEIGHT = 200
_DOMAIN_Y_MIN = 0.3  # upper bound is L/2 (r_max), computed per-call since it depends on lattice size
_ENTROPY_FLOOR = 1e-7
_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX = 1e-5, 1.0
_ENTROPY_SMOOTHING_WINDOW = 10
_SEED = 2026

# Target refresh interval for the live panel, in seconds (~20 Hz). Also used
# as the idle poll interval while paused, so the loop notices Start being
# clicked promptly without being a hot busy-loop.
FRAME_INTERVAL = 0.05

# The visuals (heatmap, both charts) are patched directly onto the persistent
# widgets every tick, at the full FRAME_INTERVAL rate -- but the numeric
# metrics readout still goes through a real solara.reactive() publish, so
# it's throttled separately to keep that reactive-render frequency low.
_METRICS_UPDATE_EVERY_N_TICKS = 4


# ---------------------------------------------------------------------------
# Physics helpers (small, local copies -- see model_b/live_visualizer.py for
# the same pattern; kept framework-agnostic so they don't depend on Solara,
# Streamlit, or anything else UI-related)
# ---------------------------------------------------------------------------


def init_lattice_at_concentration(L: int, seed: int, concentration: float) -> np.ndarray:
    """Build an L x L lattice with an exact `concentration` fraction of +1
    spins (rounded to the nearest integer count) and the rest -1.

    Kawasaki dynamics conserves total magnetization exactly, so an exact
    (not merely expected-value) split keeps the run at the chosen
    concentration for its entire duration -- the live "Concentration"
    metric tile should read the same value throughout a run regardless of
    how far the lattice has coarsened.
    """
    N = L * L
    n_up = round(concentration * N)
    spins = np.empty(N, dtype=np.int8)
    spins[:n_up] = 1
    spins[n_up:] = -1
    rng = np.random.default_rng(seed)
    rng.shuffle(spins)
    return spins.reshape(L, L)


def total_energy(lattice: np.ndarray, Jx: float, Jy: float) -> float:
    """Full-lattice anisotropic Hamiltonian, O(L^2) via vectorized NumPy rolls."""
    right = np.roll(lattice, -1, axis=1)
    down = np.roll(lattice, -1, axis=0)
    return float(-Jx * np.sum(lattice * right) - Jy * np.sum(lattice * down))


def moving_average(values: list[float] | np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average with a growing (partial) window at the start."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return values
    w = max(1, min(window, n))
    cumsum = np.cumsum(np.insert(values, 0, 0.0))
    idx = np.arange(n)
    lo = np.maximum(0, idx - w + 1)
    counts = idx - lo + 1
    return (cumsum[idx + 1] - cumsum[lo]) / counts


# ---------------------------------------------------------------------------
# Plotly figure builders
# ---------------------------------------------------------------------------
#
# All three visualizations are Plotly figures, rebuilt fresh every tick.
# Unlike a plain image-based renderer, Solara's FigurePlotly component holds
# a persistent ipywidgets FigureWidget and patches its layout/data in place
# on every re-render (see FigurePlotly's source: it fetches the *existing*
# widget via solara.get_widget() and updates .layout/.data on it, never
# tearing down and recreating the underlying widget) -- so constructing a
# fresh go.Figure here on the Python side does not by itself cause a
# flicker; the patch-in-place behavior is handled by the framework.
#
# Explicit (log-space) axis ranges are set on every figure rather than left
# to Plotly's autorange: on a log-scale axis, autorange over an empty or
# near-empty trace can produce a degenerate default range before enough
# data exists. Setting a fixed range means the axes -- and grid, and labels
# -- are fully drawn from frame 0, even with zero data points.


_LATTICE_BOX_PX = 340  # fixed square box: both the Plotly figure and its wrapping Card use this


def build_lattice_figure(lattice: np.ndarray) -> go.Figure:
    """Build the lattice heatmap. No axis ticks, labels, or colorbar.

    Explicitly sized (not autosize) to a fixed LATTICE_BOX_PX x LATTICE_BOX_PX
    square -- the wrapping Card in Page() is fixed to the same pixel size, so
    the two can't drift apart or force horizontal scrolling/clipping.
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=lattice,
            zmin=-1,
            zmax=1,
            colorscale=[[0.0, _SPIN_DOWN_COLOR], [1.0, _SPIN_UP_COLOR]],
            showscale=False,
            hoverinfo="skip",
            uid="lattice-heatmap",
        )
    )
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(
        autosize=False, width=_LATTICE_BOX_PX, height=_LATTICE_BOX_PX,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def _log_range(lo: float, hi: float) -> list[float]:
    """Convert a linear (lo, hi) axis range into the log10-space values
    Plotly's `range` expects when an axis has type="log"."""
    return [np.log10(lo), np.log10(hi)]


def _next_decade_x_max(current_sweep: float) -> float:
    """Round the x-axis max up to the next log decade (order of magnitude),
    floored at 100 -- e.g. sweep=42 -> 100, sweep=250 -> 1000, sweep=1400
    -> 10000. Used instead of a tight autorange so the trajectory always has
    a full decade of empty space ahead of it rather than hugging the right
    edge of the plot."""
    return max(100.0, 10 ** np.ceil(np.log10(max(current_sweep, 2))))


_REFERENCE_SLOPE_AMPLITUDE = 1.0  # illustrative anchor for the t^(1/3) guide line's SLOPE, not a fit
_REFERENCE_SLOPE_X = np.logspace(0, 6, 60)  # wide, static log-spaced x-domain -- see build_domain_figure
_REFERENCE_SLOPE_Y = _REFERENCE_SLOPE_AMPLITUDE * _REFERENCE_SLOPE_X ** (1.0 / 3.0)


def build_domain_figure(
    t_hist: list[float], Lx_hist: list[float], Ly_hist: list[float], x_range: tuple[float, float], L: int,
) -> go.Figure:
    """Build the Lx(t)/Ly(t) domain-growth log-log line chart.

    Per len(t_hist) < 2, both traces are given empty x=[]/y=[] rather than
    the single available point, so the (log-scale) axes don't have to
    accommodate a degenerate one-point autorange -- the explicit fixed
    range below already handles that regardless.
    """
    has_data = len(t_hist) >= 2
    x = t_hist if has_data else []
    fig = go.Figure(
        data=[
            go.Scatter(
                x=x, y=Lx_hist if has_data else [],
                mode="lines+markers", name="Lx(t)", uid="domain-lx",
                marker=dict(symbol="circle", size=5), line=dict(color=_DOMAIN_LX_COLOR, width=1.5),
            ),
            go.Scatter(
                x=x, y=Ly_hist if has_data else [],
                mode="lines+markers", name="Ly(t)", uid="domain-ly",
                marker=dict(symbol="square", size=5), line=dict(color=_DOMAIN_LY_COLOR, width=1.5),
            ),
            # Theoretical Lifshitz-Slyozov reference slope, L(t) ~ t^(1/3).
            # Precomputed over a wide, fixed x-domain (well beyond any
            # reachable x_max) rather than per-tick, since it's a static
            # curve for visual slope comparison, not live data -- the
            # worker never touches this trace, so it survives untouched
            # across every direct widget-trait update.
            go.Scatter(
                x=_REFERENCE_SLOPE_X, y=_REFERENCE_SLOPE_Y,
                mode="lines", name="t^(1/3) ref", uid="domain-ref-slope",
                line=dict(color="#999999", width=1.2, dash="dash"), hoverinfo="skip",
            ),
        ]
    )
    fig.update_xaxes(
        type="log", range=_log_range(*x_range), title_text="Time t (sweeps)",
        showgrid=True, gridcolor="#eeeeee",
    )
    fig.update_yaxes(
        type="log", range=_log_range(_DOMAIN_Y_MIN, L / 2.0), title_text="Domain size",
        showgrid=True, gridcolor="#eeeeee",
    )
    fig.update_layout(
        autosize=True, margin=_CHART_MARGIN, height=_CHART_HEIGHT, showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.7)"),
    )
    return fig


def build_entropy_figure(
    t_hist: list[float], Sdot_smoothed: list[float], x_range: tuple[float, float],
) -> go.Figure:
    """Build the S_dot(t) entropy-production log-log line chart.

    Same len(t_hist) < 2 handling as build_domain_figure().
    """
    has_data = len(t_hist) >= 2
    fig = go.Figure(
        data=[
            go.Scatter(
                x=t_hist if has_data else [], y=Sdot_smoothed if has_data else [],
                mode="lines+markers", name="S_dot(t)", uid="entropy-sdot",
                marker=dict(symbol="circle", size=5), line=dict(color=_ENTROPY_COLOR, width=1.5),
            ),
        ]
    )
    fig.update_xaxes(
        type="log", range=_log_range(*x_range), title_text="Time t (sweeps)",
        showgrid=True, gridcolor="#eeeeee",
    )
    fig.update_yaxes(
        type="log", range=_log_range(_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX),
        title_text="S_dot(t), per spin (kB units)", showgrid=True, gridcolor="#eeeeee",
    )
    fig.update_layout(autosize=True, margin=_CHART_MARGIN, height=_CHART_HEIGHT, showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# Per-session simulation state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SimMetrics:
    """Throttled (~5 Hz) numeric readout -- the only field the render tree
    subscribes to reactively. See SimState's docstring for why."""

    sweep_count: int
    energy: float
    concentration: float


class SimState:
    """One instance per browser session (created via solara.use_memo inside
    Page(), keyed on the parameters that should force a fresh run -- L,
    Jy, T_final, concentration, and an explicit reset counter).

    Only `metrics` is a solara.reactive() field, published at a throttled
    ~5 Hz. The lattice, the four history lists, and the three persistent
    Plotly FigureWidget references are plain (non-reactive) attributes
    that the background worker task mutates and patches directly, every
    tick, at the full animation rate -- entirely outside Solara's render
    cycle. See LiveDashboard's docstring for why: driving all of this
    through solara.reactive() at 20 Hz raced reacton's own render
    scheduler and intermittently crashed the session with "too many
    renders triggered", regardless of thread vs. asyncio, how many
    reactive fields were published per tick, or which component read them.
    """

    def __init__(self, L: int, seed: int, Jx: float, Jy: float, concentration: float) -> None:
        self.L = L
        self.running = solara.reactive(False)

        self.lattice = init_lattice_at_concentration(L, seed, concentration)
        self.sweep_count = 0
        self.t_history: list[float] = []
        self.Lx_history: list[float] = []
        self.Ly_history: list[float] = []
        self.Sdot_history: list[float] = []
        self.tick = 0

        # Shared x-axis upper bound for both line charts (see
        # _next_decade_x_max) -- only re-scoped once the trajectory reaches
        # 90% of the current bound, not recalculated every tick, so the line
        # advances across open space instead of the axis constantly rescaling.
        self.x_max = _next_decade_x_max(0)

        self.lattice_widget: Optional[PlotlyFigureWidget] = None
        self.domain_widget: Optional[PlotlyFigureWidget] = None
        self.entropy_widget: Optional[PlotlyFigureWidget] = None

        initial_energy = total_energy(self.lattice, Jx, Jy)
        initial_concentration = int(np.count_nonzero(self.lattice == 1)) / (L * L)
        self.metrics: solara.Reactive[SimMetrics] = solara.reactive(
            SimMetrics(0, initial_energy, initial_concentration)
        )


def _metric(label: str, value: str) -> None:
    """A small Streamlit-st.metric-like label-over-value display."""
    with solara.Column(gap="0px", style={"text-align": "center", "min-width": "110px"}):
        solara.Text(
            label.upper(),
            style={"font-size": "0.7rem", "color": "#666", "letter-spacing": "0.03em"},
        )
        solara.Text(value, style={"font-size": "1.3rem", "font-weight": "600"})


_MATERIALS_SCIENCE_MARKDOWN = """
- **Spinodal Phase Separation**: Models how a two-component mixture un-mixes over time while total concentration remains constant. I'm measuring domain growth L(t) to test if it follows Lifshitz-Slyozov scaling L(t) ~ t^(1/3).
- **Directional Precipitate Rafting**: Unequal horizontal and vertical couplings (Jx != Jy) introduce spatial bias during spin exchange, stretching domains into parallel bands similar to gamma-prime precipitate rafting in nickel superalloys under stress.
- **Trajectory Entropy Rate**: Tracks real-time heat dissipation during spin swaps across Monte Carlo sweeps, providing a quantitative measure of non-equilibrium thermodynamic irreversibility as the system relaxes.
"""


@solara.component
def _LiveFigure(key: object, initial_fig: go.Figure, on_ready: Callable[[PlotlyFigureWidget], None]) -> None:
    """Mounts one persistent go.FigureWidget and hands it back via on_ready.

    Deliberately bypasses solara.FigurePlotly's own reactive-diffing
    (fig_widget.add_traces(...) then trim, re-run through use_effect on
    every prop change): that path is what let stale legend entries survive
    a widget update, and it also means every visual refresh has to flow
    through a Solara re-render. Here, `initial_fig` only matters once --
    `key` (the owning SimState) only changes on Reset/param-change, so this
    mounts (or re-mounts, after Reset) the widget and then gets out of the
    way; all real per-tick updates come later, from the worker directly
    setting `.data[i].x/y/z` on the captured widget instance.
    """
    fig_element = PlotlyFigureWidget.element(layout=initial_fig.layout)

    def _capture():
        widget = solara.get_widget(fig_element)
        widget._config = {"displayModeBar": False}
        # FigureWidget.data can only be reassigned to a permutation of a
        # subset of its *current* traces -- a plain list of freshly built
        # trace objects is rejected outright. Clear (a valid empty subset)
        # then add_traces(): the same two-step solara's own FigurePlotly
        # uses, needed here too so a Reset (which re-fires this effect on
        # the same underlying widget instance) doesn't just accumulate a
        # second copy of the traces alongside the first.
        if len(widget.data):
            widget.data = ()
        widget.add_traces(initial_fig.data)
        on_ready(widget)

    solara.use_effect(_capture, [key])
    return fig_element


@solara.component
def LiveDashboard(state: SimState, Jx: float, Jy: float) -> None:
    """The metrics row + heatmap/chart grid.

    Split out from Page() so this component's render body only reads
    `state.metrics`/`state.running`, not the sidebar's slider reactives
    (anisotropy_ratio, T_final, L_value, sweeps_per_frame) -- and, more
    importantly, so that a metrics-triggered re-render here is *cheap*: it
    no longer has to rebuild and re-diff three Plotly figures every time,
    since the widgets are now patched directly by the worker task (see
    _LiveFigure and SimState's docstrings). Solara's auto-subscribe
    tracking forces an extra stabilizing render pass whenever a reactive
    value a component read changes mid-render; doing that with three full
    figure rebuilds in the loop, at 20 Hz, was fast enough to blow through
    reacton's "too many renders triggered" recursion guard within a couple
    hundred ticks and crash the session -- confirmed present regardless of
    thread vs. asyncio, how many reactive fields were published per tick,
    or isolating this component from the sidebar's reactives alone. Moving
    the actual widget patching outside the reactive/render path entirely
    removes the expensive work that was racing the render scheduler; the
    throttled, lightweight `metrics` re-render that remains is the same
    low-frequency regime any ordinary interactive Solara app runs in.
    """
    metrics = state.metrics.value

    initial_lattice_fig = solara.use_memo(lambda: build_lattice_figure(state.lattice), [state])
    initial_domain_fig = solara.use_memo(
        lambda: build_domain_figure(
            state.t_history, state.Lx_history, state.Ly_history, (1.0, state.x_max), state.L
        ),
        [state],
    )
    initial_entropy_fig = solara.use_memo(
        lambda: build_entropy_figure(state.t_history, state.Sdot_history, (1.0, state.x_max)), [state]
    )

    with solara.Row(justify="space-around", style={"margin": "8px 0 16px 0", "flex-wrap": "wrap"}):
        _metric("Sweep Count", f"{metrics.sweep_count:,}")
        _metric("Energy E", f"{metrics.energy:,.0f}")
        _metric("Concentration", f"{metrics.concentration:.4f}")
        _metric("Jx/Jy", f"{Jx / Jy:.2f}")

    # Bottom dashboard: fixed-size square lattice heatmap in the left
    # column, the two line charts stacked in the right column -- sized
    # to fit both, plus the sidebar/metrics above, within one 1080p
    # screen with no vertical scrolling.
    with solara.Columns([1, 1]):
        with solara.Card(
            style=f"width: {_LATTICE_BOX_PX}px; height: {_LATTICE_BOX_PX + 50}px; flex-shrink: 0;"
        ):
            solara.Markdown("### Live Lattice")
            _LiveFigure(state, initial_lattice_fig, on_ready=lambda w: setattr(state, "lattice_widget", w))

        with solara.Column(gap="12px"):
            with solara.Card(style=f"height: {_CHART_HEIGHT + 60}px;"):
                solara.Markdown("### Directional Domain Growth")
                _LiveFigure(state, initial_domain_fig, on_ready=lambda w: setattr(state, "domain_widget", w))

            with solara.Card(style=f"height: {_CHART_HEIGHT + 60}px;"):
                solara.Markdown("### Entropy Production Rate")
                _LiveFigure(state, initial_entropy_fig, on_ready=lambda w: setattr(state, "entropy_widget", w))

    solara.Text(
        "Status: running" if state.running.value else "Status: paused",
        style={"font-weight": "600", "margin-top": "8px"},
    )


@solara.component
def Page() -> None:
    # --- Sidebar controls (per-session, via use_reactive) ---
    anisotropy_ratio = solara.use_reactive(2.0)
    T_final = solara.use_reactive(1.0)
    concentration = solara.use_reactive(0.50)
    L_value: solara.Reactive[int] = solara.use_reactive(128)
    sweeps_per_frame = solara.use_reactive(10)
    reset_counter, set_reset_counter = solara.use_state(0)

    Jx = 1.0
    Jy = Jx / anisotropy_ratio.value

    # Recreate simulation state (fresh lattice, cleared histories, thread
    # restarted) whenever L, Jy, T_final, concentration, or the explicit
    # Reset counter changes -- mirrors the sim_key-triggered reinit pattern
    # used throughout this project's other dashboards.
    sim_key = (L_value.value, round(Jy, 4), round(T_final.value, 4), round(concentration.value, 4), reset_counter)
    state: SimState = solara.use_memo(
        lambda: SimState(L_value.value, _SEED, Jx, Jy, concentration.value), [sim_key]
    )

    async def worker() -> None:
        """Advances the simulation while state.running is True.

        The lattice and the four history lists live directly on `state` as
        plain mutable attributes (not solara.reactive()), so they're just
        mutated and pushed straight into the persistent FigureWidgets'
        `.data[i].x/y/z` traits every tick -- no Solara re-render involved
        for the animation itself. Only `state.metrics`, throttled to
        roughly 5 Hz, goes through an actual reactive publish. See
        SimState's and LiveDashboard's docstrings for why.
        """
        while True:
            if not state.running.value:
                await asyncio.sleep(FRAME_INTERVAL)
                continue

            beta = 1.0 / T_final.value
            n_sweeps = sweeps_per_frame.value
            total_dE = 0.0
            for _ in range(n_sweeps):
                total_dE += _kawasaki_sweep(state.lattice, beta, Jx, Jy)

            state.sweep_count += n_sweeps
            t = float(state.sweep_count)

            r_max = state.L // 2
            Cx, Cy = _axis_correlation_xy(state.lattice, r_max)
            Lx = domain_size_from_correlation(Cx)
            Ly = domain_size_from_correlation(Cy)

            dE_per_sweep_per_spin = (total_dE / n_sweeps) / (state.L * state.L)
            Sdot = max(-dE_per_sweep_per_spin / T_final.value, _ENTROPY_FLOOR)

            state.t_history.append(t)
            state.Lx_history.append(Lx)
            state.Ly_history.append(Ly)
            state.Sdot_history.append(Sdot)

            # Re-scope the shared x-axis bound only once the trajectory
            # reaches 90% of the current one, rather than every tick -- the
            # line then advances across already-open graph space, and only
            # "scopes out" to the next log decade when it's about to run out
            # of room.
            if t >= 0.9 * state.x_max:
                state.x_max = _next_decade_x_max(t)
            xrange = _log_range(1.0, state.x_max)

            # Direct widget-trait mutation -- copies passed in explicitly
            # rather than the same mutated-in-place list/array object, so
            # a value-identity fast path on the trait setter (if any)
            # can't mistake this for a no-op.
            if state.lattice_widget is not None:
                state.lattice_widget.data[0].z = state.lattice.copy()

            if state.domain_widget is not None:
                with state.domain_widget.batch_update():
                    state.domain_widget.data[0].x = list(state.t_history)
                    state.domain_widget.data[0].y = list(state.Lx_history)
                    state.domain_widget.data[1].x = list(state.t_history)
                    state.domain_widget.data[1].y = list(state.Ly_history)
                    state.domain_widget.layout.xaxis.range = xrange

            if state.entropy_widget is not None:
                Sdot_smoothed = moving_average(state.Sdot_history, _ENTROPY_SMOOTHING_WINDOW).tolist()
                with state.entropy_widget.batch_update():
                    state.entropy_widget.data[0].x = list(state.t_history)
                    state.entropy_widget.data[0].y = Sdot_smoothed
                    state.entropy_widget.layout.xaxis.range = xrange

            state.tick += 1
            if state.tick % _METRICS_UPDATE_EVERY_N_TICKS == 0:
                E = total_energy(state.lattice, Jx, Jy)
                concentration = int(np.count_nonzero(state.lattice == 1)) / (state.L * state.L)
                state.metrics.value = SimMetrics(state.sweep_count, E, concentration)

            await asyncio.sleep(FRAME_INTERVAL)

    # Tied to `state`'s identity: a new SimState (L/Jy/T_final/Reset change)
    # cancels the old task and starts a fresh one automatically.
    solara.lab.use_task(worker, dependencies=[state])

    solara.Title("Model B: Kawasaki Dynamics")

    # Explicit two-column flexbox layout, NOT solara.Sidebar(): Sidebar()
    # renders into AppLayout's navigation-drawer portal, which is a
    # floating/overlay element by default (Vuetify's v-navigation-drawer) --
    # exactly the behavior that was letting it sit on top of the main
    # content instead of pushing it aside. A plain Row of two Columns, one
    # with flex-shrink:0 at a fixed width and the other with flex-grow:1,
    # is a completely standard side-by-side (never-overlapping) flexbox
    # pattern with no dependence on the drawer component at all.
    with solara.Row(style="align-items: flex-start; width: 100%; flex-wrap: nowrap;"):
        with solara.Column(style="width: 280px; flex-shrink: 0; padding: 16px;"):
            solara.Markdown("## Model B Controls")
            solara.Text(
                "Kawasaki spin-exchange dynamics (conserved order parameter)",
                style={"color": "#666", "font-size": "0.85rem"},
            )

            with solara.Card(
                title="Physics Parameters", elevation=1,
                style={"margin": "12px 0", "padding": "0 12px 12px 12px"},
            ):
                with solara.Column(gap="14px", style={"padding": "4px 2px"}):
                    solara.SliderFloat(
                        f"Anisotropy (Jx/Jy): {anisotropy_ratio.value:.2f}",
                        value=anisotropy_ratio, min=0.1, max=3.0, step=0.1,
                    )
                    solara.Text(
                        "Jx is held fixed at 1.0; this slider sets Jy = Jx / ratio.",
                        style={"color": "#888", "font-size": "0.75rem", "margin-top": "-8px"},
                    )
                    solara.SliderFloat(
                        f"Quench Temperature: {T_final.value:.2f}",
                        value=T_final, min=0.1, max=2.5, step=0.1,
                    )
                    solara.SliderFloat(
                        f"Concentration: {concentration.value:.2f}",
                        value=concentration, min=0.10, max=0.90, step=0.05,
                    )

            with solara.Card(
                title="Simulation Engine", elevation=1,
                style={"margin": "12px 0", "padding": "0 12px 12px 12px"},
            ):
                with solara.Column(gap="14px", style={"padding": "4px 2px"}):
                    solara.Select("Lattice Size L", value=L_value, values=[64, 128])
                    solara.SliderInt(
                        f"Sweeps per Frame: {sweeps_per_frame.value}",
                        value=sweeps_per_frame, min=1, max=200, step=1,
                    )

                    with solara.Row(gap="8px", style={"flex-wrap": "wrap"}):
                        solara.Button("Start", on_click=lambda: state.running.set(True), color="primary")
                        solara.Button("Pause", on_click=lambda: state.running.set(False))
                        solara.Button("Reset", on_click=lambda: set_reset_counter(reset_counter + 1))

                    solara.Text(
                        f"Jx={Jx:.2f}, Jy={Jy:.3f}  (ratio={anisotropy_ratio.value:.2f})",
                        style={"color": "#666", "font-size": "0.8rem"},
                    )

            with solara.Details(summary="Materials Science & Engineering Context"):
                solara.Markdown(_MATERIALS_SCIENCE_MARKDOWN)

        with solara.Column(style="flex-grow: 1; min-width: 0; padding: 16px;"):
            solara.Markdown(
                "# Model B: Live Kawasaki Exchange Dashboard",
                style={"white-space": "normal", "overflow-wrap": "break-word"},
            )
            solara.Text(
                "Conserved-order-parameter (Model B) coarsening -- spin-exchange dynamics "
                "with independent horizontal/vertical couplings.",
                style={"color": "#666"},
            )

            LiveDashboard(state, Jx, Jy)
