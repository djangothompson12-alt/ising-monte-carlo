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

import matplotlib
matplotlib.use("Agg")  # server-side rendering only; this is a web app, not a GUI window
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

sys.path.insert(0, str(Path(__file__).parent))
from kawasaki_engine import (  # noqa: E402
    _axis_correlation_xy,
    _kawasaki_sweep,
    domain_size_from_correlation,
)

# --- Display constants ---
_SPIN_DOWN_COLOR = "#1f4e79"
_SPIN_UP_COLOR = "#f2f2f2"
_LATTICE_CMAP = ListedColormap([_SPIN_DOWN_COLOR, _SPIN_UP_COLOR])
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
# Figures are built via the plain matplotlib.figure.Figure API (not
# plt.subplots()) and never touch pyplot's global figure registry -- the
# officially recommended pattern for using matplotlib from a threaded server
# (each Streamlit user session runs its own script thread; pyplot's global
# state is not thread-safe). Each figure/its artists are created exactly
# once per simulation (stored in st.session_state, alongside the lattice and
# history arrays) and updated in place every frame via set_data(), so
# fig.subplots_adjust() -- the fixed-margin replacement for tight_layout() --
# also only runs once. tight_layout() is never called from the per-frame
# path: it re-measures text/tick extents on every call, which is both slow
# to run many times a second and part of what made this crash under load.
#
# The lattice heatmap itself is NOT matplotlib -- see build_lattice_figure()
# below, which uses Plotly instead and (unlike the two figures above) is
# rebuilt fresh every tick rather than persisted; see that function's
# docstring for why persistence isn't the right trade-off there. An L x L
# PNG re-encode is by far the most expensive thing in this app's render path
# (it's the one panel whose data volume scales with the lattice, not with
# the number of history points), so it's the one panel most worth moving off
# the server-side-rasterize-a-PNG path entirely: Plotly ships the raw
# z-array as JSON and lets the browser (canvas/WebGL, GPU-accelerated) do
# the rendering.


def make_domain_figure():
    """Create the Lx(t)/Ly(t) growth figure/artists once."""
    fig = Figure(figsize=(5.5, 3.2))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    (line_Lx,) = ax.plot([], [], "o-", ms=3, lw=1, color="#1f4e79")
    (line_Ly,) = ax.plot([], [], "s-", ms=3, lw=1, color="#a63603")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Time t (sweeps)")
    ax.set_ylabel("Domain size")
    ax.legend([line_Lx, line_Ly], ["Lx(t)", "Ly(t)"], loc="upper left", fontsize=8)
    ax.grid(True, which="both", alpha=0.3, linestyle="--")
    fig.subplots_adjust(left=0.16, right=0.97, top=0.93, bottom=0.16)
    return fig, ax, line_Lx, line_Ly


def make_entropy_figure():
    """Create the S_dot(t) figure/artist once."""
    fig = Figure(figsize=(5.5, 3.2))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    (line_S,) = ax.plot([], [], "o-", ms=3, lw=1, color="#6a1b9a")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Time t (sweeps)")
    ax.set_ylabel("S_dot(t), per spin (kB units)")
    ax.grid(True, which="both", alpha=0.3, linestyle="--")
    fig.subplots_adjust(left=0.16, right=0.97, top=0.93, bottom=0.16)
    return fig, ax, line_S


def build_lattice_figure(lattice: np.ndarray) -> go.Figure:
    """Build a fresh lattice heatmap Plotly figure from the current lattice.

    Called once per st.fragment tick (see live_dashboard()) -- deliberately
    NOT persisted+mutated in place the way the two matplotlib figures are,
    since a small go.Figure is cheap to construct (no server-side
    rasterization happens until st.plotly_chart renders it) and this avoids
    mutating a stored object's nested attributes from inside a fragment's
    background-timer tick. Plotly ships the raw z-array as JSON and the
    browser (canvas/WebGL) rasterizes it client-side -- no server-side PNG
    encode at all (that was the single biggest cost in the old
    matplotlib-based render path, since it scaled with L^2 rather than with
    the number of history points). No axis ticks, labels, or colorbar --
    nothing decorative is computed here.
    """
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

    # Build each figure and its artists exactly once per simulation (not per
    # frame, not per script rerun) and keep them in session_state; every
    # frame thereafter only mutates these same objects' data in place --
    # never constructs a new Figure -- which is what lets Streamlit's
    # frontend patch each chart's existing DOM node instead of tearing it
    # down and recreating it (the latter is what produces a visible
    # fade/flicker on rerun).
    (
        st.session_state.fig_domain,
        st.session_state.ax_domain,
        st.session_state.line_Lx,
        st.session_state.line_Ly,
    ) = make_domain_figure()
    (
        st.session_state.fig_entropy,
        st.session_state.ax_entropy,
        st.session_state.line_S,
    ) = make_entropy_figure()
    # The lattice heatmap (Plotly) is deliberately NOT persisted in
    # session_state the way the two figures above are -- see build_lattice_figure()
    # and its call site in live_dashboard() below for why.

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
    # st.metric() and st.pyplot() have no `key` parameter in this Streamlit
    # version (verified -- passing one raises TypeError; st.pyplot's **kwargs
    # forwards straight to matplotlib's savefig(), not to any Streamlit
    # identity mechanism). Only st.plotly_chart() below genuinely supports
    # one. These four calls instead rely on stable script-position inference,
    # which is already correct here since the same 4 calls happen in the
    # same order every tick -- Streamlit can match them to their previous
    # render without ambiguity.
    metric_cols[0].metric("Sweep Count", f"{st.session_state.sweep_count:,}")
    metric_cols[1].metric("Energy E", f"{E:,.0f}")
    metric_cols[2].metric("Concentration", f"{concentration:.4f}")
    metric_cols[3].metric("Jx/Jy", f"{Jx / Jy:.2f}")

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Live Lattice (Kawasaki Phase Separation)")
        # Deliberately rebuilt fresh every tick rather than persisted +
        # mutated in place: unlike the matplotlib plots below (where
        # rebuilding means redoing real layout/text-measurement work),
        # constructing a small go.Figure is cheap -- no server-side
        # rasterization happens until st.plotly_chart renders it -- so
        # there's no performance case for persisting it. Rebuilding also
        # sidesteps mutating a stored object's nested attributes from
        # inside an st.fragment(run_every=...) tick, which runs on
        # Streamlit's own background timer rather than a normal script
        # rerun; the stable key= below is what actually keeps the
        # frontend chart component from flickering, independent of
        # whether the Python-side Figure object is new or reused.
        st.plotly_chart(
            build_lattice_figure(lattice),
            width="stretch",
            config={"displayModeBar": False, "staticPlot": True},
            key="lattice_chart",
        )

    with right_col:
        st.subheader("Directional Domain Growth")
        if t_hist:
            st.session_state.line_Lx.set_data(t_hist, st.session_state.Lx_history)
            st.session_state.line_Ly.set_data(t_hist, st.session_state.Ly_history)
        ax_domain = st.session_state.ax_domain
        ax_domain.set_xlim(*xlim)
        ax_domain.set_ylim(0.3, L / 2.0)
        st.pyplot(
            st.session_state.fig_domain, width="stretch", clear_figure=False,
        )

        st.subheader("Entropy Production Rate")
        if t_hist:
            Sdot_smoothed = moving_average(st.session_state.Sdot_history, _ENTROPY_SMOOTHING_WINDOW)
            st.session_state.line_S.set_data(t_hist, Sdot_smoothed)
        ax_entropy = st.session_state.ax_entropy
        ax_entropy.set_xlim(*xlim)
        ax_entropy.set_ylim(_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX)
        st.pyplot(
            st.session_state.fig_entropy, width="stretch", clear_figure=False,
        )

    st.caption("Status: **running**" if st.session_state.running else "Status: **paused**")


live_dashboard()
