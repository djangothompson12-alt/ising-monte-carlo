"""
live_visualizer.py
===================

Real-time interactive dashboard for the Model B (Kawasaki spin-exchange)
quench: a live-updating 2D lattice heatmap alongside directional domain-size
and entropy-production traces, animated with matplotlib's FuncAnimation.

Self-contained within `model_b/`: imports only the Numba-jitted kernels and
FFT-based correlation/domain-size helpers from `kawasaki_engine.py` (unmodified)
and does not touch anything in the repository root or `manuscript/`.

Usage:
    python model_b/live_visualizer.py
    (or: cd model_b && python live_visualizer.py)

Close the window to stop the simulation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap

sys.path.insert(0, str(Path(__file__).parent))
from kawasaki_engine import (  # noqa: E402
    _axis_correlation_xy,
    _kawasaki_sweep,
    domain_size_from_correlation,
)

# --- Simulation parameters ---
L = 128
JX = 1.0
JY = 0.5
T_FINAL = 1.0
SWEEPS_PER_FRAME = 50
SEED = 2026

# --- Display parameters ---
_SPIN_DOWN_COLOR = "#1f4e79"
_SPIN_UP_COLOR = "#f2f2f2"
_LATTICE_CMAP = ListedColormap([_SPIN_DOWN_COLOR, _SPIN_UP_COLOR])

# Fixed axis ranges for the live line plots. blit=True caches a rendered
# background per axes and only redraws the changed artists on top of it;
# letting the axes autoscale as data grows would invalidate that cached
# background every frame and defeat the purpose of blitting. Fixed, generous
# ranges (domain size is bounded above by r_max = L/2; entropy production is
# bounded below near machine-precision-noise) avoid needing to rescale at all.
_T_AXIS_MIN, _T_AXIS_MAX = 1.0, 2.0e5
_DOMAIN_AXIS_MIN, _DOMAIN_AXIS_MAX = 0.3, L / 2.0
_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX = 1e-5, 1.0
_ENTROPY_FLOOR = 1e-7  # internal floor so S_dot=0 samples don't hit log(0); below the visible axis range

# Simple moving-average window (in frames) applied to S_dot(t) before plotting.
# Late-time entropy production is a tiny per-sweep energy-change average over
# only SWEEPS_PER_FRAME sweeps, so it's dominated by shot noise once the true
# rate drops near the floor; smoothing turns that noise into a readable
# asymptotic baseline without touching the underlying (still exact) data.
ENTROPY_SMOOTHING_WINDOW = 10


def init_balanced_lattice(L: int, seed: int) -> np.ndarray:
    """Build an L x L lattice with an exact 50/50 +-1 split.

    Kawasaki dynamics conserves total magnetization exactly, so starting
    from an exact balance (rather than merely an expected-value balance)
    keeps the run at the symmetric ("critical concentration") quench point
    for its entire duration -- and gives a clean live sanity check in the HUD.
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


def moving_average(values: list[float] | np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average, with a growing (partial) window at the start.

    Unlike `np.convolve(..., mode="same")`, this never averages in zero-padding
    at the edges, so the first few points aren't artificially pulled down.

    Args:
        values: 1D sequence to smooth.
        window: Maximum number of trailing points to average over.

    Returns:
        An array the same length as `values`.
    """
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


def total_energy(lattice: np.ndarray, Jx: float, Jy: float) -> float:
    """Full-lattice anisotropic Hamiltonian, H = -Jx*sum_x(s_i s_j) - Jy*sum_y(s_i s_j).

    O(L^2) via vectorized NumPy rolls; cheap enough to call once per frame
    purely for the HUD display (the hot Monte Carlo loop never calls this).
    """
    right = np.roll(lattice, -1, axis=1)
    down = np.roll(lattice, -1, axis=0)
    return float(-Jx * np.sum(lattice * right) - Jy * np.sum(lattice * down))


class LiveKawasakiState:
    """Holds the evolving lattice and accumulated time-series history."""

    def __init__(self, L: int, Jx: float, Jy: float, T_final: float, seed: int) -> None:
        self.L = L
        self.Jx = Jx
        self.Jy = Jy
        self.T_final = T_final
        self.beta = 1.0 / T_final
        self.N = L * L
        self.r_max = L // 2

        self.lattice = init_balanced_lattice(L, seed)
        self.sweep_count = 0
        self.t_history: list[float] = []
        self.Lx_history: list[float] = []
        self.Ly_history: list[float] = []
        self.Sdot_history: list[float] = []

    def step(self, n_sweeps: int) -> None:
        """Advance the lattice by n_sweeps Kawasaki sweeps and record observables."""
        total_dE = 0.0
        for _ in range(n_sweeps):
            total_dE += _kawasaki_sweep(self.lattice, self.beta, self.Jx, self.Jy)
        self.sweep_count += n_sweeps

        Cx, Cy = _axis_correlation_xy(self.lattice, self.r_max)
        Lx = domain_size_from_correlation(Cx)
        Ly = domain_size_from_correlation(Cy)

        dE_per_sweep_per_spin = (total_dE / n_sweeps) / self.N
        Sdot = -dE_per_sweep_per_spin / self.T_final

        self.t_history.append(float(self.sweep_count))
        self.Lx_history.append(Lx)
        self.Ly_history.append(Ly)
        self.Sdot_history.append(max(Sdot, _ENTROPY_FLOOR))

    def concentration(self) -> float:
        """Fraction of up-spins (n_up / N); exactly 0.5 for all time by conservation."""
        return float(np.count_nonzero(self.lattice == 1)) / self.N


def build_dashboard(state: LiveKawasakiState):
    """Construct the figure, axes, and animated artists for the live dashboard.

    Returns:
        (fig, artists, update_fn) where update_fn(frame) advances the
        simulation and returns the tuple of updated artists (for blitting).
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    ax_lattice = axes[0]
    axes[1].remove()  # replaced below with two stacked line-plot axes

    gs_right = fig.add_gridspec(2, 1, left=0.56, right=0.97, top=0.90, bottom=0.09, hspace=0.35)
    ax_domain = fig.add_subplot(gs_right[0])
    ax_entropy = fig.add_subplot(gs_right[1])

    fig.suptitle(
        rf"Model B Live Dashboard: Kawasaki Exchange Dynamics ($T_f={state.T_final}$)",
        fontsize=13,
    )

    # --- Left panel: lattice heatmap ---
    im = ax_lattice.imshow(
        state.lattice, cmap=_LATTICE_CMAP, vmin=-1, vmax=1,
        interpolation="nearest", animated=True,
    )
    ax_lattice.set_xticks([])
    ax_lattice.set_yticks([])
    ax_lattice.set_title(r"Spin Lattice (dark $=-1$, light $=+1$)")

    hud_text = ax_lattice.text(
        0.02, 0.98, "", transform=ax_lattice.transAxes, va="top", ha="left",
        fontsize=9, family="monospace", color="white", animated=True,
        bbox=dict(boxstyle="round", facecolor="black", alpha=0.55, edgecolor="none"),
    )

    # --- Right-top panel: directional domain sizes ---
    (line_Lx,) = ax_domain.plot(
        [], [], "o-", ms=3, lw=1, color="#1f4e79", label=rf"$L_x(t)$ ($J_x={state.Jx}$)",
        animated=True,
    )
    (line_Ly,) = ax_domain.plot(
        [], [], "s-", ms=3, lw=1, color="#a63603", label=rf"$L_y(t)$ ($J_y={state.Jy}$)",
        animated=True,
    )
    ax_domain.set_xscale("log")
    ax_domain.set_yscale("log")
    ax_domain.set_xlim(_T_AXIS_MIN, _T_AXIS_MAX)
    ax_domain.set_ylim(_DOMAIN_AXIS_MIN, _DOMAIN_AXIS_MAX)
    ax_domain.set_xlabel("Time $t$ (sweeps)")
    ax_domain.set_ylabel("Domain size (lattice units)")
    ax_domain.set_title("Directional Domain Growth")
    ax_domain.legend(loc="upper left", fontsize=8)
    ax_domain.grid(True, which="both", alpha=0.3, linestyle="--")

    # --- Right-bottom panel: entropy production rate ---
    (line_S,) = ax_entropy.plot([], [], "o-", ms=3, lw=1, color="#6a1b9a", animated=True)
    ax_entropy.set_xscale("log")
    ax_entropy.set_yscale("log")
    ax_entropy.set_xlim(_T_AXIS_MIN, _T_AXIS_MAX)
    ax_entropy.set_ylim(_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX)
    ax_entropy.set_xlabel("Time $t$ (sweeps)")
    ax_entropy.set_ylabel(r"$\dot{S}(t)$ (per spin, $k_B$)")
    ax_entropy.set_title("Irreversible Entropy Production")
    ax_entropy.grid(True, which="both", alpha=0.3, linestyle="--")

    artists = (im, line_Lx, line_Ly, line_S, hud_text)

    def update(_frame: int):
        state.step(SWEEPS_PER_FRAME)

        im.set_data(state.lattice)
        line_Lx.set_data(state.t_history, state.Lx_history)
        line_Ly.set_data(state.t_history, state.Ly_history)
        Sdot_smoothed = moving_average(state.Sdot_history, ENTROPY_SMOOTHING_WINDOW)
        line_S.set_data(state.t_history, Sdot_smoothed)

        E = total_energy(state.lattice, state.Jx, state.Jy)
        hud_text.set_text(
            f"Sweep count:   {state.sweep_count:>8d}\n"
            f"Energy E:      {E:>+10.1f}\n"
            f"Concentration: {state.concentration():.4f}\n"
            f"Jx/Jy ratio:   {state.Jx / state.Jy:.3f}  (Jx={state.Jx}, Jy={state.Jy})"
        )

        return artists

    return fig, artists, update


def main() -> None:
    """Launch the live Model B dashboard; blocks until the window is closed."""
    print(
        f"Model B live dashboard: L={L}, Jx={JX}, Jy={JY}, T_final={T_FINAL}, "
        f"{SWEEPS_PER_FRAME} sweeps/frame. Close the window to stop."
    )
    state = LiveKawasakiState(L, JX, JY, T_FINAL, SEED)
    fig, _artists, update = build_dashboard(state)

    ani = FuncAnimation(
        fig, update, interval=20, blit=True, cache_frame_data=False,
    )
    fig._live_animation_ref = ani  # keep a strong reference so it isn't garbage-collected
    plt.show()


if __name__ == "__main__":
    main()
