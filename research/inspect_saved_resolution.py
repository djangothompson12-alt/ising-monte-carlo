"""Read-only feasibility check of native resolution in saved trajectories.

No exponent fits, processed images, new simulations or holdout claims. Native
length / proposed block size is a planning proxy, not the measured coarse
length and not a guarantee of accuracy. The screens are explicitly heuristic.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from research.imaging_benchmark import sha
from research.metrology import first_crossing
from research.stable_image_metrology import refined_correlations


def inspect_archive(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as archive:
        config = json.loads(str(archive["config"]))
        times = archive["t"]
        snapshots = archive["snapshots"]
    size = config["L"]
    if (times.ndim != 1 or not len(times) or np.any(np.diff(times) <= 0)
            or not np.all(np.isfinite(times)) or times[0] < 0
            or snapshots.shape != (len(times), size, size)
            or not np.all((snapshots == -1) | (snapshots == 1))):
        raise ValueError(f"Invalid saved trajectory: {path.name}")
    counts = (snapshots == 1).sum(axis=(1, 2))
    if np.any(counts != counts[0]):
        raise ValueError(f"Composition changed: {path.name}")
    if times[-1] != config["max_sweeps"]:
        raise ValueError(f"Incomplete trajectory: {path.name}")
    keep = times >= 1000
    lengths = [[float(first_crossing(axis, .5)) for axis in refined_correlations(s)]
               for s in snapshots[keep]]
    return dict(file=path.name, sha256=sha(path), config=config,
                saved_snapshots=len(times), times=times[keep].tolist(),
                native_directional_lengths=lengths)


def coverage(records: list[dict], factor: int) -> dict:
    """Common checkpoints across all replicas; never silently drop a run."""
    if not records or any(r["times"] != records[0]["times"] for r in records):
        raise ValueError("Need nonempty records with identical checkpoint grids")
    times = np.asarray(records[0]["times"])
    lengths = np.asarray([r["native_directional_lengths"] for r in records])
    if lengths.shape != (len(records), len(times), 2):
        raise ValueError("Need both directional lengths at every checkpoint")
    finite = np.all(np.isfinite(lengths) & (lengths > 0), axis=(0, 2))
    resolution = finite & np.all(lengths / factor >= 3., axis=(0, 2))
    size = records[0]["config"]["L"]
    small = finite & np.all(lengths / size < .15, axis=(0, 2))
    def describe(mask):
        t = times[mask]
        return dict(count=len(t), times=t.tolist(),
                    time_span_ratio=float(t[-1] / t[0]) if len(t) else None)
    return dict(factor=factor, native_resolved=describe(finite),
                native_three_pixel_proxy=describe(resolution),
                proxy_and_directional_size_screen=describe(resolution & small))


def run(folder: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory")
    paths = sorted(folder.glob("*L128*.npz"))
    if not paths:
        raise ValueError("No L128 archives found")
    records = [inspect_archive(p) for p in paths]
    groups = {}
    for record in records:
        c = record["config"]
        key = json.dumps({k: c[k] for k in
                          ("L", "Jx", "Jy", "T_initial", "T_final",
                           "concentration", "max_sweeps", "eq_sweeps_initial")},
                         sort_keys=True)
        groups.setdefault(key, []).append(record)
    summaries = [dict(condition=json.loads(key), trajectories=len(group),
                      factors=[coverage(group, b) for b in (2, 4, 8)])
                 for key, group in groups.items()]
    def clean(value):
        if isinstance(value, float) and not np.isfinite(value):
            return None
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        return value
    document = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        purpose="Post-hoc native-resolution feasibility, not new validation",
        method="Full unshifted saved field; finite nonperiodic covariance half-height; refined decision-boundary arithmetic",
        limits="Native length/block factor is not processed length. Three pixels and each directional length/L < .15 are planning heuristics, not proof of resolution or absence of finite-size effects. No fits or automatic window selection.",
        source_sha256={name: sha(Path(__file__).with_name(name)) for name in
                       ("inspect_saved_resolution.py", "stable_image_metrology.py",
                        "imaging.py", "metrology.py")},
        groups=summaries, records=records)
    output.mkdir(parents=True)
    result = output / "inventory.json"
    result.write_text(json.dumps(clean(document), indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.folder, args.output))
