"""Post-hoc slope-error budgets on the unchanged, previously inspected fresh cohort.

No simulation, experimental kinetics, novel theorem, independent holdout, or
automatic resolution validation is claimed. See the dated supporting protocol.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from research.fraction_matching import TIE_SEEDS
from research.kinetic_error_budget import (paired_budget, required_static_tolerance,
                                          static_tolerance_bound)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "research/results/growth_reliability_fresh_2026-09-19_v1"
STATIC_TOLERANCES = (.02, .05, .10)
EXPONENT_BUDGET = .02


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def analyse(observations: list[dict], archived_fits: list[dict]) -> tuple[list[dict], list[dict]]:
    """Use the archived all-treatment, all-tie shared mask; never select by outcome."""
    lookup = {}
    for row in observations:
        key = (float(row["composition"]), int(row["factor"]), int(row["origin"]),
               row["id"], int(row["sweep"]), row["stage"], int(row["tie_seed"]))
        if key in lookup:
            raise ValueError("Duplicate archived observation")
        lookup[key] = row
    fits = {}
    for row in archived_fits:
        if row["observable"] != "half":
            continue
        key = (float(row["composition"]), int(row["factor"]), int(row["origin"]), row["stage"])
        if key in fits:
            raise ValueError("Duplicate archived fit")
        fits[key] = row
    expected_keys = {(c, factor, origin, stage) for c in (.5, .15)
                     for factor in (2, 4, 8) for origin in range(4)
                     for stage in ("integrated", "fixed", "matched")}
    if set(fits) != expected_keys:
        raise ValueError("Expected all 72 archived half-height comparisons")
    results, histories = [], []
    for composition in (.5, .15):
        ids = sorted({r["id"] for r in observations if float(r["composition"]) == composition})
        if len(ids) != 8:
            raise ValueError("The frozen fresh cohort requires eight trajectories per composition")
        for factor in (2, 4, 8):
            for origin in range(4):
                group = [r for r in observations if float(r["composition"]) == composition
                         and int(r["factor"]) == factor and int(r["origin"]) == origin]
                times = np.asarray(sorted({int(r["sweep"]) for r in group}), dtype=float)
                if times.size != 24 or times[0] != 1119 or times[-1] != 20000:
                    raise ValueError("Unexpected frozen fresh checkpoint grid")
                if len(group) != len(ids) * len(times) * (3 + len(TIE_SEEDS)):
                    raise ValueError("Missing or extra observations in a declared comparison")
                def array(stage, seed):
                    return np.asarray([[float(lookup[composition, factor, origin, i,
                                                     int(t), stage, seed]["half"])
                                        for t in times] for i in ids])
                values = {stage: array(stage, -1) for stage in ("native", "integrated", "fixed")}
                ties = np.asarray([array("matched", seed) for seed in TIE_SEEDS])
                values["matched"] = ties.mean(axis=0)
                common = np.all(np.isfinite(ties) & (ties > 0), axis=(0, 1))
                for value in values.values():
                    common &= np.all(np.isfinite(value) & (value > 0), axis=0)
                selected_times = times[common]
                for stage in ("integrated", "fixed", "matched"):
                    reference = fits[composition, factor, origin, stage]
                    row = dict(composition=composition, factor=factor, origin=origin, stage=stage,
                               trajectories=len(ids), retained_points=int(common.sum()),
                               available_points=len(times), exponent_budget=EXPONENT_BUDGET)
                    if (common.sum() < 4 or selected_times[-1] / selected_times[0] < 5):
                        row.update(status="unresolved fit: original window convention retained")
                        results.append(row)
                        continue
                    native = values["native"][:, common].mean(axis=0)
                    processed = values[stage][:, common].mean(axis=0)
                    budget = paired_budget(selected_times, native, processed)
                    for field, old_field in (("native_alpha", "native_alpha"),
                                             ("processed_alpha", "alpha"), ("delta", "delta")):
                        if not np.isclose(budget[field], float(reference[old_field]), rtol=0, atol=1e-11):
                            raise ArithmeticError("Replayed slope differs from the frozen fit table")
                    row.update(status="resolved", **budget,
                               paired_low=float(reference["low"]), paired_high=float(reference["high"]),
                               archived_interval_label=reference["tolerance_label"],
                               required_common_static_tolerance=required_static_tolerance(selected_times, EXPONENT_BUDGET),
                               point_shift_within_budget=abs(budget["delta"]) <= EXPONENT_BUDGET)
                    for tolerance in STATIC_TOLERANCES:
                        label = int(100 * tolerance)
                        row[f"static_{label}percent_all_times"] = (
                            budget["max_relative_length_change"] <= tolerance + 1e-14)
                        row[f"static_{label}percent_worst_slope_shift"] = static_tolerance_bound(selected_times, tolerance)
                    results.append(row)
                    for t, a, b in zip(selected_times, native, processed, strict=True):
                        histories.append(dict(composition=composition, factor=factor, origin=origin,
                                              stage=stage, sweep=int(t), native_length=float(a),
                                              processed_length=float(b), ratio=float(b / a)))
    return results, histories


def write_rows(path: Path, rows: list[dict]) -> None:
    names = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)


def run(cohort: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Choose a new result directory; frozen evidence is not overwritten")
    manifest = json.loads((cohort / "manifest.json").read_bytes())
    inputs = {name: sha(cohort / name) for name in ("observations.csv", "fits.csv")}
    if any(manifest["outputs"][name] != value for name, value in inputs.items()):
        raise ValueError("Archived input table does not match its recorded hash")
    results, histories = analyse(read_rows(cohort / "observations.csv"), read_rows(cohort / "fits.csv"))
    primary = [r for r in results if r["factor"] == 4 and r["origin"] == 0 and r["stage"] == "matched"]
    if len(results) != 72 or len(primary) != 2:
        raise AssertionError("Unexpected comparison counts")
    static_summary = []
    for tolerance in STATIC_TOLERANCES:
        key = f"static_{int(tolerance * 100)}percent_all_times"
        selected = [r for r in results if r.get(key)]
        static_summary.append(dict(
            relative_length_tolerance=tolerance, related_comparisons=len(results),
            comparisons_with_every_ensemble_mean_ratio_inside=len(selected),
            point_shifts_over_002=sum(not r["point_shift_within_budget"] for r in selected),
            archived_intervals_outside_002=sum(r["archived_interval_label"] == "outside" for r in selected),
        ))
    output.mkdir(parents=True)
    write_rows(output / "comparisons.csv", results)
    write_rows(output / "ensemble_histories.csv", histories)
    times = sorted({r["sweep"] for r in histories if r["factor"] == 4 and r["origin"] == 0 and r["stage"] == "matched"})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.1), layout="constrained")
    for c in (.5, .15):
        group = [r for r in histories if r["composition"] == c and r["factor"] == 4
                 and r["origin"] == 0 and r["stage"] == "matched"]
        axes[0].plot([r["sweep"] for r in group], [r["ratio"] for r in group], label=f"Species fraction {c:g}")
    axes[0].set(xscale="log", xlabel="Post-quench sweeps", ylabel="Processed / native ensemble mean length",
                title="Known factor-four fraction-matched result")
    axes[0].axhline(1, color="black", linestyle=":", linewidth=1)
    axes[0].legend(fontsize=8)
    tolerances = np.linspace(0, .1, 201)
    axes[1].plot(100 * tolerances, [static_tolerance_bound(times, e) for e in tolerances])
    epsilon = required_static_tolerance(times, EXPONENT_BUDGET)
    axes[1].axhline(EXPONENT_BUDGET, color="black", linestyle=":", label="Illustrative exponent budget 0.02")
    axes[1].axvline(100 * epsilon, color="grey", linestyle="--", label=f"Sufficient length tolerance {100 * epsilon:.2f}%")
    axes[1].set(xlabel="Maximum per-time relative length difference (%)",
                ylabel="Worst possible absolute slope difference", title="Fixed-grid OLS box bound, not a new law")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.grid(alpha=.2)
    fig.savefig(output / "error_budget.png", dpi=170)
    plt.close(fig)
    primary_html = "".join(
        f'<tr><td>{r["composition"]:g}</td><td>{r["native_alpha"]:.5f}</td>'
        f'<td>{r["processed_alpha"]:.5f}</td><td>{r["delta"]:+.5f}</td>'
        f'<td>[{r["paired_low"]:+.5f}, {r["paired_high"]:+.5f}]</td></tr>' for r in primary)
    document = dict(
        created_utc=datetime.now(timezone.utc).isoformat(), related_comparisons=len(results),
        primary=primary, static_summary=static_summary,
        primary_time_grid=dict(points=len(times), first=times[0], last=times[-1],
            sufficient_common_relative_tolerance_for_002=epsilon,
            worst_slope_shift_if_every_length_within_5percent=static_tolerance_bound(times, .05),
            worst_slope_shift_if_every_length_within_10percent=static_tolerance_bound(times, .1)),
        max_slope_identity_error=max(r["identity_error"] for r in results if r["status"] == "resolved"),
        interpretation=("Post-hoc diagnostic on known trajectories, not an independent holdout; ordinary "
                        "regression error propagation; same snapshots, no new simulations; native is an "
                        "operational reference, not physical truth. Bounds assume every retained ratio "
                        "lies in its declared interval, not sparse checkpoint coverage or a universal pixel rule."),
    )
    (output / "summary.json").write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Static agreement and growth fits</title><style>body{{font:16px/1.6 system-ui;color:#183039;max-width:1000px;margin:30px auto;padding:0 20px}}h1{{line-height:1.2}}img{{width:100%}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #ddd}}.note{{background:#fff1d9;padding:15px}}</style>
<h1>Does a static length tolerance protect a growth fit?</h1><p>AI-assisted supporting analysis, 15 October 2026. Student review pending.</p>
<p class="note">Known-data replay, not a new holdout or experimental ageing validation. The primary fraction-matching question and original results are unchanged. Severe resolution loss remains a limitation. The regression identity and interval bound are elementary mathematics, not a novelty claim.</p>
<p>A constant scale error changes lengths but not a fitted exponent. A ratio that changes with time can change it. For the declared fit grid, merely keeping every length within 5% allows a worst-case slope shift of {static_tolerance_bound(times, .05):.4f}. To guarantee a shift no larger than 0.02 under this conservative box assumption, every retained ratio must be within approximately {epsilon * 100:.2f}%. These illustrative tolerances are not lab standards.</p>
<img src="error_budget.png" alt="Known length-ratio drift and worst-case OLS error budget">
<p><b>Observed qualification:</b> among all 72 related comparisons, four actually stayed within 5% at every retained time, and eight stayed within 10%. None of those had a point exponent shift above 0.02. The worst-case bound therefore permits a failure that these qualifying observed cases did not exhibit. It is not an observed experimental or Kawasaki counterexample at those tolerances.</p>
<h2>Unchanged primary comparison</h2><table><tr><th>Species fraction</th><th>Native exponent</th><th>Matched exponent</th><th>Difference</th><th>Archived paired 95% interval</th></tr>{primary_html}</table>
<p>Sixteen trajectories in total, eight per composition; 24 common times, 1,119-20,000 sweeps. Five tie priorities are averaged inside each trajectory/time. The analysis replays all 72 related half-height comparisons, including smaller effects, without treating them as 72 independent experiments.</p>
<h2>What this adds, and what it does not</h2><p>The bound translates a declared static difference into a possible fit difference on a specified time grid. It is sufficient, not necessary: constant bias can violate the static tolerance yet leave the exponent unchanged. The extremal ratio sequence need not be realisable by image processing. This is not a predictor of unseen masks, proof of adequate resolution, total measurement uncertainty, or a way to recover the theoretical one third.</p>
<p><a href="comparisons.csv">All 72 comparisons</a> · <a href="ensemble_histories.csv">All paired ensemble histories</a> · <a href="summary.json">Counts and limits</a> · <a href="manifest.json">Input and source hashes</a></p></html>'''
    (output / "report.html").write_text(html)
    sources = ("research/audit_kinetic_error_budget.py", "research/kinetic_error_budget.py",
               "research/fraction_matching.py", "research/KINETIC_ERROR_BUDGET_PROTOCOL_2026-10-15.md")
    record = dict(input_tables_sha256=inputs, input_manifest_sha256=sha(cohort / "manifest.json"),
                  source_sha256={name: sha(ROOT / name) for name in sources},
                  output_sha256={name: sha(output / name) for name in
                                 ("comparisons.csv", "ensemble_histories.csv", "summary.json", "report.html", "error_budget.png")},
                  numpy_version=np.__version__, role="post-hoc supporting analysis of known frozen cohort")
    (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    return dict(comparisons=len(results), primary_time_grid=document["primary_time_grid"],
                static_summary=static_summary, max_slope_identity_error=document["max_slope_identity_error"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.cohort, args.output), indent=2))
