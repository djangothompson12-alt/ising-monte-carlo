"""
kawasaki_engine.py
===================

Numba-accelerated Kawasaki spin-exchange Monte Carlo engine for the 2D
anisotropic Ising model with periodic boundary conditions. Standalone
counterpart to the root project's Metropolis (Model A) engine.

Statistical mechanics background
---------------------------------
The anisotropic Ising Hamiltonian on a square lattice with independent
horizontal and vertical nearest-neighbor couplings :math:`J_x, J_y` is

.. math::
    H = -J_x \\sum_{\\langle i,j \\rangle_x} \\sigma_i \\sigma_j
        -J_y \\sum_{\\langle i,j \\rangle_y} \\sigma_i \\sigma_j

where :math:`\\langle i,j \\rangle_x` and :math:`\\langle i,j \\rangle_y` denote
horizontal and vertical nearest-neighbor bonds respectively. Onsager's exact
solution generalizes to this anisotropic case: the critical temperature
:math:`T_c(J_x, J_y)` is the (unique, numerically located) root of

.. math::
    \\sinh(2 J_x / T_c) \\, \\sinh(2 J_y / T_c) = 1

which reduces to the familiar isotropic result :math:`T_c = 2J/\\ln(1+\\sqrt{2})`
when :math:`J_x = J_y = J`.

Kawasaki (spin-exchange) dynamics
----------------------------------
Rather than flipping single spins (Model A, non-conserved order parameter),
this module implements **Kawasaki dynamics**: a randomly chosen nearest-
neighbor pair of spins is *exchanged* with Metropolis acceptance
probability :math:`\\min(1, e^{-\\beta \\Delta E})`. Because an exchange only
ever swaps a $+1$ and a $-1$, the total magnetization
:math:`\\sum_i \\sigma_i` is exactly conserved at every step. This is the
"Model A vs. Model B" distinction of Hohenberg and Halperin [Rev. Mod. Phys.
49, 435 (1977)]: non-conserved order-parameter coarsening obeys the
Lifshitz-Allen-Cahn law :math:`L(t) \\sim t^{1/2}`, while conserved-order-
parameter (Kawasaki / Model B) coarsening is diffusion-limited and obeys the
slower Lifshitz-Slyozov growth law

.. math::
    L(t) \\sim t^{1/3}.

For a nearest-neighbor pair of sites :math:`i, j` connected by a bond of
strength :math:`J_{ij}`, exchanging their spins leaves the :math:`i`-:math:`j`
bond's own energy unchanged (the product :math:`\\sigma_i \\sigma_j` is
invariant under the swap) and changes only the bonds each site has to its
*other* three neighbors. Writing :math:`F_i, F_j` for the full (pre-swap)
local fields at :math:`i, j` from all four of their neighbors, the energy
change of a swap between unlike spins (:math:`\\sigma_i = -\\sigma_j`) reduces to

.. math::
    \\Delta E = 2 \\sigma_i (F_i - F_j) + 4 J_{ij}.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numba import njit
from scipy.fft import fft2, ifft2
from scipy.ndimage import label as _ndimage_label
from scipy.optimize import brentq


@dataclass
class KawasakiConfig:
    """Parameters for an anisotropic Kawasaki-dynamics quench.

    The lattice is first equilibrated at `T_initial` under Kawasaki dynamics,
    then instantaneously cooled to `T_final` and evolved for `max_sweeps`
    sweeps, with the directional spin-spin correlation functions recorded at
    logarithmically spaced sweep counts. Averaging over `n_replicas`
    independent runs suppresses realization noise in the extracted domain sizes.

    Attributes:
        L: Linear lattice dimension (lattice has L * L spins).
        Jx: Horizontal (row-direction) nearest-neighbor coupling.
        Jy: Vertical (column-direction) nearest-neighbor coupling.
        T_initial: Temperature the lattice is equilibrated at before the quench.
        T_final: Post-quench temperature the system evolves at.
        concentration: Fraction of up (+1) spins in the initial condition.
            0.5 is the critical, symmetric quench (bicontinuous spinodal
            decomposition); values away from 0.5 are off-critical quenches
            into the minority-droplet/nucleation regime. Because Kawasaki
            dynamics conserves total magnetization exactly, this initial
            fraction is also the fraction throughout the entire run.
        n_replicas: Number of independent quench realizations to average over.
        max_sweeps: Number of post-quench sweeps to evolve.
        n_time_samples: Number of logarithmically spaced sweep counts to sample.
        eq_sweeps_initial: Sweeps used to equilibrate at T_initial before the quench.
        seed: Base random seed; each replica gets a derived, distinct seed.
    """

    L: int = 96
    Jx: float = 1.0
    Jy: float = 0.5
    T_initial: float | None = None
    T_final: float | None = None
    concentration: float = 0.5
    n_replicas: int = 16
    max_sweeps: int = 10000
    n_time_samples: int = 30
    eq_sweeps_initial: int = 200
    seed: int = 123

    def __post_init__(self) -> None:
        """Fill in T_initial/T_final relative to the anisotropic T_c if unset."""
        tc = anisotropic_critical_temperature(self.Jx, self.Jy)
        if self.T_final is None:
            self.T_final = 0.65 * tc
        if self.T_initial is None:
            self.T_initial = 3.0 * tc

    def temperatures_str(self) -> str:
        """Human-readable summary of the quench temperatures."""
        return f"T_initial={self.T_initial:.4f}, T_final={self.T_final:.4f}"


@dataclass
class KawasakiResult:
    """Directional domain-growth and entropy-production kinetics from a
    Kawasaki-dynamics quench.

    Attributes:
        t: Post-quench sweep counts (Monte Carlo time) at which observables were sampled.
        domain_size_x: Horizontal characteristic domain size L_x(t), averaged over replicas.
        domain_size_x_err: Standard error of L_x(t) across replicas.
        domain_size_y: Vertical characteristic domain size L_y(t), averaged over replicas.
        domain_size_y_err: Standard error of L_y(t) across replicas.
        entropy_production: Per-spin entropy production rate S_dot(t), averaged over replicas.
        entropy_production_err: Standard error of S_dot(t) across replicas.
    """

    t: np.ndarray
    domain_size_x: np.ndarray
    domain_size_x_err: np.ndarray
    domain_size_y: np.ndarray
    domain_size_y_err: np.ndarray
    entropy_production: np.ndarray = field(default_factory=lambda: np.array([]))
    entropy_production_err: np.ndarray = field(default_factory=lambda: np.array([]))


def anisotropic_critical_temperature(Jx: float, Jy: float) -> float:
    """Solve Onsager's anisotropic criticality condition for T_c(Jx, Jy).

    Finds the unique root of sinh(2*Jx/T) * sinh(2*Jy/T) = 1. Reduces to the
    isotropic result T_c = 2J / ln(1 + sqrt(2)) when Jx = Jy = J.

    Args:
        Jx: Horizontal nearest-neighbor coupling.
        Jy: Vertical nearest-neighbor coupling.

    Returns:
        The critical temperature T_c (k_B = 1).
    """

    def _condition(T: float) -> float:
        return np.sinh(2.0 * Jx / T) * np.sinh(2.0 * Jy / T) - 1.0

    # Bracket the root: the condition function is strictly decreasing in T,
    # diverging to +inf as T -> 0+ and to -1 as T -> inf. t_lo is kept away
    # from 0 to avoid a harmless sinh() overflow warning at the bracket edge.
    t_lo = 0.05 * min(Jx, Jy)
    t_hi = 50.0 * max(Jx, Jy)
    with np.errstate(over="ignore"):
        return brentq(_condition, t_lo, t_hi)


def init_lattice(L: int, seed: int, concentration: float = 0.5) -> np.ndarray:
    """Initialize an L x L lattice of shuffled +-1 spins ("hot start") with
    an *exact* `concentration` fraction of +1 sites (rounded to the nearest
    integer count), rather than an independent per-site coin flip.

    Kawasaki dynamics conserves total magnetization exactly, so fixing the
    exact count (not merely its expectation) keeps every replica at
    precisely the same concentration for its entire run -- important when
    comparing domain-growth statistics across replicas at low concentration,
    where per-site sampling noise in the realized count would otherwise
    vary the effective minority volume fraction replica to replica.

    Args:
        L: Linear lattice dimension.
        seed: Seed for the NumPy random generator.
        concentration: Fraction of up (+1) spins. 0.5 gives the usual
            unbiased critical quench; off-critical quenches use a value
            elsewhere in (0, 1).

    Returns:
        An (L, L) array of dtype int8 with entries in {-1, +1}.
    """
    N = L * L
    n_up = round(concentration * N)
    spins = np.full(N, -1, dtype=np.int8)
    spins[:n_up] = 1
    rng = np.random.default_rng(seed)
    rng.shuffle(spins)
    return spins.reshape(L, L)


@njit(cache=True)
def _local_field(lattice: np.ndarray, i: int, j: int, Jx: float, Jy: float) -> float:
    """Full anisotropic local field at site (i, j) from all four neighbors."""
    L = lattice.shape[0]
    return (
        Jx * lattice[i, (j + 1) % L]
        + Jx * lattice[i, (j - 1) % L]
        + Jy * lattice[(i + 1) % L, j]
        + Jy * lattice[(i - 1) % L, j]
    )


@njit(cache=True)
def _kawasaki_sweep(lattice: np.ndarray, beta: float, Jx: float, Jy: float) -> float:
    """Perform one Kawasaki sweep (L*L exchange attempts) in place.

    Each attempt picks a random site and a random nearest-neighbor direction,
    proposing to exchange the two spins. Exchanges between equal spins are a
    no-op and skipped; exchanges between unlike spins are accepted with the
    Metropolis probability min(1, exp(-beta * dE)), where dE is derived from
    the local fields at the two sites (see module docstring). Total
    magnetization is exactly conserved by construction.

    Returns:
        The total system energy change summed over all accepted exchanges
        this sweep (the heat absorbed by the thermal bath is its negative).
    """
    L = lattice.shape[0]
    total_dE = 0.0
    for _ in range(L * L):
        i = np.random.randint(0, L)
        j = np.random.randint(0, L)
        direction = np.random.randint(0, 4)
        if direction == 0:
            i2, j2, J_bond = i, (j + 1) % L, Jx
        elif direction == 1:
            i2, j2, J_bond = i, (j - 1) % L, Jx
        elif direction == 2:
            i2, j2, J_bond = (i + 1) % L, j, Jy
        else:
            i2, j2, J_bond = (i - 1) % L, j, Jy

        s_i = lattice[i, j]
        s_j = lattice[i2, j2]
        if s_i == s_j:
            continue

        F_i = _local_field(lattice, i, j, Jx, Jy)
        F_j = _local_field(lattice, i2, j2, Jx, Jy)
        dE = 2.0 * s_i * (F_i - F_j) + 4.0 * J_bond

        if dE <= 0.0 or np.random.random() < np.exp(-beta * dE):
            lattice[i, j] = s_j
            lattice[i2, j2] = s_i
            total_dE += dE

    return total_dE


@njit(cache=True)
def _init_lattice_jit(L: int, concentration: float) -> np.ndarray:
    """Random +-1 lattice, with an *exact* `concentration` fraction of +1
    sites, drawn from Numba's own RNG (seedable with np.random.seed inside
    jit). See `init_lattice`'s docstring for why the count is exact rather
    than a per-site Bernoulli draw.
    """
    N = L * L
    n_up = int(round(concentration * N))
    flat = np.full(N, -1, dtype=np.int8)
    flat[:n_up] = 1
    np.random.shuffle(flat)
    return flat.reshape(L, L)


@njit(cache=True)
def _seed_and_init_lattice(L: int, seed: int, concentration: float) -> np.ndarray:
    """Seed Numba's RNG and return a fresh random +-1 lattice.

    Seeding Numba's RNG (rather than only seeding the initial lattice via
    NumPy's generator) makes every subsequent jitted sweep that follows --
    not just the initial condition -- deterministic given `seed`.
    """
    np.random.seed(seed)
    return _init_lattice_jit(L, concentration)


@njit(cache=True)
def _run_n_sweeps(lattice: np.ndarray, beta: float, Jx: float, Jy: float, n_sweeps: int) -> None:
    """Advance `lattice` by n_sweeps Kawasaki sweeps in place."""
    for _ in range(n_sweeps):
        _kawasaki_sweep(lattice, beta, Jx, Jy)


@njit(cache=True)
def _run_n_sweeps_with_heat(
    lattice: np.ndarray, beta: float, Jx: float, Jy: float, n_sweeps: int
) -> float:
    """Advance `lattice` by n_sweeps Kawasaki sweeps in place.

    Returns:
        The total system energy change (sum of accepted dE) over all n_sweeps sweeps.
    """
    total_dE = 0.0
    for _ in range(n_sweeps):
        total_dE += _kawasaki_sweep(lattice, beta, Jx, Jy)
    return total_dE


def _axis_correlation_xy(lattice: np.ndarray, r_max: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute the horizontal and vertical *connected* spin autocorrelations
    C_x(r), C_y(r) for r = 0..r_max via 2D FFT (Wiener-Khinchin theorem),
    O(L^2 log L).

    Unlike the isotropic engine's axis-averaged correlation, the two
    directions are kept separate here so that anisotropic coarsening
    (Jx != Jy) can be resolved independently along each axis.

    At a critical (concentration=0.5) quench the mean magnetization m is
    zero and this reduces to the raw correlation <sigma_i sigma_{i+r}>. Away
    from criticality m != 0, so the raw correlation asymptotes to m^2 > 0 at
    large r instead of decaying through the 0.5 threshold that
    `domain_size_from_correlation` looks for -- the standard fix is the
    *normalized connected* correlation function
        g(r) = (<sigma_i sigma_{i+r}> - m^2) / (1 - m^2),
    which isolates the fluctuation/domain-structure part of the correlation
    and is renormalized so that g(0) = 1 exactly, matching the convention
    the raw correlation already used at criticality.

    Returns:
        (C_x, C_y): each of shape (r_max + 1,), the normalized connected
        correlation along the horizontal (column) and vertical (row)
        directions respectively.
    """
    L = lattice.shape[0]
    spins = lattice.astype(np.float64)
    power_spectrum = np.abs(fft2(spins)) ** 2
    autocorr = ifft2(power_spectrum).real / (L * L)  # autocorr[dy, dx], periodic

    m2 = float(np.mean(spins)) ** 2
    denom = max(1.0 - m2, 1e-12)

    C_x = np.empty(r_max + 1)
    C_y = np.empty(r_max + 1)
    C_x[0] = 1.0
    C_y[0] = 1.0
    if r_max > 0:
        C_x[1:] = (autocorr[0, 1 : r_max + 1] - m2) / denom
        C_y[1:] = (autocorr[1 : r_max + 1, 0] - m2) / denom
    return C_x, C_y


def domain_size_from_correlation(C: np.ndarray) -> float:
    """Extract the characteristic domain size as the r where C(r) crosses 0.5.

    Linearly interpolates between the two integer separations bracketing the
    crossing. Returns NaN if C(r) never decays to 0.5 within the sampled range.
    """
    for r in range(len(C) - 1):
        if C[r] >= 0.5 > C[r + 1]:
            span = C[r] - C[r + 1]
            if span <= 0.0:
                return float(r)
            frac = (C[r] - 0.5) / span
            return r + frac
    return float("nan")


def _log_time_checkpoints(max_sweeps: int, n_points: int) -> np.ndarray:
    """Return unique, ascending, logarithmically spaced integer sweep counts in [1, max_sweeps]."""
    raw = np.logspace(0.0, np.log10(max_sweeps), n_points)
    checkpoints = np.unique(np.round(raw).astype(np.int64))
    return checkpoints[checkpoints >= 1]


def _run_quench_replica(
    L: int,
    seed: int,
    beta_initial: float,
    beta_final: float,
    Jx: float,
    Jy: float,
    concentration: float,
    eq_sweeps_initial: int,
    checkpoints: np.ndarray,
    r_max: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run one full, independently seeded Kawasaki quench replica: init ->
    equilibrate at T_initial -> quench to T_final -> record C_x(r,t),
    C_y(r,t), and accepted-exchange energy change at each checkpoint.

    Sweeps advance in Numba-jitted chunks between checkpoints; the FFT-based
    correlation function (relying on SciPy) cannot run inside nopython-mode
    Numba code, so this outer orchestration stays in plain Python while the
    hot inner loops stay jitted. Heat exchange is only tracked post-quench.

    Returns:
        (Cx_traj, Cy_traj, delta_E_traj): Cx_traj and Cy_traj have shape
        (len(checkpoints), r_max + 1). delta_E_traj has shape
        (len(checkpoints),): total accepted-exchange energy change per
        inter-checkpoint interval.
    """
    lattice = _seed_and_init_lattice(L, seed, concentration)
    _run_n_sweeps(lattice, beta_initial, Jx, Jy, eq_sweeps_initial)

    n_checkpoints = len(checkpoints)
    Cx_traj = np.zeros((n_checkpoints, r_max + 1))
    Cy_traj = np.zeros((n_checkpoints, r_max + 1))
    delta_E_traj = np.zeros(n_checkpoints)
    sweep = 0
    for k in range(n_checkpoints):
        n_sweeps_interval = int(checkpoints[k]) - sweep
        delta_E_traj[k] = _run_n_sweeps_with_heat(lattice, beta_final, Jx, Jy, n_sweeps_interval)
        sweep = int(checkpoints[k])
        Cx_traj[k], Cy_traj[k] = _axis_correlation_xy(lattice, r_max)
    return Cx_traj, Cy_traj, delta_E_traj


def run_quench_kinetics(config: KawasakiConfig) -> KawasakiResult:
    """Simulate a T_initial -> T_final Kawasaki quench and extract directional
    domain-growth and entropy-production kinetics.

    For each of `config.n_replicas` independent runs, a lattice is
    equilibrated at `T_initial`, instantaneously cooled to `T_final`, and
    evolved under magnetization-conserving Kawasaki dynamics while sampling
    C_x(r,t), C_y(r,t), and the accepted-exchange energy change at
    logarithmically spaced sweep counts. L_x(t), L_y(t), and S_dot(t) are
    then extracted per replica and averaged.

    Args:
        config: Kawasaki quench simulation parameters.

    Returns:
        A KawasakiResult with L_x(t), L_y(t), S_dot(t), and their standard
        errors across replicas.
    """
    checkpoints = _log_time_checkpoints(config.max_sweeps, config.n_time_samples)
    r_max = config.L // 2
    n_ckpt = len(checkpoints)
    N = config.L * config.L

    interval_lengths = np.empty(n_ckpt)
    interval_lengths[0] = checkpoints[0]
    interval_lengths[1:] = np.diff(checkpoints)

    Lx_replicas = np.full((config.n_replicas, n_ckpt), np.nan)
    Ly_replicas = np.full((config.n_replicas, n_ckpt), np.nan)
    entropy_replicas = np.full((config.n_replicas, n_ckpt), np.nan)

    beta_initial = 1.0 / config.T_initial
    beta_final = 1.0 / config.T_final

    for rep in range(config.n_replicas):
        Cx_traj, Cy_traj, delta_E_traj = _run_quench_replica(
            config.L,
            config.seed + rep,
            beta_initial,
            beta_final,
            config.Jx,
            config.Jy,
            config.concentration,
            config.eq_sweeps_initial,
            checkpoints,
            r_max,
        )
        for k in range(n_ckpt):
            Lx_replicas[rep, k] = domain_size_from_correlation(Cx_traj[k])
            Ly_replicas[rep, k] = domain_size_from_correlation(Cy_traj[k])

        dE_per_sweep_per_spin = delta_E_traj / interval_lengths / N
        entropy_replicas[rep, :] = -dE_per_sweep_per_spin / config.T_final

    with np.errstate(invalid="ignore"):
        domain_size_x = np.nanmean(Lx_replicas, axis=0)
        domain_size_x_err = np.nanstd(Lx_replicas, axis=0) / np.sqrt(config.n_replicas)
        domain_size_y = np.nanmean(Ly_replicas, axis=0)
        domain_size_y_err = np.nanstd(Ly_replicas, axis=0) / np.sqrt(config.n_replicas)
        entropy_production = np.nanmean(entropy_replicas, axis=0)
        entropy_production_err = np.nanstd(entropy_replicas, axis=0) / np.sqrt(config.n_replicas)

    return KawasakiResult(
        t=checkpoints.astype(np.float64),
        domain_size_x=domain_size_x,
        domain_size_x_err=domain_size_x_err,
        domain_size_y=domain_size_y,
        domain_size_y_err=domain_size_y_err,
        entropy_production=entropy_production,
        entropy_production_err=entropy_production_err,
    )


# ---------------------------------------------------------------------------
# Off-critical morphology: droplet-size distribution vs. Lifshitz-Slyozov-
# Wagner (LSW) theory
# ---------------------------------------------------------------------------
#
# Bray's review (Adv. Phys. 43, 357 (1994), sec. 9 "Summary"; see also the
# general-d Model B growth-law argument in sec. 2.5, attributed to Huse)
# states that for conserved-order-parameter (Model B / Kawasaki) coarsening,
# "the growth law is independent of the volume fraction of the phases, but
# the scaling functions are not" -- i.e. L(t) ~ t^(1/3) is predicted to hold
# at any concentration, from the bicontinuous (c=0.5) regime to the dilute
# minority-droplet (off-critical) regime, but the *morphology* and the
# *droplet-size distribution* are expected to change qualitatively. In the
# dilute limit this distribution has an exact closed form from the original
# Lifshitz-Slyozov theory [Lifshitz & Slyozov, J. Phys. Chem. Solids 19, 35
# (1961); Wagner, Z. Elektrochem. 65, 581 (1961)]. This section extracts the
# simulated droplet-size distribution via periodic connected-component
# labelling and provides the closed-form LSW prediction to compare it to.


def _periodic_label(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Connected-component labelling of a boolean mask under periodic
    boundary conditions (plain `scipy.ndimage.label` only handles an open
    boundary, which would spuriously split or duplicate droplets that
    straddle the lattice edge).

    Labels the array normally, then merges any pair of labels that touch
    across the top/bottom or left/right periodic seam via union-find.

    Returns:
        (labels, n_components): `labels` is an (L, L) int array with 0 for
        background and 1..n_components for each merged droplet;
        `n_components` is the number of droplets found.
    """
    labels, n = _ndimage_label(mask)
    if n == 0:
        return labels, 0

    parent = np.arange(n + 1)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in zip(labels[0, :], labels[-1, :]):
        if a != 0 and b != 0:
            union(int(a), int(b))
    for a, b in zip(labels[:, 0], labels[:, -1]):
        if a != 0 and b != 0:
            union(int(a), int(b))

    roots = np.array([find(lbl) for lbl in range(n + 1)])
    unique_roots, new_ids = np.unique(roots, return_inverse=True)
    remap = new_ids  # remap[old_label] -> compact new label (0 stays background-adjacent)
    new_labels = remap[labels]
    # Ensure background (old label 0) maps to new label 0.
    new_labels[labels == 0] = 0
    return new_labels, int(new_labels.max())


def droplet_size_distribution(lattice: np.ndarray, minority_value: int | None = None) -> np.ndarray:
    """Sizes (in lattice sites) of every minority-phase domain ("droplet"),
    found via periodic connected-component labelling.

    Args:
        lattice: An (L, L) array of +-1 spins.
        minority_value: Which spin value (+1 or -1) counts as the minority
            phase. If None, inferred as whichever value has fewer sites.

    Returns:
        1D array of droplet sizes (number of sites each occupies), one entry
        per connected droplet, unsorted.
    """
    if minority_value is None:
        minority_value = -1 if lattice.sum() >= 0 else 1
    mask = lattice == minority_value
    labels, n = _periodic_label(mask)
    if n == 0:
        return np.array([])
    sizes = np.bincount(labels.ravel())[1:]
    return sizes.astype(np.float64)


def lsw_scaling_function(u: np.ndarray) -> np.ndarray:
    """The closed-form Lifshitz-Slyozov-Wagner scaled droplet-radius
    distribution g(u), u = R / R_c (droplet radius scaled by the
    time-dependent critical radius), in the dilute (small minority volume
    fraction) limit.

    .. math::
        g(u) = \\frac{3^4 e}{2^{5/3}} \\, u^2 \\,
               \\frac{\\exp\\!\\big[-1/(1 - 2u/3)\\big]}
                    {(u + 3)^{7/3} (3/2 - u)^{11/3}}, \\quad 0 \\le u < 3/2,

    and g(u) = 0 for u >= 3/2 (droplets larger than 1.5 R_c are forbidden in
    the asymptotic LSW scaling state). Verified numerically to integrate to
    1 over [0, 3/2) (i.e. a properly normalized probability density).

    Reference: Lifshitz & Slyozov, J. Phys. Chem. Solids 19, 35 (1961);
    Wagner, Z. Elektrochem. 65, 581 (1961).
    """
    u = np.asarray(u, dtype=np.float64)
    g = np.zeros_like(u)
    mask = u < 1.5
    x = u[mask]
    prefactor = (3.0**4) * np.e / (2.0 ** (5.0 / 3.0))
    g[mask] = (
        prefactor
        * x**2
        * np.exp(-1.0 / (1.0 - 2.0 * x / 3.0))
        / ((x + 3.0) ** (7.0 / 3.0) * (1.5 - x) ** (11.0 / 3.0))
    )
    return g


def run_quench_to_snapshot(config: KawasakiConfig, seed: int, target_sweep: int) -> np.ndarray:
    """Run one Kawasaki quench replica up to `target_sweep` post-quench
    sweeps and return the raw lattice snapshot.

    Used for morphology analysis (e.g. `droplet_size_distribution`) rather
    than the correlation-function-based domain-size pipeline in
    `run_quench_kinetics`.
    """
    beta_initial = 1.0 / config.T_initial
    beta_final = 1.0 / config.T_final
    lattice = _seed_and_init_lattice(config.L, seed, config.concentration)
    _run_n_sweeps(lattice, beta_initial, config.Jx, config.Jy, config.eq_sweeps_initial)
    _run_n_sweeps(lattice, beta_final, config.Jx, config.Jy, target_sweep)
    return lattice
