"""Render every declared main-extension result as a neutral review appendix.

Requires the completed 128-file campaign, production analysis and passing
independent table audit. It changes no number, fit, interval or selection.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from research.imaging_benchmark import sha


WINDOWS = ((1_000, 20_000), (1_000, 200_000), (20_000, 200_000),
           (20_000, 1_000_000), (200_000, 1_000_000))
METHODS = ("primary_unfiltered", "ell_over_L_below_0.15_sensitivity")
TABLES = ("fit_windows.csv", "ensemble_lengths.csv", "matched_size_ratios.csv")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def number(value: str, digits: int = 4) -> str:
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{converted:.{digits}f}" if math.isfinite(converted) else "—"


def check_inputs(campaign: Path, analysis: Path) -> tuple[list[dict], list[dict], list[dict], dict]:
    status = json.loads((campaign / "status.json").read_text())
    if status.get("state") != "complete" or status.get("completed") != 128:
        raise ValueError("The entire 128-file campaign must be complete")
    audit_path = analysis / "independent_table_audit.json"
    independent = json.loads(audit_path.read_text())
    if (independent.get("raw_files_checked") != 128
            or independent.get("fit_rows_checked") != 80
            or independent.get("audit_source_sha256") != sha(Path(__file__).with_name("audit_main_extension.py"))
            or independent.get("campaign_manifest_sha256") != sha(campaign / "manifest.json")
            or independent.get("analysis_manifest_sha256") != sha(analysis / "manifest.json")):
        raise ValueError("Independent table audit is absent, stale or incomplete")
    if independent.get("analysis_table_sha256") != {
            name: sha(analysis / name) for name in TABLES}:
        raise ValueError("An analysis table changed after the independent audit")
    provenance = json.loads((analysis / "manifest.json").read_text())
    expected_raw = provenance.get("input_sha256", {})
    actual_raw = {path.name: path for path in campaign.glob("*.npz")}
    if len(expected_raw) != 128 or set(actual_raw) != set(expected_raw):
        raise ValueError("Raw campaign inventory changed after the independent audit")
    for name, recorded_hash in expected_raw.items():
        if sha(actual_raw[name]) != recorded_hash:
            raise ValueError(f"Raw trajectory changed after the independent audit: {name}")

    fits, ensemble, matched = (read_rows(analysis / name) for name in TABLES)
    expected = {(c, side, lo, hi, method)
                for c in (0.5, 0.15) for side in (32, 64, 96, 128)
                for lo, hi in WINDOWS for method in METHODS}
    actual = [(float(row["composition"]), int(row["L"]),
               int(row["nominal_t_min"]), int(row["nominal_t_max"]), row["method"])
              for row in fits]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Fit appendix requires all 80 unique declared rows")
    if len({tuple(row.items()) for row in fits}) != len(fits):
        raise ValueError("Duplicate fit rows")
    return fits, ensemble, matched, independent


def render(fits: list[dict], ensemble: list[dict], matched: list[dict]) -> str:
    lines = [
        "# Complete 0.65 Tc extension: neutral results appendix", "",
        "AI-assisted table rendering from the completed, independently audited analysis.",
        "This appendix reports **all five fixed windows**, both compositions, all four",
        "lattice widths, and both declared fit methods. It contains no post-hoc",
        "choice of an asymptotic regime or finite-size onset. The measured exponent",
        "is an effective log–log slope of the ensemble-mean connected-correlation",
        "half-height length, not a physical alloy ageing rate.", "",
        "Each group has 16 independent seeded trajectories to 1,000,000 attempted-",
        "exchange sweeps at isotropic Jx=Jy=1 and 0.65 times the exact 2D",
        "equilibrium critical temperature. Checkpoints within one trajectory",
        "are repeated observations, not independent samples. Percentile",
        "intervals resample whole trajectories 500 times and are conditional on",
        "the observable, model and predeclared mask. An unresolved fit remains",
        "unresolved; it is never replaced by zero or a shorter selected window.",
        "",
    ]
    for method, title in (
        (METHODS[0], "Primary: no length-fraction filter"),
        (METHODS[1], "Sensitivity only: mean length/L below 0.15"),
    ):
        lines.extend((f"## {title}", "",
                      "| +1 fraction | L | Nominal sweeps | Actual sweeps | Points | α | 95% replica interval | Max ℓ/L in fit |",
                      "|---:|---:|---:|---:|---:|---:|---:|---:|"))
        for c in (0.5, 0.15):
            for side in (32, 64, 96, 128):
                for lo, hi in WINDOWS:
                    row = next(item for item in fits
                               if (float(item["composition"]), int(item["L"]),
                                   int(item["nominal_t_min"]), int(item["nominal_t_max"]),
                                   item["method"]) == (c, side, lo, hi, method))
                    actual = (f'{row["used_t_min"]}–{row["used_t_max"]}'
                              if row["used_t_min"] and row["used_t_max"] else "unresolved")
                    interval = (f'{number(row["bootstrap_low"])}–{number(row["bootstrap_high"])}'
                                if math.isfinite(float(row["bootstrap_low"]))
                                and math.isfinite(float(row["bootstrap_high"])) else "unresolved")
                    lines.append(f'| {c:.2f} | {side} | {lo}–{hi} | {actual} | '
                                 f'{row["n_points"]} | {number(row["alpha"])} | {interval} | '
                                 f'{number(row["max_length_over_L"])} |')
        lines.append("")

    lines.extend(("## Missing measurements and matched-size coverage", "",
                  "The full [ensemble table](../ensemble_lengths.csv) retains every",
                  "checkpoint, including unresolved directional lengths. This count",
                  "summarises how many *group checkpoints* had both directions resolved",
                  "in every one of the 16 trajectories; it is not a count of independent",
                  "observations.", "",
                  "| +1 fraction | L | All checkpoints | Jointly resolved | Unresolved |",
                  "|---:|---:|---:|---:|---:|"))
    for c in (0.5, 0.15):
        for side in (32, 64, 96, 128):
            group = [row for row in ensemble
                     if float(row["composition"]) == c and int(row["L"]) == side]
            resolved = sum(row["resolved_all"] == "True" for row in group)
            lines.append(f"| {c:.2f} | {side} | {len(group)} | {resolved} | {len(group)-resolved} |")
    lines.extend(("", "The [matched-size table](../matched_size_ratios.csv) retains every",
                  "predeclared checkpoint for L=32, 64 and 96 relative to L=128",
                  "at the **same sweep count**. L=128 is itself finite; neither a",
                  "ratio below one nor a percentile interval excluding one defines",
                  "a physical onset time.", "",
                  "| +1 fraction | L / 128 | All matched times | Jointly resolved | Unresolved |",
                  "|---:|---:|---:|---:|---:|"))
    for c in (0.5, 0.15):
        for side in (32, 64, 96):
            group = [row for row in matched
                     if float(row["composition"]) == c and int(row["L"]) == side]
            resolved = sum(row["status"] == "resolved" for row in group)
            lines.append(f"| {c:.2f} | {side} / 128 | {len(group)} | {resolved} | {len(group)-resolved} |")
    lines.extend(("", "Read the [original fit table](../fit_windows.csv), the",
                  "[independent arithmetic audit](../independent_table_audit.json),",
                  "the frozen protocol and the images before selecting a claim.",
                  "No row alone proves one-third growth, explains a finite-size",
                  "mechanism, or calibrates the simulation to a material.", ""))
    return "\n".join(lines)


def write_appendix(campaign: Path, analysis: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new appendix output directory")
    if output.parent.resolve() != analysis.resolve():
        raise ValueError("Put the appendix inside the audited analysis directory")
    fits, ensemble, matched, independent = check_inputs(campaign, analysis)
    output.mkdir(parents=True)
    report = output / "APPENDIX.md"
    report.write_text(render(fits, ensemble, matched))
    (output / "provenance.json").write_text(json.dumps(dict(
        status="presentation only; all declared rows, no new statistical analysis",
        source_sha256=sha(Path(__file__)),
        independent_table_audit_sha256=sha(analysis / "independent_table_audit.json"),
        analysis_table_sha256=independent["analysis_table_sha256"],
        appendix_sha256=sha(report),
    ), indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(write_appendix(arguments.campaign, arguments.analysis, arguments.output))
