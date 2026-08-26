"""
solara_app.py
=============

Solara web dashboard for Model B (Kawasaki spin-exchange dynamics):
interactive controls for the anisotropy ratio, quench temperature, lattice
size, and sweeps-per-frame, with a live-updating lattice heatmap and
directional domain-growth / entropy-production plots.

Self-contained within `model_b/`: imports only the Numba-jitted kernels and
FFT-based correlation/domain-size helpers from `kawasaki_engine.py`
(unmodified) and does not touch anything in the repository root or
`manuscript/`.

Usage (Solara apps are launched via the `solara` CLI, not `python`):
    solara run model_b/solara_app.py
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
_DOMAIN_Y_MIN = 0.5  # upper bound is L/2 (r_max), computed per-call since it depends on lattice size
_ENTROPY_FLOOR = 1e-7
_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX = 1e-7, 1.0  # matches _ENTROPY_FLOOR, so the floored tail sits on-axis, not clipped below it
_ENTROPY_SMOOTHING_WINDOW = 10
_SEED = 2026
_ISING_TC = 2.269  # 2D Ising critical temperature (Onsager), for the T/Tc reduced-temperature readout

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


def _display_domain_size(raw: float) -> float:
    """Floor/guard a raw domain_size_from_correlation() value for display.

    kawasaki_engine's domain_size_from_correlation() finds where the raw
    spin autocorrelation C(r) crosses 0.5 -- correctly, and by design,
    returns NaN when it never does. At a concentration far from 0.5, the
    conserved magnetization m = 2*concentration - 1 has m^2 > 0.5 once
    concentration <~0.15 or >~0.85, so C(r) plateaus at m^2 (its r -> inf
    limit) without ever decaying below 0.5 -- meaning every tick's Lx/Ly at
    those concentrations is legitimately NaN, not an occasional edge case.
    A log-scale Plotly trace silently drops NaN/<=0 points, so an
    all-NaN series renders as a fully hidden line rather than a visible
    (if degenerate) one.

    Clamping only here, for the live dashboard's display, rather than
    inside kawasaki_engine.py itself: that module is the shared, verified
    physics core also used by plot_kawasaki_kinetics.py's replica-averaging
    (which uses np.nanmean/np.nanstd and depends on real NaNs to exclude
    unresolved replicas from the statistics) -- silently turning its NaNs
    into a fabricated 1.0 there would quietly corrupt that averaging.
    """
    return float(np.maximum(1.0, np.nan_to_num(raw, nan=1.0, posinf=1.0)))


def total_energy(lattice: np.ndarray, Jx: float, Jy: float) -> float:
    """Full-lattice anisotropic Hamiltonian, O(L^2) via vectorized NumPy rolls."""
    right = np.roll(lattice, -1, axis=1)
    down = np.roll(lattice, -1, axis=0)
    return float(-Jx * np.sum(lattice * right) - Jy * np.sum(lattice * down))


def interfacial_density(lattice: np.ndarray) -> float:
    """Fraction of nearest-neighbor spin pairs (periodic, horizontal +
    vertical) that are antiparallel -- the density of domain-wall bonds.
    1.0 for a perfect checkerboard, 0.0 for a single uniform domain."""
    right = np.roll(lattice, -1, axis=1)
    down = np.roll(lattice, -1, axis=0)
    antiparallel = np.count_nonzero(lattice * right == -1) + np.count_nonzero(lattice * down == -1)
    return antiparallel / (2 * lattice.size)


_ALPHA_FIT_WINDOW = 20  # recent-history points used for the log-log slope fit
_ALPHA_MIN_SWEEP_T = 500  # only fit t > this -- early time is dominated by pre-scaling transients
_ALPHA_MAX_PHYSICAL = 0.5  # clamp ceiling -- LS scaling predicts ~1/3; anything above this is fit noise


def effective_growth_exponent(t_hist: list[float], Lx_hist: list[float], Ly_hist: list[float]) -> float:
    """Local coarsening exponent alpha = d(log L)/d(log t), least-squares
    fit over the most recent _ALPHA_FIT_WINDOW points with t > _ALPHA_MIN_SWEEP_T,
    for the combined (Lx+Ly)/2 effective domain size vs. time -- Lifshitz-
    Slyozov predicts alpha ~ 1/3 for isotropic Model B coarsening.

    Restricted to late-stage (t > _ALPHA_MIN_SWEEP_T) data: early on, a
    handful of noisy single-batch domain-size estimates dominate the fit
    and can swing the slope to nonphysical values (negative, or far above
    the LS prediction) well before power-law growth is actually
    established. The result is clamped to [0.0, _ALPHA_MAX_PHYSICAL] --
    a negative or unphysically large fitted slope means the fit caught
    noise, not real growth, so 0.0 is reported rather than a misleading
    number. Also returns 0.0 before enough late-stage history exists to
    fit a slope through, or if the fit is degenerate (e.g. all t equal).
    """
    t_arr = np.asarray(t_hist)
    late = t_arr > _ALPHA_MIN_SWEEP_T
    if np.count_nonzero(late) < 2:
        return 0.0

    t = t_arr[late][-_ALPHA_FIT_WINDOW:]
    L = ((np.asarray(Lx_hist)[late] + np.asarray(Ly_hist)[late]) / 2.0)[-_ALPHA_FIT_WINDOW:]

    valid = (t > 0) & (L > 0)
    if np.count_nonzero(valid) < 2:
        return 0.0
    log_t = np.log(t[valid])
    log_L = np.log(L[valid])
    if np.ptp(log_t) == 0.0:
        return 0.0

    slope, _intercept = np.polyfit(log_t, log_L, 1)
    if not np.isfinite(slope):
        return 0.0
    return float(np.clip(slope, 0.0, _ALPHA_MAX_PHYSICAL))


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


def _dynamic_x_max(current_sweep: float) -> float:
    """Continuous x-axis upper bound, floored at 100, with a constant 25%
    headroom multiplier ahead of the trajectory. Recomputed every tick
    (unlike a discrete decade-rounded bound) so the axis expands smoothly
    frame-by-frame instead of snapping to the next power of ten and
    visually compressing the already-drawn line."""
    return max(100.0, current_sweep * 1.25)


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
            # Lx drawn first (lower z-order) as a solid line; Ly drawn
            # second (on top) dashed and slightly translucent. When thermal
            # noise or an extreme concentration collapses both onto the
            # same numerical value -- e.g. both floored to 1.0 by
            # _display_domain_size -- a plain solid-over-solid overlap
            # would fully hide Lx under Ly. The dash pattern lets Lx's
            # solid color show through in the gaps, so both series stay
            # visibly distinguishable even when perfectly coincident.
            go.Scatter(
                # Plotly's own text markup (not real HTML/DOM) -- <sub>/<sup>
                # are supported in trace names, titles, and annotations, so
                # the legend renders a true subscript "x" instead of the
                # bare "Lx(t)" a plain string would show.
                x=x, y=Lx_hist if has_data else [],
                mode="lines+markers", name="L<sub>x</sub>(t)", uid="domain-lx",
                marker=dict(symbol="circle", size=5), line=dict(color=_DOMAIN_LX_COLOR, width=1.8),
            ),
            go.Scatter(
                x=x, y=Ly_hist if has_data else [],
                mode="lines+markers", name="L<sub>y</sub>(t)", uid="domain-ly", opacity=0.85,
                marker=dict(symbol="square", size=5),
                line=dict(color=_DOMAIN_LY_COLOR, width=1.8, dash="dash"),
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
        showgrid=True, gridcolor="#eeeeee", automargin=True,
    )
    fig.update_yaxes(
        type="log", range=_log_range(_DOMAIN_Y_MIN, L / 2.0), title_text="Domain size",
        showgrid=True, gridcolor="#eeeeee", automargin=True,
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
                # "Ṡ" (LATIN CAPITAL LETTER S WITH DOT ABOVE, U+1E60) reads
                # cleanly as plain Unicode text (no markup needed); "k<sub>B</sub>"
                # relies on Plotly's own text markup, same as the domain
                # chart's L<sub>x</sub>/L<sub>y</sub> subscripts.
                x=t_hist if has_data else [], y=Sdot_smoothed if has_data else [],
                mode="lines+markers", name="Ṡ(t)", uid="entropy-sdot",
                marker=dict(symbol="circle", size=5), line=dict(color=_ENTROPY_COLOR, width=1.5),
            ),
        ]
    )
    fig.update_xaxes(
        type="log", range=_log_range(*x_range), title_text="Time t (sweeps)",
        showgrid=True, gridcolor="#eeeeee", automargin=True,
    )
    fig.update_yaxes(
        type="log", range=_log_range(_ENTROPY_AXIS_MIN, _ENTROPY_AXIS_MAX),
        title_text="Ṡ(t) [k<sub>B</sub> / sweep]", showgrid=True, gridcolor="#eeeeee",
        # automargin: Plotly expands the figure's own margin as needed to
        # fit the axis title and SI-prefixed tick labels (100μ, 1μ, ...)
        # rather than clipping them against a fixed-width margin -- the
        # tick text width varies with the exponent shown, so a single fixed
        # margin value can't be picked to always fit it.
        automargin=True,
    )
    fig.update_layout(
        autosize=True,
        # Wider left margin than the shared _CHART_MARGIN (this chart's
        # y-axis title plus SI-prefixed tick labels need more room than the
        # domain-growth chart's shorter "Domain size"), and automargin
        # above still expands past this if a given label needs even more.
        margin=dict(l=85, r=20, t=30, b=40),
        height=_CHART_HEIGHT, showlegend=False,
    )
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
    alpha: float
    interfacial_density: float


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
        # _dynamic_x_max) -- recomputed every tick so it expands smoothly
        # frame-by-frame rather than snapping between discrete steps.
        self.x_max = _dynamic_x_max(0)

        self.lattice_widget: Optional[PlotlyFigureWidget] = None
        self.domain_widget: Optional[PlotlyFigureWidget] = None
        self.entropy_widget: Optional[PlotlyFigureWidget] = None

        initial_energy = total_energy(self.lattice, Jx, Jy)
        initial_concentration = int(np.count_nonzero(self.lattice == 1)) / (L * L)
        initial_interfacial = interfacial_density(self.lattice)
        self.metrics: solara.Reactive[SimMetrics] = solara.reactive(
            SimMetrics(0, initial_energy, initial_concentration, 0.0, initial_interfacial)
        )


def _metric(label: str, value: str, upper: bool = True, markdown: bool = False) -> None:
    """A small Streamlit-st.metric-like label-over-value display.

    `upper=False` opts a label out of Python's str.upper(): Unicode case
    folding maps lowercase Greek "α" to uppercase "Α" (U+0391), which is
    visually indistinguishable from Latin "A" in most fonts -- turning
    "Growth Exponent α" into what reads as "GROWTH EXPONENT A". Callers
    with a lowercase symbol in the label should pre-format it in the caps
    style themselves and pass upper=False.

    `markdown=True` renders `label` through solara.Markdown instead of
    solara.Text, so inline LaTeX like "$J_x / J_y$" is typeset via KaTeX
    (confirmed working: solara.Markdown runs $...$ through a real math
    renderer, unlike solara.Text, which escapes raw HTML tags rather than
    rendering them). Always skips the uppercase transform in this mode
    regardless of `upper` -- case-folding LaTeX source is unsafe in
    general (e.g. "\\alpha" -> "\\ALPHA" is not a valid command and
    silently breaks the render), so callers should pre-capitalize any
    plain-text portion of the label themselves.
    """
    with solara.Column(gap="0px", style={"text-align": "center", "min-width": "110px"}):
        label_style = {"font-size": "0.7rem", "color": "#666", "letter-spacing": "0.03em", "margin": "0"}
        if markdown:
            solara.Markdown(label, style=label_style)
        else:
            solara.Text(label.upper() if upper else label, style=label_style)
        solara.Text(value, style={"font-size": "1.3rem", "font-weight": "600"})


def _card_header(text: str) -> None:
    """A card's section heading, rendered as a plain wrapping Text instead
    of solara.Card's own `title=` prop: Vuetify's `.v-card-title` class
    hard-codes `white-space: nowrap; overflow: hidden; text-overflow:
    ellipsis`, which silently truncated "Physics Parameters" to "Physics
    Paramet..." once the card narrowed below its rendered text width."""
    solara.Text(
        text,
        style={
            "font-weight": "700", "font-size": "1rem", "white-space": "normal",
            "display": "block", "margin-bottom": "10px",
        },
    )


def _slider_label(text: str, markdown: bool = False) -> None:
    """A slider's live-value label, stacked in its own full-width line
    above the track instead of passed as the slider's own `label` prop:
    Vuetify renders that inline to the *left* of the track (sharing width
    with it), under the same `.v-slider__label` nowrap/ellipsis styling as
    the card title above -- fine while it happens to fit, silently clipped
    once the label text or a narrower sidebar pushes past that shared
    width. A full-width line has no such competing element to clip against.

    `markdown=True` renders via solara.Markdown for inline LaTeX (e.g.
    "Anisotropy ($J_x/J_y$): 2.00") -- see _metric's docstring for the
    same mechanism and its uppercase-transform caveat (not applicable
    here since this function never uppercases its text either way).
    """
    style = {"font-size": "0.85rem", "font-weight": "600", "margin": "0", "margin-bottom": "-6px"}
    if markdown:
        solara.Markdown(text, style=style)
    else:
        solara.Text(text, style=style)


_MATERIALS_SCIENCE_MARKDOWN = """
- **Spinodal Phase Separation**: Models how a two-component mixture un-mixes over time while total concentration stays constant. I'm measuring domain size growth over time L(t) to verify whether it matches theoretical Lifshitz-Slyozov scaling L(t) ~ t^(1/3).
- **Directional Precipitate Rafting**: Setting unequal horizontal and vertical couplings (J_x != J_y) forces domains to align into parallel bands, mimicking directional gamma-prime precipitate rafting in nickel superalloys under stress.
- **Trajectory Entropy Production Rate**: Tracks the real-time heat dissipation rate during spin swaps across Monte Carlo sweeps. As the lattice relaxes toward equilibrium, entropy production drops off, quantifying thermodynamic irreversibility.
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
        _metric("$J_x / J_y$", f"{Jx / Jy:.2f}", markdown=True)
        _metric("Growth Exponent $\\alpha$", f"{metrics.alpha:.3f}", markdown=True)
        _metric("Interfacial Density", f"{metrics.interfacial_density:.4f}")

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
            Lx = _display_domain_size(domain_size_from_correlation(Cx))
            Ly = _display_domain_size(domain_size_from_correlation(Cy))

            dE_per_sweep_per_spin = (total_dE / n_sweeps) / (state.L * state.L)
            Sdot = max(-dE_per_sweep_per_spin / T_final.value, _ENTROPY_FLOOR)

            state.t_history.append(t)
            state.Lx_history.append(Lx)
            state.Ly_history.append(Ly)
            state.Sdot_history.append(Sdot)

            # Recomputed every tick: a continuous 25%-headroom bound keeps
            # the axis expanding smoothly frame-by-frame rather than
            # snapping between discrete decades and visually compressing
            # the already-drawn line.
            state.x_max = _dynamic_x_max(t)
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
                alpha = effective_growth_exponent(state.t_history, state.Lx_history, state.Ly_history)
                interfacial = interfacial_density(state.lattice)
                state.metrics.value = SimMetrics(state.sweep_count, E, concentration, alpha, interfacial)

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
        with solara.Column(style="width: 300px; flex-shrink: 0; padding: 16px;"):
            solara.Markdown("## Model B Controls")
            solara.Text(
                "Kawasaki spin-exchange dynamics (conserved order parameter)",
                style={"color": "#666", "font-size": "0.85rem"},
            )

            with solara.Card(style={"margin": "12px 0", "padding": "10px 8px"}):
                _card_header("Physics Parameters")
                with solara.Column(gap="16px", style={"padding": "4px 2px"}):
                    _slider_label(f"Anisotropy ($J_x/J_y$): {anisotropy_ratio.value:.2f}", markdown=True)
                    solara.SliderFloat("", value=anisotropy_ratio, min=0.1, max=10.0, step=0.1)
                    solara.Markdown(
                        "$J_x$ is held fixed at 1.0; this slider sets $J_y$ = $J_x$ / ratio.",
                        style={"color": "#888", "font-size": "0.75rem", "margin": "0", "margin-top": "-10px"},
                    )
                    _slider_label(f"Quench Temperature: {T_final.value:.2f}")
                    solara.SliderFloat("", value=T_final, min=0.1, max=2.5, step=0.1)
                    solara.Markdown(
                        f"$T / T_c$ = {T_final.value / _ISING_TC:.3f}  ($T_c$ = {_ISING_TC}, "
                        "the 2D Ising critical temperature)",
                        style={"color": "#888", "font-size": "0.75rem", "margin": "0", "margin-top": "-10px"},
                    )
                    _slider_label(f"Concentration: {concentration.value:.2f}")
                    solara.SliderFloat("", value=concentration, min=0.10, max=0.90, step=0.05)

            with solara.Card(style={"margin": "12px 0", "padding": "10px 8px"}):
                _card_header("Simulation Engine")
                with solara.Column(gap="16px", style={"padding": "4px 2px"}):
                    solara.Select("Lattice Size L", value=L_value, values=[32, 64, 128])
                    _slider_label(f"Sweeps per Frame: {sweeps_per_frame.value}")
                    solara.SliderInt("", value=sweeps_per_frame, min=1, max=200, step=1)

                    with solara.Row(gap="8px", style={"flex-wrap": "wrap"}):
                        solara.Button("Start", on_click=lambda: state.running.set(True), color="primary")
                        solara.Button("Pause", on_click=lambda: state.running.set(False))
                        solara.Button("Reset", on_click=lambda: set_reset_counter(reset_counter + 1))

                    solara.Markdown(
                        f"$J_x$={Jx:.2f}, $J_y$={Jy:.3f}  (ratio={anisotropy_ratio.value:.2f})",
                        style={"color": "#666", "font-size": "0.8rem", "margin": "0"},
                    )

            with solara.Details(summary="Materials Science & Engineering Context"):
                solara.Markdown(_MATERIALS_SCIENCE_MARKDOWN)

        with solara.Column(style="flex-grow: 1; min-width: 0; padding: 16px;"):
            solara.Markdown(
                "# Anisotropic Model B Kinetics & Non-Equilibrium Thermodynamics",
                style={"white-space": "normal", "overflow-wrap": "break-word"},
            )
            solara.Text(
                "Conserved order-parameter phase separation with independent horizontal "
                "and vertical spin exchange.",
                style={"color": "#666"},
            )

            LiveDashboard(state, Jx, Jy)
