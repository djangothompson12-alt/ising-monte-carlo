"""
app.py
======

Streamlit web dashboard for Model B (Kawasaki spin-exchange dynamics):
interactive controls for the anisotropy ratio, quench temperature, lattice
size, and sweeps-per-frame, with a live-updating lattice heatmap and
directional domain-growth / entropy-production plots.

Self-contained within `model_b/`: imports only the Numba-jitted kernels and
FFT-based correlation/domain-size helpers from `kawasaki_engine.py`
(unmodified) and does not touch anything in the repository root or
`manuscript/`.

Usage (Streamlit apps are launched via the `streamlit` CLI, not `python`):
    streamlit run model_b/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

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

# Target refresh interval for the live panel, in seconds (~20 Hz). Driven by
# st.fragment(run_every=...) rather than a manual sleep()+st.rerun() loop --
# see the live_dashboard() fragment below for why.
FRAME_INTERVAL = 0.05

st.set_page_config(page_title="Model B: Kawasaki Dynamics", layout="wide")


# ---------------------------------------------------------------------------
# Physics helpers (small, local copies -- see model_b/live_visualizer.py for
# the same pattern; duplicated rather than imported so this file never pulls
# in live_visualizer's matplotlib.use("TkAgg") call, which would conflict
# with Streamlit's server-side Agg rendering)
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
# Persistent figure factories (domain-growth / entropy line plots)
# ---------------------------------------------------------------------------
#
# All three visualizations are Plotly figures, rebuilt fresh every
# st.fragment tick rather than persisted+mutated: constructing a small
# go.Figure is cheap (Plotly ships the trace data as JSON; no server-side
# rasterization happens at all until st.plotly_chart renders it -- unlike
# matplotlib's st.pyplot(), which re-encodes a brand-new PNG image every
# call regardless of how much of the *Python-side* rendering work is
# avoided). That PNG-swap is what st.pyplot() fundamentally does on every
# single call: ship a new image blob, have the browser replace the <img>
# src. Plotly's frontend component instead patches its existing chart
# in place, which is what actually avoids the grey/fade transition -- no
# amount of persisting matplotlib Figure objects server-side changes what
# gets sent to the browser each tick. A stable key= on st.plotly_chart is
# what lets the frontend recognize "this is the same chart, just new data"
# across ticks.
#
# Explicit (log-space) axis ranges are set on every figure rather than
# left to Plotly's autorange: on a log-scale axis, autorange over an
# empty or near-empty trace can produce a degenerate default range before
# enough data exists, which is what caused the domain/entropy panels to
# visually look empty/delayed for the first several ticks. Setting the
# same fixed range we already compute for the x-axis (and a fixed,
# lattice-appropriate range for each y-axis) means the axes -- and grid,
# and labels -- are fully drawn from frame 0, even with zero data points.


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
# Sidebar: controls
# ---------------------------------------------------------------------------

st.sidebar.title("Model B Controls")
st.sidebar.caption("Kawasaki spin-exchange dynamics (conserved order parameter)")

anisotropy_ratio = st.sidebar.slider(
    "Anisotropy Ratio $J_x / J_y$", min_value=0.1, max_value=3.0, value=2.0, step=0.1,
    help="Jx is held fixed at 1.0; this slider sets Jy = Jx / ratio.",
)
T_final = st.sidebar.slider(
    "Quench Temperature $T_f$", min_value=0.1, max_value=2.5, value=1.0, step=0.1,
)
L = st.sidebar.selectbox("Lattice Size $L$", options=[64, 128], index=1)
sweeps_per_frame = st.sidebar.slider(
    "MC Sweeps per Frame Update", min_value=1, max_value=200, value=10, step=1,
)

Jx = 1.0
Jy = Jx / anisotropy_ratio

st.sidebar.divider()
col_start, col_pause, col_reset = st.sidebar.columns(3)
start_clicked = col_start.button("▶ Start", width="stretch")
pause_clicked = col_pause.button("⏸ Pause", width="stretch")
reset_clicked = col_reset.button("↺ Reset", width="stretch")

with st.sidebar.expander("🔬 Materials Science & Engineering Context", expanded=False):
    st.markdown(
        """
Kawasaki exchange dynamics is a *conserved-order-parameter* model, and the
same coarsening mathematics shows up (with varying degrees of fidelity) in
several real materials phenomena:

**Binary alloy spinodal decomposition.** This is close to a literal
correspondence, not just an analogy: this simulation *is* the standard
lattice-gas realization of a binary A/B alloy (or fluid mixture) quenched
into an unstable region of its phase diagram. Spin up/down represents
atomic species A/B, conserved magnetization represents conserved alloy
composition, and the coarsening exponent measured here, $L(t)\\sim t^{1/3}$
(Lifshitz–Slyozov), is the same law used to describe Ostwald ripening of
precipitates in real alloys.

**Directional grain alignment in rolled sheet metals.** Rolling imposes a
strongly preferred direction on a metal sheet, producing elongated,
texture-aligned grains along the rolling direction. The mechanism here is
different (plastic deformation and recrystallization, not diffusive phase
separation), but the *qualitative* outcome is the same kind of thing
visualized in the left panel: making one lattice direction "easier" than
the other ($J_x \\neq J_y$ here; rolling strain there) produces visibly
elongated, anisotropic domains/grains rather than isotropic ones.

**Single-crystal superalloy microstructures.** Ni-based superalloy turbine
blades are grown as single crystals along a preferred crystallographic
direction specifically to exploit anisotropic mechanical properties. Under
applied stress at high temperature, their $\\gamma'$ precipitates coarsen
*directionally* ("rafting"), driven by elastic anisotropy -- a genuine,
well-documented materials phenomenon that is conceptually the closest
real-world parallel to what $J_x \\neq J_y$ produces here: an external
asymmetry biasing which direction domains preferentially grow along.
        """
    )

st.sidebar.caption(
    f"$J_x={Jx:.2f}$, $J_y={Jy:.3f}$  (ratio $={anisotropy_ratio:.2f}$)"
)

# ---------------------------------------------------------------------------
# Session-state simulation bookkeeping
# ---------------------------------------------------------------------------

sim_key = (L, round(Jx, 4), round(Jy, 4), round(T_final, 4))

if reset_clicked or st.session_state.get("sim_key") != sim_key:
    st.session_state.sim_key = sim_key
    st.session_state.lattice = init_balanced_lattice(L, seed=_SEED)
    st.session_state.sweep_count = 0
    st.session_state.t_history = []
    st.session_state.Lx_history = []
    st.session_state.Ly_history = []
    st.session_state.Sdot_history = []
    st.session_state.running = False
    # No figure objects to (re)build here -- all three charts are Plotly,
    # built fresh each fragment tick from these history arrays; see the
    # "Plotly figure builders" section above for why that's the right
    # trade-off (unlike the matplotlib approach this file used previously).

if start_clicked:
    st.session_state.running = True
if pause_clicked:
    st.session_state.running = False

# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

st.title("Model B: Live Kawasaki Exchange Dashboard")
st.caption(
    "Conserved-order-parameter (Model B) coarsening -- spin-exchange dynamics "
    "with independent horizontal/vertical couplings."
)


def advance_one_frame() -> None:
    """Run sweeps_per_frame Kawasaki sweeps and record the resulting observables."""
    beta = 1.0 / T_final
    lattice = st.session_state.lattice
    total_dE = 0.0
    for _ in range(sweeps_per_frame):
        total_dE += _kawasaki_sweep(lattice, beta, Jx, Jy)
    st.session_state.sweep_count += sweeps_per_frame

    r_max = L // 2
    Cx, Cy = _axis_correlation_xy(lattice, r_max)
    Lx = domain_size_from_correlation(Cx)
    Ly = domain_size_from_correlation(Cy)

    dE_per_sweep_per_spin = (total_dE / sweeps_per_frame) / (L * L)
    Sdot = max(-dE_per_sweep_per_spin / T_final, _ENTROPY_FLOOR)

    st.session_state.t_history.append(float(st.session_state.sweep_count))
    st.session_state.Lx_history.append(Lx)
    st.session_state.Ly_history.append(Ly)
    st.session_state.Sdot_history.append(Sdot)


# The live panel is an st.fragment: only ITS contents re-execute on each
# tick, not the whole page (title, sidebar, etc. above are untouched after
# the first run). This replaces the previous approach of a manual
# for-loop + time.sleep() + st.rerun() inside the main script body, which
# tied up the session's script-execution thread for the full duration of
# each batch and re-ran the entire script (full page rebuild) at every
# batch boundary -- the combination that was causing multi-second stalls
# and reset-like behavior under load. run_every is set to None (fragment
# stays static) whenever the sim isn't running, and to FRAME_INTERVAL while
# it is; since this decoration line re-executes on every normal script
# rerun (e.g. a button click), it always reflects the current running state.
@st.fragment(run_every=FRAME_INTERVAL if st.session_state.running else None)
def live_dashboard() -> None:
    if st.session_state.running:
        advance_one_frame()

    lattice = st.session_state.lattice
    t_hist = st.session_state.t_history
    xlim = (1.0, max(10.0, st.session_state.sweep_count * 1.5))

    metric_cols = st.columns(4)
    N = L * L
    n_up = int(np.count_nonzero(lattice == 1))
    concentration = n_up / N
    E = total_energy(lattice, Jx, Jy)
    # st.metric() has no `key` parameter in this Streamlit version (verified
    # -- passing one raises TypeError). Only st.plotly_chart() below
    # genuinely supports one. These four calls instead rely on stable
    # script-position inference, which is already correct here since the
    # same 4 calls happen in the same order every tick.
    metric_cols[0].metric("Sweep Count", f"{st.session_state.sweep_count:,}")
    metric_cols[1].metric("Energy E", f"{E:,.0f}")
    metric_cols[2].metric("Concentration", f"{concentration:.4f}")
    metric_cols[3].metric("Jx/Jy", f"{Jx / Jy:.2f}")

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Live Lattice (Kawasaki Phase Separation)")
        # Rebuilt fresh every tick -- constructing a small go.Figure is cheap
        # (no server-side rasterization happens until st.plotly_chart renders
        # it). The stable key= is what keeps the frontend chart component
        # from flickering across ticks, independent of the Python-side
        # object's identity.
        st.plotly_chart(
            build_lattice_figure(lattice),
            width="stretch",
            config={"displayModeBar": False, "staticPlot": True},
            key="lattice_chart",
        )

    with right_col:
        st.subheader("Directional Domain Growth")
        st.plotly_chart(
            build_domain_figure(t_hist, st.session_state.Lx_history, st.session_state.Ly_history, xlim, L),
            width="stretch",
            config={"displayModeBar": False},
            key="domain_chart",
        )

        st.subheader("Entropy Production Rate")
        Sdot_smoothed = moving_average(st.session_state.Sdot_history, _ENTROPY_SMOOTHING_WINDOW)
        st.plotly_chart(
            build_entropy_figure(t_hist, Sdot_smoothed.tolist(), xlim),
            width="stretch",
            config={"displayModeBar": False},
            key="entropy_chart",
        )

    st.caption("Status: **running**" if st.session_state.running else "Status: **paused**")


live_dashboard()
