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

import sys
import threading
import time
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import solara

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
_CHART_MARGIN = dict(l=40, r=20, t=30, b=40)
_CHART_HEIGHT = 300
_DOMAIN_Y_MIN = 0.3  # upper bound is L/2 (r_max), computed per-call since it depends on lattice size
_ENTROPY_FLOOR = 1e-7
_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX = 1e-5, 1.0
_ENTROPY_SMOOTHING_WINDOW = 10
_SEED = 2026

# Target refresh interval for the live panel, in seconds (~20 Hz).
FRAME_INTERVAL = 0.05

# How long the background thread sleeps between polls while paused, so it
# isn't a hot busy-loop but still notices Start being clicked promptly.
_IDLE_POLL_INTERVAL = 0.05


# ---------------------------------------------------------------------------
# Physics helpers (small, local copies -- see model_b/live_visualizer.py for
# the same pattern; kept framework-agnostic so they don't depend on Solara,
# Streamlit, or anything else UI-related)
# ---------------------------------------------------------------------------


def init_balanced_lattice(L: int, seed: int) -> np.ndarray:
    """Build an L x L lattice with an exact 50/50 +-1 split.

    Kawasaki dynamics conserves total magnetization exactly, so an exact
    (not merely expected-value) balance keeps the run at the symmetric
    quench point for its entire duration.
    """
    N = L * L
    if N % 2 != 0:
        raise ValueError("L*L must be even for an exact 50/50 split")
    spins = np.empty(N, dtype=np.int8)
    spins[: N // 2] = 1
    spins[N // 2 :] = -1
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


def build_lattice_figure(lattice: np.ndarray) -> go.Figure:
    """Build the lattice heatmap. No axis ticks, labels, or colorbar."""
    fig = go.Figure(
        data=go.Heatmap(
            z=lattice,
            zmin=-1,
            zmax=1,
            colorscale=[[0.0, _SPIN_DOWN_COLOR], [1.0, _SPIN_UP_COLOR]],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=480)
    return fig


def _log_range(lo: float, hi: float) -> list[float]:
    """Convert a linear (lo, hi) axis range into the log10-space values
    Plotly's `range` expects when an axis has type="log"."""
    return [np.log10(lo), np.log10(hi)]


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
                mode="lines+markers", name="Lx(t)",
                marker=dict(symbol="circle", size=5), line=dict(color=_DOMAIN_LX_COLOR, width=1.5),
            ),
            go.Scatter(
                x=x, y=Ly_hist if has_data else [],
                mode="lines+markers", name="Ly(t)",
                marker=dict(symbol="square", size=5), line=dict(color=_DOMAIN_LY_COLOR, width=1.5),
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
        margin=_CHART_MARGIN, height=_CHART_HEIGHT,
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
                mode="lines+markers", name="S_dot(t)",
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
    fig.update_layout(margin=_CHART_MARGIN, height=_CHART_HEIGHT, showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# Per-session simulation state
# ---------------------------------------------------------------------------


class SimState:
    """One instance per browser session (created via solara.use_memo inside
    Page(), keyed on the parameters that should force a fresh run -- L,
    Jy, T_final, and an explicit reset counter). Bundles the lattice and
    history arrays as solara.reactive() fields so updating them from the
    background worker thread (see Page()) triggers re-rendering of exactly
    the components that read them.
    """

    def __init__(self, L: int, seed: int) -> None:
        self.L = L
        self.lattice = solara.reactive(init_balanced_lattice(L, seed))
        self.sweep_count = solara.reactive(0)
        self.t_history: solara.Reactive[list[float]] = solara.reactive([])
        self.Lx_history: solara.Reactive[list[float]] = solara.reactive([])
        self.Ly_history: solara.Reactive[list[float]] = solara.reactive([])
        self.Sdot_history: solara.Reactive[list[float]] = solara.reactive([])
        self.running = solara.reactive(False)


def _metric(label: str, value: str) -> None:
    """A small Streamlit-st.metric-like label-over-value display."""
    with solara.Column(gap="0px", style={"text-align": "center", "min-width": "110px"}):
        solara.Text(
            label.upper(),
            style={"font-size": "0.7rem", "color": "#666", "letter-spacing": "0.03em"},
        )
        solara.Text(value, style={"font-size": "1.3rem", "font-weight": "600"})


_MATERIALS_SCIENCE_MARKDOWN = """
Kawasaki exchange dynamics is a *conserved-order-parameter* model, and the
same coarsening mathematics shows up (with varying degrees of fidelity) in
several real materials phenomena:

**Binary alloy spinodal decomposition.** This is close to a literal
correspondence, not just an analogy: this simulation *is* the standard
lattice-gas realization of a binary A/B alloy (or fluid mixture) quenched
into an unstable region of its phase diagram. Spin up/down represents
atomic species A/B, conserved magnetization represents conserved alloy
composition, and the coarsening exponent measured here, L(t) ~ t^(1/3)
(Lifshitz-Slyozov), is the same law used to describe Ostwald ripening of
precipitates in real alloys.

**Directional grain alignment in rolled sheet metals.** Rolling imposes a
strongly preferred direction on a metal sheet, producing elongated,
texture-aligned grains along the rolling direction. The mechanism here is
different (plastic deformation and recrystallization, not diffusive phase
separation), but the *qualitative* outcome is the same kind of thing
visualized in the left panel: making one lattice direction "easier" than
the other (Jx != Jy here; rolling strain there) produces visibly elongated,
anisotropic domains/grains rather than isotropic ones.

**Single-crystal superalloy microstructures.** Ni-based superalloy turbine
blades are grown as single crystals along a preferred crystallographic
direction specifically to exploit anisotropic mechanical properties. Under
applied stress at high temperature, their gamma-prime precipitates coarsen
*directionally* ("rafting"), driven by elastic anisotropy -- a genuine,
well-documented materials phenomenon that is conceptually the closest
real-world parallel to what Jx != Jy produces here: an external asymmetry
biasing which direction domains preferentially grow along.
"""


@solara.component
def Page() -> None:
    # --- Sidebar controls (per-session, via use_reactive) ---
    anisotropy_ratio = solara.use_reactive(2.0)
    T_final = solara.use_reactive(1.0)
    L_value: solara.Reactive[int] = solara.use_reactive(128)
    sweeps_per_frame = solara.use_reactive(10)
    reset_counter, set_reset_counter = solara.use_state(0)

    Jx = 1.0
    Jy = Jx / anisotropy_ratio.value

    # Recreate simulation state (fresh lattice, cleared histories, thread
    # restarted) whenever L, Jy, T_final, or the explicit Reset counter
    # changes -- mirrors the sim_key-triggered reinit pattern used
    # throughout this project's other dashboards.
    sim_key = (L_value.value, round(Jy, 4), round(T_final.value, 4), reset_counter)
    state: SimState = solara.use_memo(lambda: SimState(L_value.value, _SEED), [sim_key])

    def worker(cancel: threading.Event) -> None:
        """Background thread: advances the simulation while state.running is
        True, publishing new (copied) values to the reactive fields above --
        never mutating and reassigning the *same* object, since Solara's
        reactive change-detection short-circuits on `is` identity and would
        otherwise miss the update.
        """
        working_lattice = state.lattice.value.copy()
        while not cancel.is_set():
            if not state.running.value:
                time.sleep(_IDLE_POLL_INTERVAL)
                continue

            beta = 1.0 / T_final.value
            n_sweeps = sweeps_per_frame.value
            total_dE = 0.0
            for _ in range(n_sweeps):
                total_dE += _kawasaki_sweep(working_lattice, beta, Jx, Jy)
            new_sweep_count = state.sweep_count.value + n_sweeps

            r_max = state.L // 2
            Cx, Cy = _axis_correlation_xy(working_lattice, r_max)
            Lx = domain_size_from_correlation(Cx)
            Ly = domain_size_from_correlation(Cy)

            dE_per_sweep_per_spin = (total_dE / n_sweeps) / (state.L * state.L)
            Sdot = max(-dE_per_sweep_per_spin / T_final.value, _ENTROPY_FLOOR)

            state.sweep_count.value = new_sweep_count
            state.t_history.value = state.t_history.value + [float(new_sweep_count)]
            state.Lx_history.value = state.Lx_history.value + [Lx]
            state.Ly_history.value = state.Ly_history.value + [Ly]
            state.Sdot_history.value = state.Sdot_history.value + [Sdot]
            state.lattice.value = working_lattice.copy()

            time.sleep(FRAME_INTERVAL)

    # Tied to `state`'s identity: a new SimState (L/Jy/T_final/Reset change)
    # cancels the old thread and starts a fresh one automatically.
    solara.use_thread(worker, dependencies=[state])

    with solara.Sidebar():
        solara.Markdown("## Model B Controls")
        solara.Text(
            "Kawasaki spin-exchange dynamics (conserved order parameter)",
            style={"color": "#666", "font-size": "0.85rem"},
        )
        solara.SliderFloat(
            "Anisotropy Ratio Jx / Jy", value=anisotropy_ratio, min=0.1, max=3.0, step=0.1,
        )
        solara.Text(
            "Jx is held fixed at 1.0; this slider sets Jy = Jx / ratio.",
            style={"color": "#888", "font-size": "0.75rem"},
        )
        solara.SliderFloat("Quench Temperature Tf", value=T_final, min=0.1, max=2.5, step=0.1)
        solara.Select("Lattice Size L", value=L_value, values=[64, 128])
        solara.SliderInt(
            "MC Sweeps per Frame Update", value=sweeps_per_frame, min=1, max=200, step=1,
        )

        with solara.Row(gap="8px"):
            solara.Button("Start", on_click=lambda: state.running.set(True), color="primary")
            solara.Button("Pause", on_click=lambda: state.running.set(False))
            solara.Button("Reset", on_click=lambda: set_reset_counter(reset_counter + 1))

        solara.Text(
            f"Jx={Jx:.2f}, Jy={Jy:.3f}  (ratio={anisotropy_ratio.value:.2f})",
            style={"color": "#666", "font-size": "0.8rem"},
        )

        with solara.Details(summary="Materials Science & Engineering Context"):
            solara.Markdown(_MATERIALS_SCIENCE_MARKDOWN)

    # --- Main area ---
    solara.Title("Model B: Kawasaki Dynamics")
    solara.Markdown("# Model B: Live Kawasaki Exchange Dashboard")
    solara.Text(
        "Conserved-order-parameter (Model B) coarsening -- spin-exchange dynamics "
        "with independent horizontal/vertical couplings.",
        style={"color": "#666"},
    )

    lattice = state.lattice.value
    t_hist = state.t_history.value
    xlim = (1.0, max(10.0, state.sweep_count.value * 1.5))

    N = state.L * state.L
    n_up = int(np.count_nonzero(lattice == 1))
    concentration = n_up / N
    E = total_energy(lattice, Jx, Jy)

    with solara.Row(justify="space-around", style={"margin": "8px 0 16px 0"}):
        _metric("Sweep Count", f"{state.sweep_count.value:,}")
        _metric("Energy E", f"{E:,.0f}")
        _metric("Concentration", f"{concentration:.4f}")
        _metric("Jx/Jy", f"{Jx / Jy:.2f}")

    with solara.Row(justify="space-between", style={"align-items": "flex-start"}):
        with solara.Column(style={"flex": "1"}):
            solara.Markdown("### Live Lattice (Kawasaki Phase Separation)")
            solara.FigurePlotly(build_lattice_figure(lattice))

        with solara.Column(style={"flex": "1"}):
            solara.Markdown("### Directional Domain Growth")
            solara.FigurePlotly(
                build_domain_figure(t_hist, state.Lx_history.value, state.Ly_history.value, xlim, state.L)
            )

            solara.Markdown("### Entropy Production Rate")
            Sdot_smoothed = moving_average(state.Sdot_history.value, _ENTROPY_SMOOTHING_WINDOW)
            solara.FigurePlotly(build_entropy_figure(t_hist, Sdot_smoothed.tolist(), xlim))

    solara.Text(
        "Status: running" if state.running.value else "Status: paused",
        style={"font-weight": "600", "margin-top": "8px"},
    )
