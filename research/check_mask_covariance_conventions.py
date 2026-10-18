"""Check finite-field covariance conventions using separately counted pairs.

This is a bounded verification companion, not a new estimator, a PoreSpy run,
or the full Ledesma-Alonso multi-descriptor baseline. All fields are the known
synthetic fixtures. Nothing changes the production audit or frozen results.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path

import numpy as np

from research.mask_metrology import binary_correlations
from research.verify_mask_resolution_audit import synthetic_cases


def direct_conventions(mask: np.ndarray) -> dict:
    """Count all valid directional pairs; centre by the finite global mean.

    Integer numerators avoid subtracting close floating-point probabilities.
    The two conventions differ because finite-lag marginals can differ from p.
    """
    mask = np.asarray(mask)
    if mask.ndim != 2 or mask.dtype != bool or min(mask.shape) < 4:
        raise ValueError("Need a Boolean 2D field with at least four pixels per axis")
    total, count = int(mask.size), int(np.count_nonzero(mask))
    shape = (2, min(mask.shape) // 2 + 1)
    centred = np.full(shape, np.nan)
    homogeneous = np.full(shape, np.nan)
    correction = np.full(shape, np.nan)
    probability = np.zeros(shape)
    marginals = np.zeros((*shape, 2))
    for direction, axis in enumerate((1, 0)):
        for lag in range(shape[1]):
            left_slices, right_slices = [slice(None)] * 2, [slice(None)] * 2
            left_slices[axis] = slice(0, mask.shape[axis] - lag)
            right_slices[axis] = slice(lag, None)
            left, right = mask[tuple(left_slices)], mask[tuple(right_slices)]
            pairs = int(left.size)
            both = int(np.count_nonzero(left & right))
            marginal_count = int(np.count_nonzero(left)) + int(np.count_nonzero(right))
            probability[direction, lag] = both / pairs
            marginals[direction, lag] = (np.count_nonzero(left) / pairs,
                                         np.count_nonzero(right) / pairs)
            if count in (0, total):
                continue
            denominator = pairs * count * (total - count)
            centred[direction, lag] = (
                total * total * both - total * count * marginal_count
                + pairs * count * count) / denominator
            homogeneous[direction, lag] = (
                total * total * both - pairs * count * count) / denominator
            correction[direction, lag] = (
                2 * pairs * count * count - total * count * marginal_count) / denominator
    return dict(phase_fraction=count / total, centred=centred,
                homogeneous=homogeneous, correction=correction,
                probability=probability, marginals=marginals)


def direct_reduce(mask: np.ndarray, factor: int, ties_to_foreground: bool) -> np.ndarray:
    """Explicit block counts, without the production averaging helper."""
    if (isinstance(factor, bool) or not isinstance(factor, int) or factor < 1
            or any(size % factor for size in mask.shape)
            or min(mask.shape) // factor < 4):
        raise ValueError("Factor must divide the field and retain at least four pixels per axis")
    observed = np.zeros(tuple(size // factor for size in mask.shape), dtype=bool)
    for iy in range(observed.shape[0]):
        for ix in range(observed.shape[1]):
            count = int(np.count_nonzero(mask[iy * factor:(iy + 1) * factor,
                                              ix * factor:(ix + 1) * factor]))
            observed[iy, ix] = (2 * count >= factor * factor if ties_to_foreground
                               else 2 * count > factor * factor)
    return observed


def direct_crossing(values: np.ndarray) -> float:
    for index in range(len(values) - 1):
        a, b = values[index:index + 2]
        if np.isfinite(a) and np.isfinite(b) and a >= .5 > b:
            return float(index + (a - .5) / (a - b))
    return float("nan")


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Choose a new output directory; preserve earlier checks")
    rows, maximum_error, maximum_identity = [], 0., 0.
    cases = synthetic_cases()
    for name, mask in cases.items():
        for factor in (1, 2, 4):
            for tie in (False, True):
                reduced = direct_reduce(mask, factor, tie)
                for complement in (False, True):
                    observed = ~reduced if complement else reduced
                    reference = direct_conventions(observed)
                    actual, _ = binary_correlations(observed)
                    np.testing.assert_allclose(actual, reference["centred"],
                                               atol=1e-12, rtol=0, equal_nan=True)
                    np.testing.assert_allclose(reference["centred"],
                                               reference["homogeneous"] + reference["correction"],
                                               atol=1e-12, rtol=0, equal_nan=True)
                    for direction, label in enumerate(("x", "y")):
                        valid = np.isfinite(actual[direction])
                        error = (float(np.max(np.abs(actual[direction, valid]
                                                    - reference["centred"][direction, valid])))
                                 if np.any(valid) else None)
                        identity = (float(np.max(np.abs(reference["centred"][direction, valid]
                            - reference["homogeneous"][direction, valid]
                            - reference["correction"][direction, valid]))) if np.any(valid) else None)
                        maximum_error = max(maximum_error, error or 0.)
                        maximum_identity = max(maximum_identity, identity or 0.)
                        centred_length = direct_crossing(reference["centred"][direction])
                        conventional_length = direct_crossing(reference["homogeneous"][direction])
                        rows.append(dict(case=name, factor=factor,
                            tie_rule="foreground" if tie else "background",
                            phase_label="complement" if complement else "original",
                            direction=label, phase_fraction=reference["phase_fraction"],
                            lags=len(actual[direction]), maximum_kernel_error=error,
                            maximum_convention_difference=(float(np.max(np.abs(
                                reference["correction"][direction, valid]))) if np.any(valid) else None),
                            centred_half_height=(float(centred_length * factor)
                                                 if np.isfinite(centred_length) else None),
                            homogeneous_half_height=(float(conventional_length * factor)
                                                      if np.isfinite(conventional_length) else None),
                            centred_crossing_status="resolved" if np.isfinite(centred_length) else "unresolved",
                            interpretation="Known synthetic convention comparison, not independent material data"))
    summary = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        synthetic_fields=len(cases), directional_checks=len(rows),
        mask_comparisons=len(rows) // 2,
        maximum_absolute_kernel_error=maximum_error,
        maximum_identity_residual=maximum_identity,
        interpretation="Internal AI-assisted convention check; not physical validation, external review, PoreSpy execution or full published-method reproduction",
        production_changed=False, sources_sha256={
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (
                Path(__file__), Path(__file__).with_name("mask_metrology.py"),
                Path(__file__).with_name("imaging.py"),
                Path(__file__).with_name("verify_mask_resolution_audit.py"))})
    output.mkdir(parents=True)
    with (output / "all_cases.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    body = "".join("<tr>" + "".join(f"<td>{escape(str(row[key]) if row[key] is not None else 'unresolved')}</td>" for key in
        ("case", "factor", "tie_rule", "phase_label", "direction", "maximum_kernel_error",
         "centred_half_height", "homogeneous_half_height", "centred_crossing_status")) + "</tr>" for row in rows)
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Checking the measurement conventions</title>
<style>body{{font:16px/1.5 system-ui;max-width:1100px;margin:36px auto;padding:0 20px;color:#172c35}}
table{{border-collapse:collapse;font-size:12px}}th,td{{padding:7px;border:1px solid #ccd6d8;text-align:left}}
.scroll{{overflow:auto}}.note{{background:#edf3f3;padding:16px}}</style>
<h1>Same pixels, different measurement conventions</h1>
<p class="note">AI-assisted internal synthetic check. Not materials data, outside review,
a PoreSpy execution, or the full published multi-descriptor baseline.</p>
<p><b>{len(rows)} directional checks</b> on {len(cases)} known synthetic fields;
maximum disagreement with independent centred pair counting:
<b>{maximum_error:.3g}</b>. All planned fields and failed crossings are retained.</p>
<h2>What this adds</h2><p>A fair comparison must match centring, boundaries,
directions and the length rule. On a finite field, subtracting the global
fraction squared from a pair probability is not generally the same as
correlating a globally centred image: the lag-specific endpoint means differ.
The exact finite-marginal correction reconciles the two calculations.</p>
<p>This is established algebra, not a new algorithm. A difference between
unmatched conventions is not evidence that a competing tool is inaccurate.
The production audit and all frozen simulation results are unchanged.</p>
<h2>Complete convention comparison</h2><p>Lengths use original synthetic pixel
units. None is physical ground truth. Opposite labels and tie conventions are
paired checks, not extra independent samples. Missing crossings remain unresolved.</p>
<div class="scroll"><table><thead><tr><th>Field</th><th>Factor</th><th>Tie rule</th>
<th>Phase</th><th>Axis</th><th>Kernel error</th><th>Centred length</th>
<th>Homogeneous-form length</th><th>Centred status</th></tr></thead><tbody>{body}</tbody></table></div>
<p><a href="all_cases.csv">All-case CSV</a> | <a href="summary.json">Check summary and source hashes</a></p>
</html>"""
    (output / "report.html").write_text(html)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output), indent=2))
