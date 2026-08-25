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
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.colors import ListedColormap

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

metrics_row = st.columns(4)
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
    """Draw the lattice heatmap, both line plots, and the metrics row from current state."""
    lattice = st.session_state.lattice
    t_hist = st.session_state.t_history

    # --- lattice heatmap ---
    fig_lattice, ax_lattice = plt.subplots(figsize=(5.2, 5.2))
    ax_lattice.imshow(lattice, cmap=_LATTICE_CMAP, vmin=-1, vmax=1, interpolation="nearest")
    ax_lattice.set_xticks([])
    ax_lattice.set_yticks([])
    fig_lattice.tight_layout()
    lattice_placeholder.pyplot(fig_lattice, width="stretch")
    plt.close(fig_lattice)

    # --- domain growth plot ---
    fig_domain, ax_domain = plt.subplots(figsize=(5.5, 3.2))
    if t_hist:
        ax_domain.plot(
            t_hist, st.session_state.Lx_history, "o-", ms=3, lw=1,
            color="#1f4e79", label=rf"$L_x(t)$ ($J_x={Jx:.2f}$)",
        )
        ax_domain.plot(
            t_hist, st.session_state.Ly_history, "s-", ms=3, lw=1,
            color="#a63603", label=rf"$L_y(t)$ ($J_y={Jy:.2f}$)",
        )
        ax_domain.legend(loc="upper left", fontsize=8)
    ax_domain.set_xscale("log")
    ax_domain.set_yscale("log")
    ax_domain.set_xlim(1.0, max(10.0, st.session_state.sweep_count * 1.5))
    ax_domain.set_ylim(0.3, L / 2.0)
    ax_domain.set_xlabel("Time $t$ (sweeps)")
    ax_domain.set_ylabel("Domain size")
    ax_domain.grid(True, which="both", alpha=0.3, linestyle="--")
    fig_domain.tight_layout()
    domain_placeholder.pyplot(fig_domain, width="stretch")
    plt.close(fig_domain)

    # --- entropy production plot (smoothed) ---
    fig_entropy, ax_entropy = plt.subplots(figsize=(5.5, 3.2))
    if t_hist:
        Sdot_smoothed = moving_average(st.session_state.Sdot_history, _ENTROPY_SMOOTHING_WINDOW)
        ax_entropy.plot(t_hist, Sdot_smoothed, "o-", ms=3, lw=1, color="#6a1b9a")
    ax_entropy.set_xscale("log")
    ax_entropy.set_yscale("log")
    ax_entropy.set_xlim(1.0, max(10.0, st.session_state.sweep_count * 1.5))
    ax_entropy.set_ylim(_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX)
    ax_entropy.set_xlabel("Time $t$ (sweeps)")
    ax_entropy.set_ylabel(r"$\dot{S}(t)$ (per spin, $k_B$)")
    ax_entropy.grid(True, which="both", alpha=0.3, linestyle="--")
    fig_entropy.tight_layout()
    entropy_placeholder.pyplot(fig_entropy, width="stretch")
    plt.close(fig_entropy)

    # --- metrics row ---
    N = L * L
    n_up = int(np.count_nonzero(lattice == 1))
    concentration = n_up / N
    E = total_energy(lattice, Jx, Jy)
    metrics_row[0].metric("Sweep Count", f"{st.session_state.sweep_count:,}")
    metrics_row[1].metric("Energy $E$", f"{E:,.0f}")
    metrics_row[2].metric("Concentration", f"{concentration:.4f}")
    metrics_row[3].metric("$J_x/J_y$", f"{Jx / Jy:.2f}")

    status_placeholder.caption(
        "Status: **running**" if st.session_state.running else "Status: **paused**"
    )


if st.session_state.running:
    advance_one_frame()

render()

if st.session_state.running:
    time.sleep(0.05)
    st.rerun()
