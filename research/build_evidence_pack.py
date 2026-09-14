"""Assemble a portable PRIVATE writing/review pack; never publish or overwrite.

Includes raw simulation outputs, licensed experimental feasibility slices,
analysis files and a frozen source snapshot. This is not journal acceptance.
"""
import argparse
import csv
import html
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path
from research.imaging_benchmark import sha
from research.verify_study import verify

ROOT=Path(__file__).resolve().parents[1]


def build(output):
    archive=output.with_suffix('.zip')
    if output.exists() or archive.exists():raise FileExistsError('Choose a new pack name')
    audits={name:verify(ROOT/'research/runs'/name) for name in ('overnight','imaging_validation')}
    output.mkdir(parents=True)
    selected=[ROOT/p for p in ('requirements.txt','CITATION.cff','AI_USE_AND_CONTRIBUTIONS.md',
        'model_a/ising_engine.py','model_b/kawasaki_engine.py','model_b/research_export.py','model_b/solara_app.py',
        'phase_diagram.py','experiments/string_lab.py',
        'docs/MEASUREMENT_STUDY_RESULTS.md','docs/PAPER_EVIDENCE_GUIDE.md','docs/OVERNIGHT_RESULTS.md',
        'figures/fig_regular_solution_spinodal.png')]
    selected+=list((ROOT/'research').glob('*.py'))+list((ROOT/'research').glob('*.md'))
    selected+=list((ROOT/'research/plans').glob('*.json'))+list((ROOT/'tests').glob('*.py'))
    selected+=[ROOT/'research/experimental_images.template.json']
    if (ROOT/'LICENSE').exists():selected.append(ROOT/'LICENSE')
    missing=[str(p) for p in selected if not p.is_file()]
    if missing:raise FileNotFoundError(f'Missing required source files: {missing}')
    for path in selected:
        dest=output/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    for name in ('overnight','imaging_validation','experimental_source_audit','alge_feasibility'):
        shutil.copytree(ROOT/'research/runs'/name,output/'research/runs'/name)
    (output/'VERIFICATION.json').write_text(json.dumps(audits,indent=2)+'\n')
    (output/'environment.freeze.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    with (output/'research/runs/imaging_validation/imaging_v1/paired_fits.csv').open() as f:rows=list(csv.DictReader(f))
    shown=[r for r in rows if r['condition'] in ('bin4','blur2','crop32') and r['t_min']=='1000' and r['t_max']=='20000']
    table=''.join('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in (r['c'],r['condition'],
        f'{float(r["delta_vs_full"]):.3f}',f'[{float(r["delta_low"]):.3f}, {float(r["delta_high"]):.3f}]'))+'</tr>' for r in shown)
    panels=[('Long-run growth','research/runs/overnight/analysis/growth_c0.png'),
        ('Different observables on identical trajectories','research/runs/overnight/estimator_analysis_v1/estimators_c0.5_L128.png'),
        ('Controlled observation operators','research/runs/overnight/imaging_v1/operators_c0.15.png'),
        ('Actual simulation size versus observation window','research/runs/overnight/imaging_v1/box_vs_window_c0.15.png'),
        ('Independent seeded repeat','research/runs/imaging_validation/imaging_v1/observation_ratios_c0.15.png'),
        ('Experimental feasibility — not validation','research/runs/alge_feasibility/qa/experimental_feasibility.png')]
    figures=''.join(f'<section><h2>{title}</h2><img src="{path}" alt="{title}"></section>' for title,path in panels)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Coarsening measurement study — evidence pack</title><style>
body{font:17px/1.55 system-ui,sans-serif;color:#192c39;background:#f7f8fa;margin:0}main{max-width:1100px;margin:auto;padding:36px 24px}
h1{font-size:34px;line-height:1.15}h2{font-size:23px}section{background:white;padding:22px;margin:24px 0;border:1px solid #d5dee3;border-radius:8px}
img{display:block;max-width:100%;height:auto}a{color:#075c91}table{border-collapse:collapse;width:100%}th,td{padding:9px;text-align:left;border-bottom:1px solid #d5dee3}
.notice{border-left:4px solid #ad7732;padding:12px;background:#fff7e9}small{color:#435568}@media print{body{background:white}section{break-inside:avoid}main{padding:0}}
</style><main><p>PRIVATE WORKING EVIDENCE PACK · 10 SEPTEMBER 2026</p>
<h1>How observation choices change measured coarsening</h1>
<p>64 long-run replicas, eight fresh-seed repeat replicas, controlled image tests and five original experimental feasibility slices.</p>
<p class="notice">Computational findings, not an established new physical law. Experimental slices are unregistered and not validated for phase-size measurement. No academic endorsement or journal acceptance is claimed. AI assistance is documented.</p>
<section><h2>Start here</h2><p><a href="docs/MEASUREMENT_STUDY_RESULTS.md">Results and claim boundaries</a> · <a href="docs/PAPER_EVIDENCE_GUIDE.md">Your writing guide</a> · <a href="research/IMAGING_PROTOCOL.md">Observation protocol</a> · <a href="AI_USE_AND_CONTRIBUTIONS.md">Contributions</a></p>
<p>The strongest repeated finding is that binning plus segmentation changes the fitted effective exponent without changing the simulated trajectory. The smallest-crop effect varies between ensembles; no universal correction is established.</p></section>
<section><h2>Fresh-seed repeat: paired exponent changes</h2><p>Four replicas per composition; nominal 1,000–20,000 sweeps, actual 1,224–20,000. Difference from full finite-window image reference; 95% whole-replica bootstrap intervals, not total uncertainty.</p>
<table><tr><th>Composition</th><th>Operator</th><th>Difference</th><th>Interval</th></tr>'''+table+'''</table></section>'''+figures+'''
<section><h2>Reproduction and limitations</h2><p>See README.md for commands. Source snapshots and all raw files are included, with SHA-256 hashes in MANIFEST.json. Keep the source files paired with their recorded environment and analysis manifests.</p>
<p>Original experimental data: Jonas Fell, <a href="https://doi.org/10.5281/zenodo.14923133">Zenodo 14923133</a>, CC-BY-4.0. The five TIFFs are unchanged selected members; archive-wide checksums were not verified. See THIRD_PARTY_DATA.md.</p>
<p>Independent understanding, prior-art reconciliation, a defensible experimental sampling/segmentation procedure and external technical review remain necessary before submission.</p></section></main></html>'''
    (output/'index.html').write_text(page)
    (output/'README.md').write_text('''# Private coarsening evidence pack

Open index.html for the figure index. Read docs/MEASUREMENT_STUDY_RESULTS.md
and docs/PAPER_EVIDENCE_GUIDE.md before writing. This pack is not a finished
paper, endorsement, or proof of novelty. Nothing was submitted automatically.
The source repository declares MIT in CITATION.cff but currently lacks a
standalone LICENSE file. Clarify source licensing before public redistribution;
the experimental images separately carry the verified CC-BY-4.0 licence.

## Reproduce in a compatible scientific Python environment

The tested environment is recorded in environment.freeze.txt; installing the
entire freeze on another platform is not guaranteed to work. Numerical core:
Python 3.11, NumPy 2.0.2, SciPy 1.17.1, Numba 0.60.0, Matplotlib and Pillow.
From the unpacked root (new output directories preserve original analyses):

```bash
NUMBA_CACHE_DIR=.numba_cache_tests MPLCONFIGDIR=.mplconfig python -m unittest discover -s tests -v
MPLCONFIGDIR=.mplconfig python -m research.verify_study research/runs/overnight
MPLCONFIGDIR=.mplconfig python -m research.compare_estimators research/runs/overnight --output reproduced_estimators
MPLCONFIGDIR=.mplconfig python -m research.imaging_benchmark research/runs/overnight --output reproduced_imaging
MPLCONFIGDIR=.mplconfig python -m research.imaging_benchmark research/runs/imaging_validation --output reproduced_repeat
```

For scientific-image import, run python -m research.analyse_images --help.
No experimental input manifest is populated automatically: phase thresholds,
calibration, ROI and specimen identity require scientific justification.

The full read-only campaign checks do not independently verify the first heat
interval, and do not prove every implementation detail is correct. The whole
study is primarily Model B; no new Model A results are claimed.
''')
    (output/'THIRD_PARTY_DATA.md').write_text('''# Third-party experimental data

Creator: Jonas Fell (Saarland University).
Title: X-ray computed tomography dataset: 3D microstructural evolution of an
annealed Al alloy imaged using SEM-based nano-CT.
Source: https://doi.org/10.5281/zenodo.14923133
Licence: Creative Commons Attribution 4.0 International,
https://creativecommons.org/licenses/by/4.0/

Five original, unmodified central TIFF slices are included under
research/runs/alge_feasibility/. The manifest identifies their archive members,
local hashes, CRC checks and selection procedure. QA figures are derived
displays with separate percentile contrast scaling; they are not quantitative
phase segmentation. No endorsement by the data creator is implied.
''')
    inventory={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'MANIFEST.json').write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
        files=inventory),indent=2)+'\n')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(output))
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise RuntimeError('Archive CRC verification failed')
        for name,digest in inventory.items():
            import hashlib
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise RuntimeError(f'Archive hash mismatch: {name}')
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive)}  {archive.name}\n')
    print(json.dumps(dict(folder=str(output),archive=str(archive),bytes=archive.stat().st_size,
        files=len(inventory)+1,archive_crc_and_hashes_verified=True),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    build(p.parse_args().output)
