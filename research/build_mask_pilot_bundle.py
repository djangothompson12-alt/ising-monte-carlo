"""Build a small local review copy of the static audit, never publish or contact anyone.

An explicit allowlist excludes real masks, raw microscopy, private planning,
outreach and campaign archives. The included inputs are newly generated
synthetic circles and an empty field, visibly labelled as such.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from research.make_mask_resolution_demo import make


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "LICENSE", "requirements-mask-audit.txt", "research/__init__.py",
    "research/mask_resolution_audit.py", "research/mask_audit_io.py",
    "research/mask_metrology.py", "research/imaging.py", "research/metrology.py",
    "research/make_mask_resolution_demo.py", "research/verify_mask_resolution_audit.py",
    "research/verify_mask_audit_delivery.py", "research/mask_resolution_audit.template.json",
    "research/build_mask_pilot_bundle.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Choose a new bundle directory; do not overwrite review evidence")
    digests = {name: sha(ROOT / name) for name in SOURCES}
    contents = output / "contents"
    contents.mkdir(parents=True)
    for name in SOURCES:
        target = contents / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    make(contents / "synthetic_demo")
    readme = """# A small, local phase-mask resolution audit

AI-assisted research prototype, prepared 15 October 2026 for technical
criticism. Student approval, outside use and physical validation are not
established. This folder contains no original microscopy images or private
planning. The example masks are artificial circles and an empty field.

## One specific job

On an already approved binary 2D mask, compare a finite directional
correlation half-height length before and after direct 2x/4x block reduction.
Keep the same declared rectangular field, propagate square-pixel spacing,
and retain missing crossings and under-resolution warnings. The declared
exact-tie rule stays primary; the opposite rule is also reported. If the
image owner has not set a useful tolerance beforehand, no acceptance
classification is made. Native-mask agreement is not physical accuracy.

This is not raw-image segmentation, an instrument-resolution simulation,
a particle-radius measurement, an ageing-law fit, alloy-property prediction
or chemical-composition conservation test. Phase area fraction is geometry,
not generally chemical composition.

## Try without supplying any image

From this unzipped folder, using Python 3.11 (tested):

    python3.11 -m venv .venv
    .venv/bin/python -m pip install -r requirements-mask-audit.txt
    .venv/bin/python -m research.make_mask_resolution_demo --output my-demo

On Windows use the environment's Scripts/python.exe instead. Open
my-demo/audit/report.html. synthetic_demo/audit/report.html is a ready-made
example.
It retains the empty-field failures. There is no web server or account.
Only NumPy, SciPy and Pillow are needed; no plotting, Numba or web UI stack.
The inherited dependency floors are not a compatibility certificate for all
versions; exact runtime versions are recorded in generated manifests.

## Verify the calculation and local delivery

    .venv/bin/python -m research.verify_mask_resolution_audit --output my-check
    .venv/bin/python -m research.verify_mask_audit_delivery my-demo/audit --input-plan my-demo/input_plan.json --require-current-sources

The first command compares 324 measurements with separately implemented
integer-pair/rational arithmetic. For a slower exhaustive check of all
65,536 4x4 masks, add --exhaustive-four-by-four and use a new output folder.
That is exhaustive for this smallest shape only, not physical validation.
Delivery hashes detect changes relative to a manifest, not forgery or truth.
Replay uses the same implementation and needs original local masks.

## An owner-led pilot

Copy research/mask_resolution_audit.template.json to a private folder and
declare actual labels, source/rights, mask authority, calibration, material,
ROI and intended decision. No ROI is silently trimmed; each axis must be at
least 16 pixels and divisible by four. TIFF stacks must be explicitly reduced
to one selected plane; non-square pixels need a different estimator.
Choose mean_length or both_directions and any justified tolerance before
examining results. Then run:

    .venv/bin/python -m research.mask_resolution_audit /path/to/private-plan.json --output my-pilot

No supplied image is uploaded. The HTML/CSV omit pixels and input paths but
retain specimen IDs and descriptions, so obtain permission before sharing.
The program refuses to overwrite any result directory.

## The criticism requested

Would this exact native-versus-reduced measurement help a decision in your
workflow, duplicate existing checks, or risk a misleading interpretation?
Which feature, reference or tolerance would make one small pilot informative?
An unhelpful or failed test is a result to record, not hide.

Code, test scaffolding, analysis and this text received substantial Codex AI
assistance. No student hours or expert approval are inferred from this bundle.
The research project is https://github.com/djangothompson12-alt/ising-monte-carlo .
This is a local versioned copy, not a claim the latest changes are on GitHub.
"""
    (contents / "README.md").write_text(readme)
    if digests != {name: sha(ROOT / name) for name in SOURCES}:
        raise RuntimeError("Source changed during bundle preparation")
    inventory = {p.relative_to(contents).as_posix(): sha(p)
                 for p in sorted(contents.rglob("*")) if p.is_file()}
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256=digests, members_sha256=inventory,
                    excluded="Real masks and micrographs, private planning/outreach, simulations, credentials",
                    status="Local AI-assisted review copy; student approval pending; not distributed")
    (contents / "BUNDLE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = output / "mask-audit-pilot.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(contents.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(contents).as_posix())
    return dict(archive=str(archive), bytes=archive.stat().st_size,
                archive_sha256=sha(archive), members=len(inventory) + 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))
