"""Bounded, exploratory reanalysis of already known Kawasaki trajectories.

Run from the repository root with:
    .venv311/bin/python -m research.observation_sensitivity --output OUTPUT

This never advances a simulation. The protocol fixes two length definitions,
three observation operators, a common window and all nine paired contrasts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from research.chord_observation import foreground_chords, majority_observation
from research.fraction_matching import TIE_SEEDS, integrate, match_fraction
from research.growth_reliability import paired_fit
from research.imaging import image_length

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research/runs/growth_reliability_holdout_v1"
ORIGINAL = ROOT / "research/results/growth_reliability_fresh_2026-09-19_v1"
PROTOCOL = "research/CHORD_OBSERVATION_PROTOCOL_2026-09-26.md"
OPERATORS = ("native", "matched", "majority")
METRICS = ("half", "chord")
SERIES = tuple(f"{op}_{metric}" for metric in METRICS for op in OPERATORS)
SOURCES = (
    "research/observation_sensitivity.py", "research/chord_observation.py",
    "research/fraction_matching.py", "research/growth_reliability.py",
    "research/imaging.py", "research/metrology.py", "research/reference_measurements.py",
    "tests/test_observation_sensitivity.py", "tests/test_chord_observation.py", PROTOCOL,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    return value


def write_json(path, value):
    path.write_text(json.dumps(clean_json(value), indent=2, allow_nan=False) + "\n")


def write_csv(path, rows):
    if not rows:
        raise ValueError("Refuse empty evidence table")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def common_mask(raw):
    """raw: metric x trajectory x time x (native, majority, five ties)."""
    raw = np.asarray(raw, dtype=float)
    if raw.ndim != 4 or raw.shape[0] != 2 or raw.shape[3] != 7:
        raise ValueError("Expected two metrics and seven operator/tie outcomes")
    return np.all(np.isfinite(raw) & (raw > 0), axis=(0, 1, 3))


def series_arrays(raw):
    """Average matched tie LENGTHS within a run, never count ties as runs."""
    return np.stack([
        value
        for metric in range(2)
        for value in (raw[metric, :, :, 0], raw[metric, :, :, 2:].mean(axis=-1),
                      raw[metric, :, :, 1])
    ])


def contrast_definitions():
    definitions = []
    def add(name, terms, kind):
        weights = np.zeros(len(SERIES))
        for key, weight in terms.items():
            weights[SERIES.index(key)] = weight
        definitions.append((name, weights, kind))
    for metric in METRICS:
        for op in OPERATORS[1:]:
            add(f"{op} - native ({metric})",
                {f"{op}_{metric}": 1, f"native_{metric}": -1}, "processing")
    for op in OPERATORS:
        add(f"chord - half ({op})", {f"{op}_chord": 1, f"{op}_half": -1}, "observable")
    for op in OPERATORS[1:]:
        add(f"{op}: chord shift - half shift",
            {f"{op}_chord": 1, "native_chord": -1,
             f"{op}_half": -1, "native_half": 1}, "interaction")
    return definitions


def fit_comparison(times, values, draws=1000, seed=912):
    """One paired trajectory-resampling schedule for all six series."""
    t = np.asarray(times, dtype=float)
    a = np.asarray(values, dtype=float)
    if (t.ndim != 1 or len(t) < 4 or not np.all(np.isfinite(t))
            or np.any(t <= 0) or np.any(np.diff(t) <= 0) or t[-1] / t[0] < 5):
        raise ValueError("Common times need >=4 points and >=5-fold span")
    if (a.ndim != 3 or a.shape[0] != 6 or a.shape[1] < 2 or a.shape[2] != len(t)
            or not np.all(np.isfinite(a) & (a > 0))):
        raise ValueError("Need six resolved series, each trajectory by common time")
    if not isinstance(draws, int) or draws < 2:
        raise ValueError("Need at least two bootstrap draws")
    x = np.log(t)
    x -= x.mean()
    weights = x / (x @ x)
    alpha = np.log(a.mean(axis=1)) @ weights
    indices = np.random.default_rng(seed).integers(a.shape[1], size=(draws, a.shape[1]))
    boot = (np.log(a[:, indices, :].mean(axis=2)) @ weights).T
    intervals = np.percentile(boot, [2.5, 97.5], axis=0)
    fits = [dict(series=key, alpha=float(alpha[i]), low=float(intervals[0, i]),
                 high=float(intervals[1, i])) for i, key in enumerate(SERIES)]
    contrasts = []
    for name, coeff, kind in contrast_definitions():
        low, high = np.percentile(boot @ coeff, [2.5, 97.5])
        contrasts.append(dict(contrast=name, kind=kind, delta=float(alpha @ coeff),
                              low=float(low), high=float(high)))
    return fits, contrasts


def original_primary_check(times, raw, composition, reference_rows):
    # Separate original native/matched half-height mask, not the new chord mask.
    primary = np.take(raw[0], [0, 2, 3, 4, 5, 6], axis=-1)
    mask = np.all(np.isfinite(primary) & (primary > 0), axis=(0, 2))
    arrays = series_arrays(raw)
    fit = paired_fit(times[mask], arrays[0][:, mask], arrays[1][:, mask])
    rows = [r for r in reference_rows if float(r["composition"]) == composition
            and r["factor"] == "4" and r["origin"] == "0"
            and r["observable"] == "half" and r["stage"] == "matched"]
    if len(rows) != 1:
        raise AssertionError("Cannot identify original primary estimate")
    old = rows[0]
    errors = {key: abs(fit[key] - float(old[key]))
              for key in ("native_alpha", "alpha", "delta", "low", "high")}
    if (not all(np.isfinite(v) and v < 1e-12 for v in errors.values())
            or int(mask.sum()) != int(old["retained_points"])):
        raise AssertionError(f"Original primary estimate did not reproduce: {errors}")
    return dict(composition=composition, passed=True, points=int(mask.sum()),
                max_absolute_error=max(errors.values()), **fit)


def measure_archives(expected):
    rows, grouped, configs = [], {}, {}
    common_times = None
    tc = 2 / np.log(1 + np.sqrt(2))
    for name in sorted(expected):
        with np.load(RAW / name, allow_pickle=False) as data:
            config = json.loads(str(data["config"]))
            c = float(config["concentration"])
            if (config["L"] != 128 or config["Jx"] != 1 or config["Jy"] != 1
                    or c not in (.5, .15) or config["eq_sweeps_initial"] != 200
                    or not np.isclose(config["T_final"], .65 * tc, rtol=0, atol=1e-12)
                    or not np.isclose(config["T_initial"], 3 * tc, rtol=0, atol=1e-12)):
                raise AssertionError(f"Unexpected experiment metadata: {name}")
            times_all, states = data["t"], data["snapshots"]
            select = (times_all >= 1000) & (times_all <= 20000)
            times = times_all[select]
            if common_times is None:
                common_times = times.copy()
            if len(times) != 24 or not np.array_equal(common_times, times):
                raise AssertionError("Archived time grid changed")
            if states.shape != (len(times_all), 128, 128) or not np.all(np.isin(states, [-1, 1])):
                raise AssertionError("Invalid archived lattice")
            fractions = ((states.astype(float) + 1) / 2).mean(axis=(1, 2))
            if not np.all(fractions == fractions[0]):
                raise AssertionError("Underlying trajectory composition changed")
            values = np.full((2, len(times), 7), np.nan)
            for ti, (t, state) in enumerate(zip(times, states[select])):
                native = ((state + 1) // 2).astype(np.uint8)
                fraction = float(native.mean())
                average = integrate(native, 4)
                variants = [("native", -1, native, 1.),
                            ("majority", -1, majority_observation(native), 1.)]
                variants += [("matched", seed, match_fraction(average, fraction, seed)[0], 4.)
                             for seed in TIE_SEEDS]
                for vi, (op, tie, field, spacing) in enumerate(variants):
                    half = image_length(field, pixel_size=spacing)
                    chord = foreground_chords(field, spacing=spacing)
                    values[:, ti, vi] = half["length"], chord["chord"]
                    rows.append(dict(archive=name, composition=c, sweep=int(t), operator=op,
                        tie_seed=tie, pixel_spacing=spacing, native_fraction=fraction,
                        observed_fraction=float(field.mean()), half=half["length"],
                        half_x=half["length_x"], half_y=half["length_y"],
                        half_resolved=half["resolved"], **chord))
            grouped.setdefault(c, []).append(values)
            configs[name] = config
        print(f"Measured {name}: {len(times)} saved lattices", flush=True)
    if set(grouped) != {.5, .15} or any(len(v) != 8 for v in grouped.values()):
        raise AssertionError("Need exactly eight trajectories per composition")
    return rows, {c: np.stack(v, axis=1) for c, v in grouped.items()}, common_times, configs


def diagnostic_histories(rows):
    groups = {}
    for row in rows:
        groups.setdefault((row["composition"], row["operator"], row["sweep"]), []).append(row)
    # Each run contributes equally: all matched runs have the same five ties.
    return [dict(composition=c, operator=op, sweep=t,
                 observed_fraction=float(np.mean([r["observed_fraction"] for r in rs])),
                 censored_fraction=float(np.mean([r["censored_fraction"] for r in rs])),
                 complete_chords=float(np.mean([r["complete_chords"] for r in rs])),
                 half=float(np.mean([r["half"] for r in rs])),
                 chord=float(np.mean([r["chord"] for r in rs])))
            for (c, op, t), rs in sorted(groups.items())]


def plot_results(out, groups):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ("#294e80", "#bd5915", "#16806d")
    names = ("Native", "4×4 fraction-matched", "One majority pass")
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for row, c in enumerate((.5, .15)):
        group = groups[c]
        t, a = np.array(group["times"]), group["values"]
        for col, metric in enumerate(METRICS):
            ax = axes[row, col]
            for op in range(3):
                index = col * 3 + op
                ax.loglog(t, a[index].mean(axis=0), color=colors[op], label=names[op])
            ax.set(title=f"c = {c:.2f} · {'Half-height' if col == 0 else 'Foreground chord'}",
                   xlabel="Post-quench sweeps", ylabel="Mean length (native lattice sites)")
            ax.grid(alpha=.2, which="both")
    axes[0, 0].legend(fontsize=9)
    fig.suptitle("Same saved trajectories, different observation and length definitions", fontsize=13)
    fig.savefig(out / "growth_curves.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    for ax, c in zip(axes, (.5, .15)):
        items = [r for r in groups[c]["contrasts"] if r["kind"] == "processing"]
        for i, item in enumerate(items):
            ax.plot([item["low"], item["high"]], [i, i], color=colors[i % 2 + 1], lw=2)
            ax.plot(item["delta"], i, "o", color=colors[i % 2 + 1])
        ax.axvline(0, color="gray", lw=1)
        ax.set(yticks=range(4), yticklabels=[r["contrast"] for r in items],
               xlabel="Processed minus native fitted exponent", title=f"c = {c:.2f}")
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=.2)
    fig.suptitle("Processing effects · paired 95% trajectory-bootstrap intervals", fontsize=12)
    fig.savefig(out / "processing_shifts.png", dpi=160)
    plt.close(fig)


def render_report(out, summary):
    def table(rows, fields):
        def cell(v):
            return html.escape(f"{v:.5f}" if isinstance(v, float) else str(v))
        return ("<table><thead><tr>" + "".join(f"<th>{html.escape(f)}</th>" for f in fields)
                + "</tr></thead><tbody>" + "".join("<tr>" + "".join(
                    f"<td>{cell(r[f])}</td>" for f in fields) + "</tr>" for r in rows)
                + "</tbody></table>")
    overview = []
    blocks = []
    for group in summary["groups"]:
        alphas = {r["series"]: r["alpha"] for r in group["fits"]}
        for metric in METRICS:
            overview.append(dict(composition=group["composition"], measurement=metric,
                native=alphas[f"native_{metric}"], matched=alphas[f"matched_{metric}"],
                majority=alphas[f"majority_{metric}"]))
        blocks.append(f"<h2>Species fraction c = {group['composition']:.2f}</h2>"
            f"<p>Eight independent trajectories; {group['retained_points']} of 24 times retained. "
            f"Shared window: {group['first_sweep']}–{group['last_sweep']} post-quench sweeps. "
            f"Removed times: {html.escape(str(group['removed_times']))}.</p>"
            + table(group["fits"], ("series", "alpha", "low", "high"))
            + "<h3>Every planned paired contrast</h3>"
            + table(group["contrasts"], ("contrast", "delta", "low", "high")))
    diagnostics = summary["diagnostic_ranges"]
    content = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Observation sensitivity — exploratory appendix</title>
<style>body{font:17px/1.55 system-ui,sans-serif;color:#253247;max-width:1100px;margin:36px auto;padding:0 22px}
h1{font-size:30px;line-height:1.2}h2{margin-top:40px}table{border-collapse:collapse;width:100%;font-size:14px;margin:18px 0}
th,td{padding:8px;border-bottom:1px solid #d7dee8;text-align:left}th{background:#eef2f6}
img{width:100%;height:auto}a{color:#1e589b}.notice{background:#fff4dc;padding:16px;border-left:4px solid #aa6900}
@media(max-width:700px){table{font-size:11px}th,td{padding:4px}}</style>
<h1>Does the processing effect depend on how length is measured?</h1>
<p>26 September 2026 · AI-assisted exploratory appendix · not a new holdout or an external review.</p>
<div class="notice">The existing question stays fixed: does preserving species fraction after reduced-resolution
segmentation preserve the native finite-window growth exponent? This appendix checks a second length
definition and a local majority filter. It is not a test that processing should recover 1/3.</div>
<h2>The short answer</h2>
<p>In these saved trajectories, fraction matching changes the chord-based exponent much less than the
half-height exponent. The majority filter decreases the half-height exponent but increases the chord exponent.
For the fraction-matched c = 0.15 images, the two exponents are very close and their paired difference interval
includes zero. Processing effects depend on the length definition; they are not always large or in the same direction.</p>
""" + table(overview, ("composition", "measurement", "native", "matched", "majority")) + """
<p>Numbers above are fitted exponents, not domain lengths. The full paired intervals and every planned
contrast are retained below. This supports a sensitivity warning, not a claim that one method is the true answer.</p>
<h2>What was compared</h2>
<p>The same 16 archived 128×128 Kawasaki trajectories (eight each at c = 0.50 and 0.15), isotropic
Jx = Jy = 1 and T = 0.65 Tc. All six measurement series use the same positive, resolved times in each
composition. No new dynamics were run. These short windows are an observation test, not an asymptotic-growth test.</p>
<p><b>Observation:</b> native pixels; origin-zero 4×4 block means with nearest-count fraction matching;
or exactly one simultaneous five-site majority pass. Five fixed tie priorities are averaged within each
matched trajectory/time, not counted as extra independent runs. Only the observation filter uses periodic neighbours.</p>
<p>Here “fraction” means the fraction of +1-labelled sites or pixels, not a calibrated phase volume fraction
of a real alloy. Matching is exact at c = 0.50. At nominal c = 0.15, the native fraction is 0.1500244 and
the nearest coarse-grid fraction is 0.1503906; that small, disclosed pixel-count residual is unavoidable on this grid.</p>
<p><b>Length:</b> the existing normalized finite-image covariance half-height, or the number-weighted mean
complete foreground chord across horizontal and vertical lines. Foreground means the +1 species.
Chords touching image edges are excluded and counted; both measurements are non-wrapping.
Coarse pixel spacing is converted back to native lattice sites. Neither length is a uniquely correct domain size.</p>
<img src="growth_curves.png" alt="Growth curves for both compositions and both length definitions">
<img src="processing_shifts.png" alt="All four processing shifts for each composition with paired intervals">
""" + "".join(blocks) + """
<h2>What these intervals do and do not mean</h2>
<p>Slopes are ordinary least-squares fits of log ensemble-mean length against log sweeps. The 1,000 paired
bootstrap draws resample eight whole trajectories, using the same indices for all series (seed 912).
The percentile 95% intervals describe run-resampling uncertainty; they do not remove systematic bias,
establish a mechanism, or cover every possible analysis choice. The 18 correlated contrasts are descriptive
and not adjusted for multiple comparisons. Small, opposite or unresolved effects must also be reported.</p>
<h2>Boundary and composition checks</h2>
<p>Censoring below is the fraction of foreground runs touching an edge, not the phase fraction.
The ranges cover the time history of ensemble-mean diagnostics, with ties averaged within runs.
Discarding edge chords favours shorter chords and can bias the slope as domains grow.
This chord convention is not a finite-size correction. The majority pass can change observed species fraction.</p>
""" + table(diagnostics, ("composition", "operator", "fraction_min", "fraction_max",
                            "censored_min", "censored_max", "complete_min", "complete_max")) + """
<h2>Checks and limits</h2>
<p>The original native/fraction-matched half-height estimates and paired intervals were recomputed from
archived snapshots using the original measurement definitions and time mask, and matched the archive to 1e−12.
Known-size chord, boundary, unit-conversion, simultaneous-filter and synthetic-slope tests are supplied.
Input and source hashes were captured before measurement and checked again afterwards.
This is internal software verification, not independent academic validation.</p>
<p>The data and primary effects were already known before this analysis; the protocol is a local dated plan,
not an external preregistration. The existing reviewer PDF and evidence pack were not changed.
There is no quantitative prediction for a real alloy, proof of a new growth law, or novelty claim here.</p>
<p>Context: <a href="https://arxiv.org/abs/1001.3985">Majumder and Das (2010)</a> use a majority-spin observation
rule and interface-to-interface lengths; our finite, foreground-only chords are not their exact implementation.
<a href="https://arxiv.org/abs/1712.03183">Ledesma-Alonso et al.</a> address resolution sensitivity of microstructure descriptors.</p>
<h2>Evidence</h2><p><a href="summary.json">All results and masks</a> ·
<a href="observations.csv">Every measurement and tie outcome</a> ·
<a href="contrasts.csv">All paired contrasts</a> · <a href="histories.csv">Time-dependent diagnostics</a> ·
<a href="freeze.json">Before-analysis hashes</a> · <a href="manifest.json">After-analysis verification</a> ·
<a href="protocol.md">Fixed exploratory protocol</a></p></html>
"""
    (out / "report.html").write_text(content)


def run(output):
    import scipy
    import matplotlib
    out = Path(output).resolve()
    if out.exists():
        raise FileExistsError("Use a new output directory; never overwrite evidence")
    source_hashes = {p: sha(ROOT / p) for p in SOURCES}
    original_manifest = json.loads((ORIGINAL / "manifest.json").read_text())
    expected = original_manifest["input_sha256"]
    if len(expected) != 16 or {p.name for p in RAW.glob("*.npz")} != set(expected):
        raise AssertionError("Unexpected archived input set")
    actual = {name: sha(RAW / name) for name in expected}
    if actual != expected or sha(ORIGINAL / "fits.csv") != original_manifest["outputs"]["fits.csv"]:
        raise AssertionError("Original input or result hashes changed")
    evidence_paths = (ORIGINAL / "manifest.json", ORIGINAL / "fits.csv")
    evidence_hashes = {str(p.relative_to(ROOT)): sha(p) for p in evidence_paths}
    out.mkdir(parents=True)
    freeze = dict(status="declared_before_reanalysis", exploratory_known_data=True,
        timestamp=datetime.now(timezone.utc).isoformat(), sources=source_hashes,
        original_evidence=evidence_hashes, input_sha256=actual,
        python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
        matplotlib=matplotlib.__version__, bootstrap_draws=1000, bootstrap_seed=912,
        tie_seeds=TIE_SEEDS, planned_contrasts=18)
    write_json(out / "freeze.json", freeze)
    (out / "protocol.md").write_bytes((ROOT / PROTOCOL).read_bytes())
    rows, raw_groups, times, configs = measure_archives(expected)
    with (ORIGINAL / "fits.csv").open() as stream:
        reference_rows = list(csv.DictReader(stream))
    groups, primaries, all_contrasts, failures = {}, [], [], []
    for c, raw in sorted(raw_groups.items(), reverse=True):
        primaries.append(original_primary_check(times, raw, c, reference_rows))
        mask = common_mask(raw)
        values = series_arrays(raw)[:, :, mask]
        selected = times[mask]
        removed = []
        for ti in np.flatnonzero(~mask):
            invalid = np.argwhere(~(np.isfinite(raw[:, :, ti, :]) & (raw[:, :, ti, :] > 0)))
            removed.append(dict(sweep=int(times[ti]), invalid_metric_run_variant=invalid.tolist()))
        try:
            fits, contrasts = fit_comparison(selected, values)
        except ValueError as error:
            failures.append(dict(composition=c, error=str(error), removed_times=removed))
            continue
        group = dict(composition=c, trajectories=8, retained_points=int(mask.sum()),
            first_sweep=int(selected[0]), last_sweep=int(selected[-1]),
            removed_times=removed, times=selected.tolist(), fits=fits, contrasts=contrasts,
            values=values)
        groups[c] = group
        all_contrasts += [dict(composition=c, **r) for r in contrasts]
    histories = diagnostic_histories(rows)
    ranges = []
    for c in (.5, .15):
        for op in OPERATORS:
            selected = [r for r in histories if r["composition"] == c and r["operator"] == op]
            ranges.append(dict(composition=c, operator=op,
                fraction_min=min(r["observed_fraction"] for r in selected),
                fraction_max=max(r["observed_fraction"] for r in selected),
                censored_min=min(r["censored_fraction"] for r in selected),
                censored_max=max(r["censored_fraction"] for r in selected),
                complete_min=min(r["complete_chords"] for r in selected),
                complete_max=max(r["complete_chords"] for r in selected)))
    summary = dict(status="complete" if not failures else "unresolved_common_window",
        independent_trajectories=16, measured_saved_lattices=384, measurement_rows=len(rows),
        exploratory=True, primary_reproduction=primaries, failures=failures,
        groups=[{k: v for k, v in g.items() if k != "values"} for g in groups.values()],
        diagnostic_ranges=ranges, configurations=configs)
    write_csv(out / "observations.csv", rows)
    write_csv(out / "histories.csv", histories)
    write_json(out / "summary.json", summary)
    if all_contrasts:
        write_csv(out / "contrasts.csv", all_contrasts)
    if not failures:
        plot_results(out, groups)
        render_report(out, summary)
    unchanged = (source_hashes == {p: sha(ROOT / p) for p in SOURCES}
        and actual == {name: sha(RAW / name) for name in expected}
        and evidence_hashes == {p: sha(ROOT / p) for p in evidence_hashes})
    if not unchanged:
        raise AssertionError("Input, protocol, source or primary evidence changed during reanalysis")
    write_json(out / "manifest.json", dict(status=summary["status"], unchanged_verified=True,
        completed_at=datetime.now(timezone.utc).isoformat(),
        outputs={p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}))
    print(json.dumps(clean_json(dict(status=summary["status"],
        primary_reproduction=primaries, groups=summary["groups"], failures=failures)), indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)
