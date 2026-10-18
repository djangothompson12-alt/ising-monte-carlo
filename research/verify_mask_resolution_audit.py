"""Reproduce internal numerical checks of the supplied-mask audit.

The reference independently forms integer centred pixel-pair products,
calculates exact rational covariances, and interpolates the half-height
crossing with rational arithmetic. It shares no averaging, covariance or
crossing function with the audit. These checks validate a specified discrete
calculation on synthetic masks, not segmentation or physical accuracy.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np

from research.mask_resolution_audit import SOURCE_FILES, measure


def reference_measure(mask: np.ndarray, factor: int, pixel_size: float,
                      ties_to_foreground: bool) -> dict:
    """Slow exact reference for small Boolean test fields; no FFT or audit helpers."""
    mask = np.asarray(mask)
    if mask.ndim != 2 or mask.dtype != bool or min(mask.shape) < 4:
        raise ValueError("Need a small 2D Boolean test mask")
    if (isinstance(factor, bool) or not isinstance(factor, int) or factor < 1
            or any(n % factor for n in mask.shape) or min(mask.shape) // factor < 4):
        raise ValueError("Factor must divide both axes and retain at least four pixels")
    if mask.size > 4096:
        raise ValueError("Exact reference is bounded to 4096 native pixels")
    if not np.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError("Positive finite pixel spacing required")
    height, width = mask.shape
    counts = []
    for y in range(0, height, factor):
        counts.append([sum(bool(value) for value in mask[y:y + factor, x:x + factor].ravel())
                       for x in range(0, width, factor)])
    counts = np.asarray(counts, dtype=np.int64)
    observed = (2 * counts >= factor * factor if ties_to_foreground
                else 2 * counts > factor * factor)
    total = int(observed.size)
    foreground = int(np.count_nonzero(observed))
    lengths = []
    if foreground in (0, total):
        lengths = [float("nan"), float("nan")]
    else:
        centred = observed.astype(np.int64) * total - foreground
        # The variance of the integer-scaled centred indicator is k*(N-k).
        variance = foreground * (total - foreground)
        for axis in (1, 0):
            correlations = []
            for lag in range(min(observed.shape) // 2 + 1):
                if axis == 1:
                    left, right = centred[:, :observed.shape[1] - lag], centred[:, lag:]
                else:
                    left, right = centred[:observed.shape[0] - lag, :], centred[lag:, :]
                products = sum(int(a) * int(b)
                               for a, b in zip(left.ravel(), right.ravel(), strict=True))
                correlations.append(Fraction(products, int(left.size) * variance))
            crossing = float("nan")
            for index, (left, right) in enumerate(zip(correlations, correlations[1:])):
                if left >= Fraction(1, 2) > right:
                    crossing = float(index + (left - Fraction(1, 2)) / (left - right))
                    break
            lengths.append(crossing * pixel_size * factor)
    return dict(length_x=lengths[0], length_y=lengths[1],
                length=float(np.mean(lengths)),
                phase_fraction=foreground / total,
                tie_block_fraction=float(np.mean(2 * counts == factor * factor)),
                resolved=bool(np.all(np.isfinite(lengths))))


def synthetic_cases() -> dict[str, np.ndarray]:
    y, x = np.indices((16, 16))
    stripe = (x // 4) % 2 == 1
    exact_half = stripe.copy()
    exact_half[4:] = np.roll(exact_half[4:], 1, axis=1)
    cy, cx = np.indices((32, 32))
    circles = ((cx - 9) ** 2 + (cy - 11) ** 2 <= 6 ** 2) | ((cx - 23) ** 2 + (cy - 22) ** 2 <= 5 ** 2)
    ay, ax = np.indices((24, 32))
    rare = np.zeros((16, 16), dtype=bool)
    rare[4, 11] = True
    rng = np.random.default_rng(20261013)
    return dict(empty=np.zeros((16, 16), dtype=bool),
                full=np.ones((16, 16), dtype=bool),
                single_pixel_checkerboard=(x + y) % 2 == 1,
                two_pixel_checkerboard=(x // 2 + y // 2) % 2 == 1,
                four_pixel_checkerboard=(x // 4 + y // 4) % 2 == 1,
                horizontal_stripes=stripe.T.copy(), vertical_stripes=stripe,
                diagonal_stripes=((x + y) // 4) % 2 == 1,
                two_circles=circles, circles_complement=~circles,
                anisotropic_checkerboard=(ax // 8 + ay // 4) % 2 == 1,
                one_foreground_pixel=rare, one_background_pixel=~rare,
                exact_half_lag=exact_half,
                random_15=rng.random((16, 16)) < .15,
                random_50=rng.random((16, 16)) < .5,
                random_85=rng.random((16, 16)) < .85,
                rectangular_random=rng.random((24, 20)) < .5)


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Choose a new validation directory")
    cases = synthetic_cases()
    rows = []
    maximum_error = 0.0
    for name, mask in cases.items():
        for factor in (1, 2, 4):
            for tie_rule in (False, True):
                for spacing in (.06, 1.05, 2.35):
                    expected = reference_measure(mask, factor, spacing, tie_rule)
                    actual = measure(mask, factor, spacing, tie_rule)
                    errors = []
                    for key in ("length", "length_x", "length_y", "phase_fraction", "tie_block_fraction"):
                        value, reference = actual[key], expected[key]
                        if np.isnan(reference):
                            if not np.isnan(value):
                                raise AssertionError(f"{name}/{factor}/{key}: unresolved reference lost")
                        else:
                            error = abs(value - reference)
                            if error > 1e-11 * max(1.0, abs(reference)):
                                raise AssertionError(f"{name}/{factor}/{key}: {value} != {reference}")
                            errors.append(error)
                    if (actual["status"] == "resolved") != expected["resolved"]:
                        raise AssertionError(f"{name}/{factor}: resolution status disagrees")
                    error = max(errors, default=0.0)
                    maximum_error = max(maximum_error, error)
                    rows.append(dict(case=name, native_shape=list(mask.shape), factor=factor,
                                     tie_rule="foreground" if tie_rule else "background",
                                     pixel_spacing=spacing, status=actual["status"],
                                     maximum_absolute_error=error))
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  synthetic_fields=len(cases), measurement_comparisons=len(rows),
                  maximum_absolute_error=maximum_error, checks=rows,
                  reference="Independent integer centred-pair products, rational covariances and rational crossing",
                  interpretation="Internal AI-assisted synthetic calculation verification; not external validation",
                  numpy_version=np.__version__,
                  source_sha256={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                 for name in ("verify_mask_resolution_audit.py", *SOURCE_FILES)})
    output.mkdir(parents=True)
    (output / "verification.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return {key: result[key] for key in ("synthetic_fields", "measurement_comparisons", "maximum_absolute_error")}


def exhaustive_four_by_four(output: Path) -> dict:
    """Check every possible 4x4 Boolean field against the rational reference.

    Four pixels is the smallest retained axis accepted by the length kernel.
    This verifies all 65,536 fields of that shape, not all larger images or
    a meaningful physical resolution. Single-direction failures are retained.
    """
    if output.exists():
        raise FileExistsError("Choose a new exhaustive-check directory")
    maximum = 0.0
    outcomes = dict(both_resolved=0, x_only=0, y_only=0, neither_resolved=0)
    phase_counts = [0] * 17
    digest = hashlib.sha256()
    for code in range(1 << 16):
        mask = ((code >> np.arange(16)) & 1).astype(bool).reshape(4, 4)
        expected = reference_measure(mask, 1, 1.0, False)
        actual = measure(mask, 1, 1.0, False)
        for key in ("length", "length_x", "length_y", "phase_fraction"):
            a, b = actual[key], expected[key]
            if np.isnan(b):
                if not np.isnan(a):
                    raise AssertionError(f"Mask {code}: {key} lost unresolved status")
            else:
                error = abs(a - b)
                maximum = max(maximum, error)
                if error > 1e-12:
                    raise AssertionError(f"Mask {code}: {key}: {a} != {b}")
        x_ok, y_ok = np.isfinite(expected["length_x"]), np.isfinite(expected["length_y"])
        outcome = ("both_resolved" if x_ok and y_ok else "x_only" if x_ok
                   else "y_only" if y_ok else "neither_resolved")
        outcomes[outcome] += 1
        phase_counts[int(mask.sum())] += 1
        compact = [code, outcome] + [None if not np.isfinite(expected[key]) else expected[key]
                                    for key in ("length_x", "length_y")]
        digest.update((json.dumps(compact, separators=(",", ":"), allow_nan=False) + "\n").encode())
        if (code + 1) % 8192 == 0:
            print(f"Exact small-mask comparisons: {code + 1}/65536", flush=True)
    result = dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        shape=[4, 4], binary_fields=1 << 16, exhaustive_for_this_shape=True,
        maximum_absolute_error=maximum, resolution_outcomes=outcomes,
        fields_by_foreground_count=phase_counts, reference_results_sha256=digest.hexdigest(),
        reference="Exact integer centred-pair products and rational crossing, no production helpers",
        interpretation="Exhaustive discrete-kernel verification at the smallest shape, not physical accuracy or larger-field exhaustiveness",
        source_sha256={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                       for name in ("verify_mask_resolution_audit.py", *SOURCE_FILES)},
    )
    output.mkdir(parents=True)
    (output / "verification.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--exhaustive-four-by-four", action="store_true")
    arguments = parser.parse_args()
    runner = exhaustive_four_by_four if arguments.exhaustive_four_by_four else run
    print(json.dumps(runner(arguments.output), indent=2))
