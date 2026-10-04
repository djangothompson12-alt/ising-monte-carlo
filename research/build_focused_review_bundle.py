"""Build a small, private evidence copy for the fresh fraction-matching test.

Only allowlisted simulation data and their source dependency graph are copied.
The original campaign manifest is never edited: its git-status text is omitted
from a labelled derivative, preserving the numerical identity and raw hashes.
Nothing is published, sent, simulated or represented as student-approved.
"""

from __future__ import annotations

import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = Path("research/runs/growth_reliability_holdout_v1")
FRESH = Path("research/results/growth_reliability_fresh_2026-09-19_v1")
FREEZE = Path("research/results/growth_reliability_freeze_2026-09-19_v1.json")
CORRECTION = Path("research/results/fresh_arithmetic_audit_2026-09-20_v1/verification.json")
PACKAGES = ("numpy", "scipy", "numba", "matplotlib", "Pillow")
CONTEXT_FILES = {
    "research/runs/main_065_multisize_v1/analysis_declared_v1/fit_windows.csv",
    *{f"output/{folder}/{name}" for folder in (
        "fem_mask_audit_2026-09-22_v2",
        "fem_mask_audit_2026-09-22_tie_foreground_sensitivity_v1")
      for name in ("field_summary.csv", "audit/measurements.csv", "audit/manifest.json")},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def safe_relative(name: str) -> Path:
    path = Path(name)
    if not name or path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"Unsafe relative path: {name!r}")
    return path


def source_graph(root: Path, names: set[str]) -> list[Path]:
    """Include transitive project imports, not a broad source-folder copy."""
    pending = [safe_relative(name) for name in names]
    seen = set()
    while pending:
        relative = pending.pop()
        if relative in seen:
            continue
        path = root / relative
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise FileNotFoundError(f"Missing/unsafe source: {relative}")
        seen.add(relative)
        if path.suffix != ".py":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.level:
                    raise ValueError(f"Relative import needs explicit handling: {relative}")
                modules.append(node.module)
                modules.extend(f"{node.module}.{alias.name}" for alias in node.names)
            for module in modules:
                if module.split(".")[0] not in {"research", "model_b"}:
                    continue
                base = Path(*module.split("."))
                for candidate in (base.with_suffix(".py"), base / "__init__.py"):
                    if (root / candidate).is_file():
                        pending.append(candidate)
    return sorted(seen)


def redact_campaign_manifest(original: dict) -> tuple[dict, dict]:
    """The campaign's numerical identity is kept exactly, private filenames are not."""
    derived = dict(original)
    removed = [key for key in ("git_status",) if key in derived]
    for key in removed:
        del derived[key]
    derived["portable_copy_note"] = (
        "Derived manifest: git_status omitted to avoid disclosing private-note "
        "filenames. Numerical identity is unchanged. This file is NOT byte-identical "
        "to the original manifest cited by the frozen analysis."
    )
    record = {"removed_fields": removed, "numerical_identity_unchanged":
              derived["identity"] == original["identity"],
              "original_manifest_included": False,
              "original_manifest_retained_in_local_workspace": True}
    return derived, record


def checked_inputs(root: Path) -> dict:
    freeze = read_json(root / FREEZE)
    analysis = read_json(root / FRESH / "manifest.json")
    original = read_json(root / CAMPAIGN / "manifest.json")
    status = read_json(root / CAMPAIGN / "status.json")
    if (status.get("state"), status.get("completed"), status.get("total")) != ("complete", 16, 16):
        raise ValueError("Fresh campaign is not complete")
    plan = original["identity"]["plan"]
    if (plan["sizes"], plan["concentrations"], plan["replicas"],
            plan["max_sweeps"], plan["Jx"], plan["Jy"], plan["T_final_over_tc"]) != (
            [128], [.5, .15], 8, 20000, 1, 1, .65):
        raise ValueError("Unexpected primary campaign conditions")
    if analysis["sources"] != freeze["sources"]:
        raise ValueError("Analysis sources disagree with the pre-generation freeze")
    for name, expected in freeze["sources"].items():
        if sha(root / safe_relative(name)) != expected:
            raise ValueError(f"Frozen source changed: {name}")
    if sha(root / FREEZE) != analysis["freeze_sha256"]:
        raise ValueError("Frozen protocol/seed manifest identity changed")
    if sha(root / CAMPAIGN / "manifest.json") != analysis["campaign_manifest_sha256"]:
        raise ValueError("Original campaign-manifest identity changed")
    expected = {f"c{ci}_L128_rep{rep:03d}.npz" for ci in range(2) for rep in range(8)}
    if set(analysis["input_sha256"]) != expected:
        raise ValueError("Analysis does not cover exactly the 16 declared trajectories")
    if {p.name for p in (root / CAMPAIGN).glob("*.npz")} != expected:
        raise ValueError("Raw campaign inventory changed")
    for name, expected_hash in analysis["input_sha256"].items():
        if sha(root / CAMPAIGN / name) != expected_hash:
            raise ValueError(f"Raw trajectory changed: {name}")
    for name, expected_hash in analysis["outputs"].items():
        if sha(root / FRESH / safe_relative(name)) != expected_hash:
            raise ValueError(f"Frozen output changed: {name}")
    correction = read_json(root / CORRECTION)
    if correction["analysis_manifest_sha256"] != sha(root / FRESH / "manifest.json"):
        raise ValueError("Correction audit is for a different analysis")
    if correction["audit_source_sha256"] != sha(root / "research/audit_fresh_measurements.py"):
        raise ValueError("Correction-audit source changed")
    return {"frozen": freeze, "analysis": analysis, "campaign": original,
            "correction": correction}


def _copy(root: Path, relative: Path, output: Path) -> None:
    source = root / relative
    if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
        raise FileNotFoundError(f"Missing/unsafe selected file: {relative}")
    target = output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def copy_context(root: Path, output: Path, pdf_record: dict) -> dict:
    """Copy only explicitly allowed context tables, not microscopy pixels."""
    expected = pdf_record.get("context", {}).get("sources", {})
    if not expected:
        return {"included": False}
    if set(expected) != CONTEXT_FILES:
        raise ValueError("PDF contextual inventory differs from the allowlist")
    for name, digest in expected.items():
        path = safe_relative(name)
        if sha(root / path) != digest:
            raise ValueError(f"PDF contextual evidence changed: {name}")
        _copy(root, path, output)
    chord = Path("research/results/chord_observation_sensitivity_2026-09-26_v2")
    manifest = read_json(root / chord / "manifest.json")
    if manifest.get("status") != "complete" or manifest.get("unchanged_verified") is not True:
        raise ValueError("Chord appendix lacks completed status")
    for name in ("summary.json", "contrasts.csv"):
        if sha(root / chord / name) != manifest["outputs"][name]:
            raise ValueError(f"Chord appendix changed: {name}")
        _copy(root, chord / name, output)
    _copy(root, chord / "manifest.json", output)
    _copy(root, Path("research/build_fraction_matching_brief.py"), output)
    text = '''# Context supporting the October brief

These contextual results are separate from the 16 fresh primary trajectories.
Do not pool their sample sizes or interpret their measurements as equivalent.

## Longer simulations

The [complete declared fit table](research/runs/main_065_multisize_v1/analysis_declared_v1/fit_windows.csv)
includes all sizes, compositions, windows and unresolved fits from the separate
128-trajectory million-sweep study. The cited rows have L=128,
method=primary_unfiltered and nominal window 20000-1000000; actual retained
times are 21336-1000000. These use the periodic engine length, not the
finite-image statistic in the primary experiment. This compact package does
not contain the 128 raw trajectories or reproduce their simulation analysis.
The separate 40-run 0.6 Tc campaign is not included or represented as a
completed literature-method replication.

## Materials-image audit

The [primary FeM summary](output/fem_mask_audit_2026-09-22_v2/field_summary.csv)
and [field measurements](output/fem_mask_audit_2026-09-22_v2/audit/measurements.csv)
cover all 81 fields from one mounted specimen. The
[post-hoc opposite-tie summary](output/fem_mask_audit_2026-09-22_tie_foreground_sensitivity_v1/field_summary.csv)
and [field measurements](output/fem_mask_audit_2026-09-22_tie_foreground_sensitivity_v1/audit/measurements.csv)
change only the treatment of exactly balanced blocks. Both audit manifests
retain the original measurement hashes. The PDF builder independently
recomputes the cited medians from those field rows. This is not a new
pixel-level recalculation or an independent-specimen study.

Source: [Gomes et al., FeM v1](https://doi.org/10.5281/zenodo.5014700).
Microscopy pixels are excluded; their redistribution terms have not been
established. Producer masks are treated as references, not physical truth.
Small length changes are not a laboratory pass without an owner-defined
tolerance. Digital downsampling is not an independently acquired microscope
image. No external user has approved or adopted this tool.

## Exploratory chord appendix

The [summary](research/results/chord_observation_sensitivity_2026-09-26_v2/summary.json)
and [all contrasts](research/results/chord_observation_sensitivity_2026-09-26_v2/contrasts.csv)
reuse the same known 16 trajectories. Processing shifts were smaller for
complete foreground chords than half-height lengths. Edge-censored chords
are excluded, so these are not the published periodic all-domain measurement.
This is exploratory support, not a second untouched confirmation cohort.

## Rebuilding the PDF

The included `research/build_fraction_matching_brief.py` reads the packaged
primary data and context tables. With numpy, Pillow, reportlab and pypdf
installed, run it from the unpacked package:

```bash
python -B -m research.build_fraction_matching_brief --root . --output ../rebuilt_review_brief.pdf
```

Choose an unused output name. The original PDF and its provenance remain
unchanged. Rebuilding reproduces the selected numbers and illustrations, not
independent scientific validation or student approval of its AI-assisted prose.
'''
    (output / "CONTEXT.md").write_text(text)
    return {"included": True, "sources": expected,
            "boundary": "Aggregate long-run and static-mask context; no raw third-party images"}


def local_links(folder: Path) -> dict:
    """Check the deliberately small navigation surface, not text inside source code."""
    checked = 0
    pages = [Path("README.md"), FRESH / "report.html"]
    if (folder / "CONTEXT.md").is_file():
        pages.append(Path("CONTEXT.md"))
    for relative in pages:
        page = folder / relative
        source = page.read_text()
        targets = (re.findall(r"\]\(([^)]+)\)", source) if page.suffix == ".md"
                   else re.findall(r'(?:href|src)=[\"\']([^\"\']+)[\"\']', source))
        for target in targets:
            if target.startswith(("https:", "http:", "mailto:", "#")):
                continue
            path = (page.parent / target.split("#")[0]).resolve()
            if not path.is_relative_to(folder.resolve()) or not path.is_file():
                raise ValueError(f"Broken/nonportable link in {relative}: {target}")
            checked += 1
    return {"status": "passed", "local_links_checked": checked,
            "scope": "Generated README, optional context navigation and frozen fresh-run HTML report"}


def compare_replay(original: Path, replay: Path) -> dict:
    """Compare all fits numerically without pretending roundoff is byte identity."""
    with (original / "fits.csv").open(newline="") as stream:
        old = list(csv.DictReader(stream))
    with (replay / "fits.csv").open(newline="") as stream:
        new = list(csv.DictReader(stream))
    if len(old) != len(new) or not old:
        raise ValueError("Replayed fit inventory differs")
    maximum = 0.
    for row, (a, b) in enumerate(zip(old, new)):
        if a.keys() != b.keys():
            raise ValueError("Replayed fit fields differ")
        for key in a:
            if a[key] == b[key]:
                continue
            try:
                x, y = float(a[key]), float(b[key])
            except ValueError as error:
                raise ValueError(f"Replayed label differs at row {row}: {key}") from error
            if math.isnan(x) and math.isnan(y):
                continue
            if not math.isfinite(x) or not math.isfinite(y) or abs(x-y) > 1e-12:
                raise ValueError(f"Replayed value differs at row {row}: {key}")
            maximum = max(maximum, abs(x-y))
    if sha(original / "observations.csv") != sha(replay / "observations.csv"):
        raise ValueError("Replayed observations are not byte-identical in this tested environment")
    return {"status": "passed_numeric", "fit_rows_checked": len(old),
            "maximum_absolute_fit_field_difference": maximum,
            "absolute_comparison_tolerance": 1e-12,
            "observations_byte_identical": True,
            "fits_byte_identical": sha(original / "fits.csv") == sha(replay / "fits.csv"),
            "original_fit_sha256": sha(original / "fits.csv"),
            "replayed_fit_sha256": sha(replay / "fits.csv"),
            "replayed_observations_sha256": sha(replay / "observations.csv"),
            "replayed_manifest_sha256": sha(replay / "manifest.json"),
            "scope": "Frozen sources reanalysed saved data in an unzipped copy; no new simulation or independent data"}


def _readme(root: Path, has_pdf: bool, has_primary_audit: bool = False,
            has_context: bool = False) -> str:
    with (root / FRESH / "fits.csv").open(newline="") as stream:
        primary = [r for r in csv.DictReader(stream) if
                   (r["factor"], r["origin"], r["observable"], r["stage"]) ==
                   ("4", "0", "half", "matched")]
    if len(primary) != 2:
        raise ValueError("Missing primary comparisons")
    rows = "\n".join(
        f'| {float(r["composition"]):.2f} | {float(r["native_alpha"]):.5f} | '
        f'{float(r["alpha"]):.5f} | {float(r["delta"]):.5f} '
        f'[{float(r["low"]):.5f}, {float(r["high"]):.5f}] |' for r in primary)
    pdf = "[Two-page reviewer brief](review_brief.pdf).\n\n" if has_pdf else ""
    if has_context:
        pdf += "[Long-run, materials-mask and exploratory chord context](CONTEXT.md).\n\n"
    primary_audit = (
        "- [New separate primary-result recheck](primary_audit/REPORT.md).\n"
        "- [Its exact numbers and input hashes](primary_audit/verification.json).\n"
        if has_primary_audit else "")
    return f'''# Fraction matching: focused evidence copy

**Local working copy. Not approved by the student, published,
submitted, independently reviewed or externally adopted. Substantial AI assistance.**

{pdf}## One question

After reducing image resolution, is preserving the species fraction sufficient
to preserve the measured finite-window coarsening exponent in 2D Kawasaki simulations?
The reference is the native-image exponent, not the theoretical asymptotic 1/3.
This experiment does not identify the entire cause of the native exponent's shortfall.

## Result and scope

Sixteen fresh simulations: eight per composition; 128×128 sites; Jx=Jy=1;
T=0.65 Tc after 200 preparation sweeps at 3 Tc. All simulations are included.
The main comparison uses 4×4 arithmetic block means followed by nearest-count
rank segmentation. Five fixed tie priorities are sensitivity choices, not replicates.
Matching is exact at 50:50 and nearest-integer at 15:85. The same 24 retained
checkpoints span 1,119–20,000 sweeps; the nominal frozen window was 1,000–20,000.
Lengths are finite-image directional connected-covariance half-height crossings,
not the engine's periodic length. Intervals use 1,000 paired whole-run bootstrap draws.

| Nominal +1 species fraction | Native exponent | Fraction-matched exponent | Difference [95% interval] |
|---|---:|---:|---|
{rows}

Matching fraction did not preserve the exponent in this comparison. It helps at
finer resolution, so this is not a claim that fraction matching always fails.
No new growth law, alloy-specific prediction, certified originality or validated
safe-resolution rule is claimed. Phase area fraction in a real alloy image is
not generally its conserved chemical composition.

## Read or check

- [All 144 frozen comparison fits and report]({FRESH}/report.html).
- [All 36,864 retained observations]({FRESH}/observations.csv), including ties.
- [Frozen protocol](research/GROWTH_RELIABILITY_PROTOCOL_2026-09-19.md).
- [Pre-generation source and seed freeze]({FREEZE}).
- [Raw campaign plan](research/plans/growth_reliability_holdout_v1.json).
- [Correction audit and all recalculated fit checks]({CORRECTION}).
- [Scope of the correction](CORRECTIONS.md).
- [Source classification and file hashes](MANIFEST.json).
- [Metadata-redaction record](PROVENANCE_REDACTION.json).
- [Recorded environments](ENVIRONMENT.json).
- [Saved-data reproduction check](REPRODUCTION_CHECK.json).
{primary_audit}

The raw NPZ directory contains exactly 16 independently seeded trajectories.
Each archive stores `t` (post-quench sweeps), `snapshots` (±1 sites), `config`
(actual seed/parameters), conserved `magnetization`, `realized_concentration`,
and periodic engine observables. Checkpoints within a run are not independent.

## Reproduce without rerunning Monte Carlo

Unzip into an empty folder and open a terminal in this folder. Use Python 3.11
in a virtual environment; install the recorded numerical dependencies:

```bash
python -m venv .review-venv
.review-venv/bin/python -m pip install -r requirements-numerical.txt
.review-venv/bin/python -B -m research.verify_review_copy .
.review-venv/bin/python -B -m research.verify_study research/runs/growth_reliability_holdout_v1 --source-root .
.review-venv/bin/python -B -m research.audit_growth_reliability research/runs/growth_reliability_holdout_v1 --cohort fresh --freeze research/results/growth_reliability_freeze_2026-09-19_v1.json --output ../fresh_fraction_replay
```

On Windows use the virtual environment's `Scripts/python.exe`. The analysis
output must be new. Compare its `fits.csv` and `observations.csv` with the frozen
files here. Exact-byte agreement is an environment-specific reproducibility check;
different numerical libraries can change roundoff, especially first-zero decisions.
For an independent arithmetic implementation, optionally run:

```bash
.review-venv/bin/python -B -m research.audit_fresh_measurements research/runs/growth_reliability_holdout_v1 ../fresh_fraction_replay --output ../fresh_direct_pair_audit
```

That audit is expected to report **discrepancies_found**, not a clean pass:
the recorded factor-eight secondary boundary issue is preserved and disclosed.
The primary factor-four result is unchanged. The two predeclared warning
screens accepted zero of 18 comparisons and have no demonstrated usable coverage.
Use the **new reanalysis directory** in that command: its derived campaign-manifest
hash matches this redacted copy. Running the audit directly against the frozen
original output will intentionally reject the changed manifest hash. If included,
`primary_audit/audit_primary.py` is an unchanged record of the additional local
check, not a portable command: it retains its original-path and manifest checks.

## Provenance and privacy

The nine recorded frozen sources, all raw archives and the frozen analysis
tables are byte-identical copies checked against their old hashes. Current
support dependencies and later checking/packaging scripts are identified separately;
they were not all covered by the original nine-file freeze. This copy preserves
the original environment record but does not claim that provenance freeze was complete.

The original campaign manifest included private-note filenames in `git_status`.
That field is omitted here. Its numerical identity is unchanged, but its hash is
different. The untouched frozen analysis manifest still records the original hash;
the redaction record explains this intentional mismatch. New reanalysis should
recover the numeric tables, **not** the original analysis-manifest hash.
Original private notes, third-party microscopy images, raw data from other
campaigns and old paper drafts are not included. If CONTEXT.md is present,
it lists separate aggregate context tables and their limited verification scope.
No simulation source or raw-data file in the working project was altered.

Code, design, analysis, checking and prose have had substantial AI assistance.
This is not evidence that Django independently completed or already understands
every step. Student explanation/approval and specialist criticism remain necessary.
'''


def build(root: Path, output: Path, review_pdf: Path | None = None,
          primary_audit: Path | None = None, replay_output: Path | None = None) -> dict:
    root, output = root.resolve(), output.resolve()
    if output.exists() or output.with_suffix(".zip").exists():
        raise FileExistsError("Choose a new bundle directory and ZIP name")
    evidence = checked_inputs(root)
    if review_pdf is not None and not review_pdf.is_file():
        raise FileNotFoundError(review_pdf)
    pdf_provenance = review_pdf.with_suffix(".provenance.json") if review_pdf else None
    if pdf_provenance and (not pdf_provenance.is_file() or
                           read_json(pdf_provenance)["pdf_sha256"] != sha(review_pdf)):
        raise ValueError("Reviewer PDF provenance missing or inconsistent")
    if primary_audit is not None:
        primary_check = read_json(primary_audit / "verification.json")
        if primary_check.get("status") != "pass_primary_only":
            raise ValueError("Expected a completed, primary-only arithmetic check")
        if (sha(primary_audit / "audit_primary.py") != primary_check["audit_script_sha256"]
                or sha(primary_audit / "primary_measurements.csv") != primary_check["measurement_output_sha256"]):
            raise ValueError("Primary-check source or observations changed")
    frozen = evidence["frozen"]["sources"]
    source_names = set(frozen) | {
        "research/verify_study.py", "research/verify_review_copy.py",
        "research/audit_fresh_measurements.py", "research/build_focused_review_bundle.py"}
    sources = source_graph(root, source_names)
    selected = set(sources) | {FREEZE, CORRECTION, CAMPAIGN / "status.json", Path("LICENSE")}
    selected |= {CAMPAIGN / name for name in evidence["analysis"]["input_sha256"]}
    selected |= {FRESH / name for name in ("observations.csv", "fits.csv", "report.html", "manifest.json")}
    output.mkdir(parents=True)
    for relative in sorted(selected):
        _copy(root, relative, output)
    original_path = root / CAMPAIGN / "manifest.json"
    derived, redaction = redact_campaign_manifest(evidence["campaign"])
    derived_path = output / CAMPAIGN / "manifest.json"
    derived_path.write_text(json.dumps(derived, indent=2) + "\n")
    redaction.update(original_sha256=sha(original_path), derivative_sha256=sha(derived_path),
                     derivative_path=str(CAMPAIGN / "manifest.json"),
                     original_hash_verified_locally_against_frozen_analysis=True,
                     raw_files_and_frozen_sources_unmodified=True)
    (output / "PROVENANCE_REDACTION.json").write_text(json.dumps(redaction, indent=2) + "\n")
    if review_pdf:
        shutil.copyfile(review_pdf, output / "review_brief.pdf")
        shutil.copyfile(pdf_provenance, output / "review_brief.provenance.json")
    context = copy_context(root, output, read_json(pdf_provenance)) if review_pdf else {"included": False}
    if primary_audit:
        (output / "primary_audit").mkdir()
        for name in ("REPORT.md", "verification.json", "primary_measurements.csv", "audit_primary.py"):
            shutil.copyfile(primary_audit / name, output / "primary_audit" / name)
    (output / "README.md").write_text(_readme(root, review_pdf is not None,
                                              primary_audit is not None, context["included"]))
    (output / "CORRECTIONS.md").write_text(
        "# Preserved numerical correction\n\n"
        "The separately coded direct-pair audit checked every one of the 36,864 "
        "retained observations and all 144 fits. It found 37 factor-eight "
        "fraction-matched 50:50 positive-lobe discrepancies at an exact "
        "correlation zero affected by FFT roundoff. Four secondary fits change; "
        "maximum change in their exponent difference is about 0.001841. "
        "The primary factor-four results and all tolerance classifications "
        "are unchanged. Frozen outputs were not replaced.\n\n"
        "The included verification JSON retains status `discrepancies_found`, "
        "original and direct-recomputed values, exact conditional bootstrap "
        "intervals, leave-one-run-out ranges, and every changed secondary fit. "
        "These are internal AI-assisted checks, not independent human review.\n")
    versions = {name: importlib.metadata.version(name) for name in PACKAGES}
    (output / "requirements-numerical.txt").write_text(
        "# Versions used for this local reproduction; Python 3.11.\n" +
        "\n".join(f"{name}=={version}" for name, version in versions.items()) + "\n")
    environment = {"bundle_environment": {"python": platform.python_version(),
                    "platform": platform.platform(), "packages": versions},
                   "generation_environment": {key: evidence["campaign"]["identity"][key]
                                              for key in ("python", "versions")}}
    (output / "ENVIRONMENT.json").write_text(json.dumps(environment, indent=2) + "\n")
    reproduction = (compare_replay(root / FRESH, replay_output) if replay_output
                    else {"status": "not_run", "scope": "No replay result supplied to this bundle build"})
    (output / "REPRODUCTION_CHECK.json").write_text(json.dumps(reproduction, indent=2) + "\n")
    # README refers to MANIFEST; populate once before the link check.
    (output / "MANIFEST.json").write_text("{}\n")
    links = local_links(output)
    inventory = {str(path.relative_to(output)): sha(path) for path in sorted(output.rglob("*"))
                 if path.is_file() and path.name != "MANIFEST.json"}
    (output / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in inventory.items()))
    inventory["SHA256SUMS"] = sha(output / "SHA256SUMS")
    manifest = {"schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "local_copy_student_approval_required", "files": inventory,
                "frozen_sources": dict(frozen),
                "current_support_sources_not_in_original_freeze": {
                    str(path): sha(root / path) for path in sources if str(path) not in frozen},
                "original_campaign_manifest_sha256": sha(original_path),
                "derived_campaign_manifest_sha256": sha(derived_path),
                "local_links": links, "raw_trajectories": 16,
                "context": context,
                "frozen_observation_rows": 36864, "frozen_fit_rows": 144,
                "boundary": "Allowlisted local evidence copy; no external review, publication or validation"}
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    from research.verify_review_copy import verify
    integrity = verify(output)
    zip_path = output.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(path, Path(output.name) / path.relative_to(output))
    return {"output": str(output), "zip": str(zip_path), "zip_bytes": zip_path.stat().st_size,
            "zip_sha256": sha(zip_path), "integrity": integrity, "links": links,
            "student_approval": False, "external_review": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-pdf", type=Path)
    parser.add_argument("--primary-audit", type=Path)
    parser.add_argument("--replay-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(ROOT, args.output, args.review_pdf, args.primary_audit,
                           args.replay_output), indent=2))
