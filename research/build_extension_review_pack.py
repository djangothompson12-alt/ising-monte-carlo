"""Build a private, hash-checked review copy of the completed 0.65 Tc study.

This is a reproducibility handoff, not a public release, endorsement, paper,
or validation against an alloy. It never changes an archived trajectory.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

from research.audit_archived_observables import audit_campaign
from research.confirm_image_operator_extension import validate_complete
from research.imaging_benchmark import sha
from research.render_extension_appendix import check_inputs
from research.verify_study import verify


ROOT = Path(__file__).resolve().parents[1]
MAIN = Path("research/runs/main_065_multisize_v1")
ANALYSIS = MAIN / "analysis_declared_v1"
HOLDOUT = MAIN / "image_holdout_v1"
PRIOR = (Path("research/runs/overnight"),
         Path("research/runs/imaging_validation"))
FROZEN = Path("research/frozen_sources/2026-09-10")
CORE_PACKAGES = ("numpy", "numba", "scipy", "matplotlib", "Pillow")
REVIEW_DOCS = (
    "ALGE_REAL_IMAGE_AUDIT_2026-09-18.md",
    "APPLIED_IMAGE_AUDIT.md",
    "ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md",
    "BINNING_DECOMPOSITION_RESULTS_2026-09-17.md",
    "EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md",
    "EXTERNAL_DATASET_SCOUT_2026-09-17.md",
    "EXTERNAL_USE_DECISION_2026-09-17.md",
    "FECR_MATERIALS_CASE_STUDY_2026-09-18.md",
    "FIVE_WORKSTREAMS_STATUS_2026-09-13.md",
    "INITIAL_LENGTH_SENSITIVITY_2026-09-17.md",
    "MASK_RESOLUTION_AUDIT.md",
    "MASK_AUDIT_PILOT_RECORD.template.md",
    "METALDAM_CLEANUP_SENSITIVITY_2026-09-17.md",
    "METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md",
    "METALDAM_STATIC_PILOT_2026-09-17.md",
    "PAIRED_WINDOW_AUDIT_2026-09-18.md",
    "PAPER_EVIDENCE_GUIDE.md",
    "PARTNER_PILOT_PROTOCOL_2026-09-17.md",
    "PHYSICAL_MEASUREMENTS.md",
    "REFERENCE_RUN_INTEGRITY_2026-09-17.md",
    "REGULAR_SOLUTION_BINODAL_2026-09-18.md",
    "REVIEW_RESPONSE_LOG.template.md",
    "SMALL_LATTICE_EQUILIBRIUM_CHECK_2026-09-17.md",
    "START_HERE.md",
    "STUDENT_DEFENCE_2026-09-18.md",
    "SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _raw_hashes(folder: Path) -> dict[str, str]:
    return {path.name: sha(path) for path in sorted(folder.glob("*.npz"))}


def verify_extension_evidence(root: Path = ROOT) -> dict:
    """Refuse a packet if the raw run or any added analysis is stale."""
    campaign = root / MAIN
    analysis = root / ANALYSIS
    holdout = root / HOLDOUT
    validate_complete(campaign)
    primary = verify(campaign, root)
    if primary["replicas"] != 128 or primary["snapshots"] != 9600:
        raise ValueError("The complete 128-run archive did not verify")
    for prior in PRIOR:
        verify(root / prior, root / FROZEN)

    saved_observable_audit = _read_json(campaign / "observable_audit_v1.json")
    fresh_observable_audit = audit_campaign(campaign)
    for key in ("manifest_sha256", "replicas", "snapshots_checked",
                "directional_lengths_checked", "unresolved_saved",
                "unresolved_recomputed", "threshold_rounding_ambiguities"):
        if saved_observable_audit.get(key) != fresh_observable_audit[key]:
            raise ValueError(f"Observable audit is stale: {key}")
    if (fresh_observable_audit["snapshots_checked"] != 9600
            or fresh_observable_audit["directional_lengths_checked"] != 19200):
        raise ValueError("Not every archived observable was checked")

    replay = _read_json(campaign / "first_interval_replay_v1.json")
    raw = _raw_hashes(campaign)
    if (replay.get("status") != "passed" or replay.get("replicas") != 128
            or replay.get("raw_npz_sha256") != raw
            or replay.get("source_sha256") != sha(root / "research/replay_first_energy_interval.py")
            or replay.get("engine_sha256") != sha(root / "model_b/kawasaki_engine.py")):
        raise ValueError("First-interval replay is stale or incomplete")

    fits, ensemble, matched, independent = check_inputs(campaign, analysis)
    if (len(fits), len(ensemble), len(matched)) != (80, 600, 450):
        raise ValueError("Declared result-table inventory is incomplete")
    appendix = analysis / "appendix_v1"
    appendix_provenance = _read_json(appendix / "provenance.json")
    if (appendix_provenance.get("source_sha256")
            != sha(root / "research/render_extension_appendix.py")
            or appendix_provenance.get("independent_table_audit_sha256")
            != sha(analysis / "independent_table_audit.json")
            or appendix_provenance.get("appendix_sha256")
            != sha(appendix / "APPENDIX.md")):
        raise ValueError("All-row appendix changed after rendering")

    holdout_meta = _read_json(holdout / "manifest.json")
    expected_holdout_files = {name: digest for name, digest in raw.items()
                              if name.startswith(("c0_L128_", "c1_L128_"))}
    source_hashes = holdout_meta.get("source_sha256", {})
    if (holdout_meta.get("campaign_manifest_sha256") != sha(campaign / "manifest.json")
            or holdout_meta.get("campaign_status_sha256") != sha(campaign / "status.json")
            or holdout_meta.get("input_sha256") != expected_holdout_files
            or holdout_meta.get("prior_manifest_sha256") != {
                str(root / prior): sha(root / prior / "manifest.json") for prior in PRIOR}
            or source_hashes != {
                relative: sha(root / relative) for relative in source_hashes}
            or source_hashes.get("research/confirm_image_operator_extension.py")
            != sha(root / "research/confirm_image_operator_extension.py")
            or source_hashes.get("research/PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md")
            != sha(root / "research/PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md")):
        raise ValueError("New-seed image holdout provenance is stale")
    with (holdout / "paired_fits.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    actual_rows = {(float(row["composition"]), int(row["nominal_t_min"]),
                    int(row["nominal_t_max"])) for row in rows}
    if len(rows) != 4 or actual_rows != {
            (c, lo, hi) for c in (0.5, 0.15)
            for lo, hi in ((1000, 20000), (1000, 200000))}:
        raise ValueError("Holdout does not contain exactly four fixed fit rows")
    with (holdout / "per_replica_checkpoint.csv").open(newline="") as stream:
        if sum(1 for _ in stream) != 2401:
            raise ValueError("Holdout must retain all 2,400 saved-state rows")
    for name in ("REPORT.md", "holdout_delta_alpha.png"):
        if not (holdout / name).is_file():
            raise ValueError(f"Holdout display is missing: {name}")

    return dict(campaign=primary, independent_fit_rows=independent["fit_rows_checked"],
                independent_matched_rows=independent["matched_size_rows_checked"],
                observable_directions=fresh_observable_audit["directional_lengths_checked"],
                threshold_rounding_ambiguities=fresh_observable_audit[
                    "threshold_rounding_ambiguities"],
                first_intervals_replayed=replay["replicas"],
                holdout_replicas=32, holdout_rows=2400)


def selected_files(root: Path = ROOT) -> list[Path]:
    """Deliberate source/data inventory: no private outreach or third-party TIFFs."""
    individual = [
        "README.md", "CLAUDE.md", "EXTERNAL_REVIEW.md", "LICENSE", "CITATION.cff",
        "requirements.txt", "AI_USE_AND_CONTRIBUTIONS.md",
        "model_a/ising_engine.py", "model_b/kawasaki_engine.py",
        "phase_diagram.py", "comparative_analysis.py",
        "manuscript/main.tex", "manuscript/WRITING_GUIDE.md",
        "manuscript/REPORT_DRAFT_2026-09-18.md",
        "experiments/PROTOCOL.md",
        "model_a/figures/fig1_phase_transitions_corrected.png",
        "model_a/figures/fig2_spin_domains.png",
        "model_a/figures/fig3_kinetics_entropy.png",
        "docs/CLAIM_AUDIT_2026-09-17.md",
        "docs/PROGRESS_AND_LIMITS.md", "docs/review_brief.html",
        "docs/LITERATURE_COMPARISON_2026-09-17.md",
        "docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md",
        "docs/SECOND_ASSISTANT_AUDIT_TASK.md",
        "docs/TECHNICAL_REPORT_BACKBONE.md",
        "docs/MEASUREMENT_STUDY_RESULTS.md",
        "docs/OVERNIGHT_RESULTS.md",
    ]
    individual += [f"docs/{name}" for name in REVIEW_DOCS]
    paths = [root / name for name in individual]
    paths += list((root / "research").glob("*.py"))
    paths += list((root / "research").glob("*.md"))
    paths += list((root / "research/plans").glob("*.json"))
    paths += list((root / FROZEN).rglob("*.py"))
    paths += list((root / "figures").glob("*.png"))
    paths += list((root / "figures").glob("*.json"))
    paths += list((root / "research/results").rglob("*"))
    for test in ("test_audit_archived_observables.py",
                 "test_audit_main_extension.py",
                 "test_build_extension_review_pack.py",
                 "test_confirm_image_operator_extension.py",
                 "test_main_extension_matched_sizes.py",
                 "test_make_mask_resolution_demo.py",
                 "test_mask_resolution_audit.py",
                 "test_verify_review_copy.py"):
        paths.append(root / "tests" / test)
    for campaign in (*PRIOR, MAIN):
        paths += list((root / campaign).rglob("*"))
    paths = sorted({path for path in paths if path.is_file()})
    missing = [name for name in individual if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required review files: {missing}")
    for path in paths:
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Review file escapes repository: {path}")
    return paths


def _review_readme() -> str:
    return """# Private 0.65 Tc Kawasaki review copy

This is an **AI-assisted, unpublished technical review copy**, not Django's
finished paper, a peer-reviewed result, an endorsement, or a validated
alloy predictor. It includes the full 128-run extension, the two earlier
simulation ensembles used for the new-seed image comparison, frozen sources
for those earlier ensembles, declared analyses, all unresolved rows and a
record of AI assistance. No third-party microscopy TIFFs or private outreach
notes are included. The full-repository README mentions a historical PDF,
but that stale PDF is intentionally omitted from this review copy. Check
`MANIFEST.json` before treating any file as evidence.
Some preserved analysis manifests contain the creator's local filesystem
paths. Inspect those and the attributed, derived public Al–Ge figures before
sharing this **private** copy outside the project. No source tomography TIFF
or third-party steel photograph is bundled.

Start with `docs/SECOND_ASSISTANT_AUDIT_TASK.md` for an adversarial audit,
or `research/MAIN_EXTENSION_PROTOCOL.md` and its matched-size addendum for
the declared physics test. Only after that, inspect the all-row table at
`research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md`,
the separate image holdout at
`research/runs/main_065_multisize_v1/image_holdout_v1/REPORT.md`, and the
AI-assisted `manuscript/REPORT_DRAFT_2026-09-18.md`.

The nominal 200,000–1,000,000-sweep fits are **unresolved** by the fixed
factor-of-five time-span rule. Do not quietly change that rule or call the
broader 20,000–1,000,000 slopes asymptotic. The holdout is a selected-effect
directional repeat, not a blind first discovery; block thresholding also
changes apparent phase fraction. All runs are model sweeps and lattice sites,
not hours, nanometres or real-alloy strength predictions.

## Reproduce with Python 3.11

The analysis environment used to build this copy is in
`environment_versions.json`; `requirements-core.txt` pins its core packages
for convenience, not a guarantee of cross-platform binary compatibility.
Before analysis, check the unpacked file inventory, then use a fresh writable
output folder. The integrity check cannot tell whether a scientific claim is
right; it only detects missing or changed files:

```bash
python -m research.verify_review_copy .
python -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
mkdir -p .mplconfig .numba_cache_review reproduced
MPLCONFIGDIR=.mplconfig .venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m research.verify_study research/runs/main_065_multisize_v1 --source-root .
.venv/bin/python -m research.audit_archived_observables research/runs/main_065_multisize_v1 --output reproduced/observable_audit.json
NUMBA_CACHE_DIR=.numba_cache_review .venv/bin/python -m research.replay_first_energy_interval research/runs/main_065_multisize_v1 --source-root . --output reproduced/first_interval.json
MPLCONFIGDIR=.mplconfig .venv/bin/python -m research.analyse_main_extension research/runs/main_065_multisize_v1 --output reproduced/analysis
.venv/bin/python -m research.audit_main_extension research/runs/main_065_multisize_v1 reproduced/analysis --output reproduced/analysis/independent_table_audit.json
.venv/bin/python -m research.render_extension_appendix research/runs/main_065_multisize_v1 reproduced/analysis --output reproduced/analysis/appendix_v1
MPLCONFIGDIR=.mplconfig .venv/bin/python -m research.confirm_image_operator_extension research/runs/main_065_multisize_v1 --output reproduced/image_holdout
```

Each writer refuses to overwrite an existing output path. The image holdout
uses the included earlier two cohorts only to reject overlapping seeds;
its output has its own method and raw-file hashes. To verify the older
cohorts, use `research.verify_study` with
`--source-root research/frozen_sources/2026-09-10`.

The results are reproducible computational measurements, **not** an
experimental validation. Please report concrete errors, missing assumptions
and ambiguous claims rather than a generic endorsement.

To inspect the separate, bounded mask-resolution tool without real data,
run `.venv/bin/python -m research.make_mask_resolution_demo --output
reproduced/synthetic-mask-demo` from this copy. One drawn field resolves and
one empty field correctly remains unresolved; neither is alloy evidence.
"""


def check_core_links(folder: Path) -> int:
    """Catch missing local targets in the handoff's primary reading route."""
    documents = (
        "README.md", "EXTERNAL_REVIEW.md", "docs/PROGRESS_AND_LIMITS.md",
        "docs/START_HERE.md", "docs/review_brief.html",
    )
    checked = 0
    for name in documents:
        document = folder / name
        body = document.read_text()
        targets = re.findall(r"\]\(([^)]+)\)", body)
        targets += re.findall(r'(?:href|src)="([^"]+)"', body)
        for target in targets:
            url = urlsplit(target)
            if url.scheme or target.startswith("#"):
                continue
            relative = unquote(url.path)
            if not relative:
                continue
            # The old tracked PDF is deliberately excluded from this package.
            if name == "README.md" and relative == "manuscript/main.pdf":
                continue
            if not (document.parent / relative).exists():
                raise FileNotFoundError(f"Broken review link: {name} -> {target}")
            checked += 1
    return checked


def build(output: Path) -> dict:
    output = output.resolve()
    private_root = (ROOT / "output").resolve()
    if output.parent != private_root:
        raise ValueError("Review copies must be direct children of ignored output/")
    archive = output.with_suffix(".zip")
    if output.exists() or archive.exists():
        raise FileExistsError("Choose a new review-copy name")
    evidence = verify_extension_evidence(ROOT)
    files = selected_files(ROOT)
    output.mkdir(parents=True)
    for source in files:
        destination = output / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    linked_targets_checked = check_core_links(output)
    environment = dict(python=platform.python_version(),
                       packages={name: importlib.metadata.version(name)
                                 for name in CORE_PACKAGES},
                       note="Provenance of the pack builder; see the original campaign manifest for run-time versions.")
    (output / "environment_versions.json").write_text(json.dumps(environment, indent=2) + "\n")
    (output / "requirements-core.txt").write_text("\n".join(
        f"{name}=={version}" for name, version in environment["packages"].items()) + "\n")
    (output / "REVIEW_ME_FIRST.md").write_text(_review_readme())
    (output / "BUILD_CONTEXT.json").write_text(json.dumps(dict(
        built_utc=datetime.now(timezone.utc).isoformat(),
        git_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                             cwd=ROOT, text=True).strip(),
        warning="The base commit does not contain all uncommitted files in this reviewed, hash-listed copy.",
        verification=evidence,
        local_link_targets_checked=linked_targets_checked,
    ), indent=2) + "\n")
    inventory = {str(path.relative_to(output)): sha(path)
                 for path in sorted(output.rglob("*")) if path.is_file()}
    (output / "MANIFEST.json").write_text(json.dumps(dict(
        built_utc=datetime.now(timezone.utc).isoformat(),
        files=inventory,
        boundary="private AI-assisted review copy; not a publication or external validation",
    ), indent=2) + "\n")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as zipped:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(output))
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise RuntimeError("Review archive failed its CRC check")
        for name, digest in inventory.items():
            from hashlib import sha256
            if sha256(zipped.read(name)).hexdigest() != digest:
                raise RuntimeError(f"Review archive hash mismatch: {name}")
    (archive.with_suffix(".zip.sha256")).write_text(
        f"{sha(archive)}  {archive.name}\n")
    return dict(folder=str(output), archive=str(archive),
                files=len(inventory) + 1, bytes=archive.stat().st_size,
                verification=evidence)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(build(arguments.output), indent=2))
