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
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # server-side rendering only; this is a web app, not a GUI window
import numpy as np
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

# Frames advanced per script execution while running, before yielding back to
# Streamlit with a single st.rerun(). Batching frames here (rather than one
# rerun per frame) is what actually eliminates the UI flash: it avoids
# rebuilding the whole page layout on every frame. Keep this modest so
# Pause/Reset/slider changes still feel responsive (at 0.05s/frame, a chunk
# of 10 takes ~0.5s to yield back).
FRAMES_PER_CHUNK = 10

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
# Persistent figure factories
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


def make_lattice_figure(L: int):
    """Create the lattice heatmap figure/artist once; L fixes the image shape."""
    fig = Figure(figsize=(5.2, 5.2))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    im = ax.imshow(
        np.zeros((L, L)), cmap=_LATTICE_CMAP, vmin=-1, vmax=1, interpolation="nearest",
    )
    ax.set_xticks([])
    ax.set_yticks([])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig, im


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
    "MC Sweeps per Frame Update", min_value=1, max_value=200, value=50, step=1,
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
    # frame thereafter only calls set_data()/set_xlim() on these same objects.
    st.session_state.fig_lattice, st.session_state.im_lattice = make_lattice_figure(L)
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

_metric_cols = st.columns(4)
# Plain columns don't support in-place replacement: calling col.metric() again
# just appends another metric widget below the last one. Wrapping each column
# in its own st.empty() gives each metric a placeholder that DOES replace its
# content on every call, instead of stacking a new row every frame.
metric_ph_sweep = _metric_cols[0].empty()
metric_ph_energy = _metric_cols[1].empty()
metric_ph_conc = _metric_cols[2].empty()
metric_ph_aniso = _metric_cols[3].empty()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Live Lattice (Kawasaki Phase Separation)")
    lattice_placeholder = st.empty()

with right_col:
    st.subheader("Directional Domain Growth $L_x(t)$, $L_y(t)$")
    domain_placeholder = st.empty()
    st.subheader(r"Entropy Production Rate $\dot{S}(t)$")
    entropy_placeholder = st.empty()

status_placeholder = st.empty()


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


def render() -> None:
    """Update the persistent figures/artists and metrics from current state, and push them
    to their placeholders. Creates no new Figure objects and calls no layout-solving
    functions (tight_layout) -- everything here is a cheap in-place artist update."""
    lattice = st.session_state.lattice
    t_hist = st.session_state.t_history
    xlim = (1.0, max(10.0, st.session_state.sweep_count * 1.5))

    # --- lattice heatmap ---
    st.session_state.im_lattice.set_data(lattice)
    lattice_placeholder.pyplot(st.session_state.fig_lattice, width="stretch", clear_figure=False)

    # --- domain growth plot ---
    if t_hist:
        st.session_state.line_Lx.set_data(t_hist, st.session_state.Lx_history)
        st.session_state.line_Ly.set_data(t_hist, st.session_state.Ly_history)
    ax_domain = st.session_state.ax_domain
    ax_domain.set_xlim(*xlim)
    ax_domain.set_ylim(0.3, L / 2.0)
    domain_placeholder.pyplot(st.session_state.fig_domain, width="stretch", clear_figure=False)

    # --- entropy production plot (smoothed) ---
    if t_hist:
        Sdot_smoothed = moving_average(st.session_state.Sdot_history, _ENTROPY_SMOOTHING_WINDOW)
        st.session_state.line_S.set_data(t_hist, Sdot_smoothed)
    ax_entropy = st.session_state.ax_entropy
    ax_entropy.set_xlim(*xlim)
    ax_entropy.set_ylim(_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX)
    entropy_placeholder.pyplot(st.session_state.fig_entropy, width="stretch", clear_figure=False)

    # --- metrics row (dedicated placeholders -- replace in place, never stack) ---
    N = L * L
    n_up = int(np.count_nonzero(lattice == 1))
    concentration = n_up / N
    E = total_energy(lattice, Jx, Jy)
    metric_ph_sweep.metric("Sweep Count", f"{st.session_state.sweep_count:,}")
    metric_ph_energy.metric("Energy E", f"{E:,.0f}")
    metric_ph_conc.metric("Concentration", f"{concentration:.4f}")
    metric_ph_aniso.metric("Jx/Jy", f"{Jx / Jy:.2f}")

    status_placeholder.caption(
        "Status: **running**" if st.session_state.running else "Status: **paused**"
    )


if st.session_state.running:
    # Advance several frames inside this single script execution, reusing the
    # same st.empty() placeholders declared above, instead of doing one frame
    # per full script rerun. Re-running the whole script every frame was the
    # actual cause of the UI flashing: each rerun re-executes everything above
    # (title, sidebar, columns, placeholder creation), so the browser briefly
    # tears down and rebuilds the entire layout every ~50ms. Looping here lets
    # each frame just update the *contents* of already-existing placeholders.
    # We still yield back to Streamlit every FRAMES_PER_CHUNK frames (via
    # st.rerun() below) so Pause/Reset/slider changes stay responsive.
    for _ in range(FRAMES_PER_CHUNK):
        advance_one_frame()
        render()
        time.sleep(0.05)
else:
    render()

if st.session_state.running:
    st.rerun()
