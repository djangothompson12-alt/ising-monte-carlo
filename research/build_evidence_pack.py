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
FROZEN_MAIN_SOURCE=Path('research/frozen_sources/2026-09-10')


def verify_added_figure_sources(root):
    """Reject a pack if the new compact figures outlive their archived inputs."""
    provenance=json.loads((root/'figures/fig_core_observation_shift_v1.json').read_text())
    expected=('research/runs/overnight/analysis/exponents.csv',
              'research/runs/overnight/imaging_v1/paired_fits.csv',
              'research/runs/imaging_validation/imaging_v1/paired_fits.csv')
    if (set(provenance['input_sha256'])!=set(expected)
        or provenance['source_sha256']!=sha(root/'research/plot_core_results.py')):
        raise ValueError('Compact-figure provenance does not match its declared inputs/source')
    for relative in expected:
        if provenance['input_sha256'][relative]!=sha(root/relative):
            raise ValueError(f'Compact figure has a stale input: {relative}')
    control=json.loads((root/'research/runs/synthetic_growth_control_v2/provenance.json').read_text())
    if (control['source_sha256']!=sha(root/'research/synthetic_growth_control.py')
        or control['imaging_sha256']!=sha(root/'research/imaging.py')):
        raise ValueError('Known-growth control provenance is stale')
    morphology=json.loads((root/'figures/fig_archived_morphology_v1.json').read_text())
    if (morphology['source_sha256']!=sha(root/'research/plot_archived_morphology.py')
        or set(morphology['raw_npz_sha256'])!=
           {'c0_L128_rep000.npz','c1_L128_rep000.npz'}):
        raise ValueError('Morphology figure source provenance is stale')
    for name, recorded in morphology['raw_npz_sha256'].items():
        if recorded!=sha(root/'research/runs/overnight'/name):
            raise ValueError(f'Morphology figure raw input is stale: {name}')
    paired=json.loads((root/'research/results/paired_window_sensitivity_2026-09-18/provenance.json').read_text())
    if (paired['source_sha256']['research/paired_window_sensitivity.py']
            !=sha(root/'research/paired_window_sensitivity.py')
        or paired['source_sha256']['research/analyse_campaign.py']
            !=sha(root/'research/analyse_campaign.py')
        or paired['input_manifest_sha256']!=sha(root/'research/runs/overnight/manifest.json')
        or paired['input_status_sha256']!=sha(root/'research/runs/overnight/status.json')):
        raise ValueError('Paired fitting-window audit provenance is stale')
    for name, recorded in paired['input_sha256'].items():
        if recorded!=sha(root/'research/runs/overnight'/name):
            raise ValueError(f'Paired fitting-window audit raw input is stale: {name}')


def verify_alge_audit_provenance(root):
    """Check the separate CC BY source and analysis hashes before packing."""
    qa_path=root/'research/results/alge_time_series_metadata_qa_2026-09-18/metadata_qa.json'
    qa=json.loads(qa_path.read_text())
    static=json.loads((root/'research/results/alge_static_operator_2026-09-18/summary.json').read_text())
    if (qa['analysis_source_sha256']!=sha(root/'research/inspect_alge_time_series.py')
        or static['qa_manifest_sha256']!=sha(qa_path)
        or static['protocol_sha256']!=sha(root/'research/ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md')
        or static['source_sha256']['research/alge_static_operator_test.py']!=sha(root/'research/alge_static_operator_test.py')
        or static['source_sha256']['research/imaging.py']!=sha(root/'research/imaging.py')):
        raise ValueError('Al–Ge real-image audit method provenance is stale')
    for name, recorded in static['input_tiff_sha256'].items():
        if (recorded!=sha(root/'research/runs/alge_time_series_source_v1'/name)
            or recorded!=next(item['sha256'] for item in qa['records'] if item['file']==name)):
            raise ValueError(f'Al–Ge real-image source changed: {name}')


def verify_alge_figure_provenance(root):
    figure=root/'figures/fig_alge_fixed_plane_audit.png'
    meta=json.loads((root/'figures/fig_alge_fixed_plane_audit.json').read_text())
    expected=(root/'research/plot_alge_static_operator.py',
              root/'research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv',
              root/'research/results/alge_static_operator_2026-09-18/summary.json')
    if (not figure.is_file()
        or meta['source_sha256']!=sha(expected[0])
        or meta['table_sha256']!=sha(expected[1])
        or meta['summary_sha256']!=sha(expected[2])):
        raise ValueError('Al–Ge static audit figure provenance is stale')


def build(output):
    archive=output.with_suffix('.zip')
    if output.exists() or archive.exists():raise FileExistsError('Choose a new pack name')
    verify_added_figure_sources(ROOT)
    verify_alge_audit_provenance(ROOT)
    verify_alge_figure_provenance(ROOT)
    # Both archived campaigns record the pre-temperature-ratio runner. The
    # present research/campaign.py has a different hash and must not be used
    # to attest these older trajectories.
    audits={name:verify(ROOT/'research/runs'/name, ROOT/FROZEN_MAIN_SOURCE)
            for name in ('overnight','imaging_validation')}
    reference_name='majumder_das_2010_l128'
    reference_folder=ROOT/'research/runs'/reference_name
    audits[reference_name]=verify(reference_folder, ROOT)
    reference_observables=json.loads((ROOT/'output/benchmark_observable_audit_2026-09-17.json').read_text())
    if (reference_observables['manifest_sha256']!=sha(reference_folder/'manifest.json')
        or reference_observables['replicas']!=40
        or reference_observables['snapshots_checked']!=3600
        or reference_observables['directional_lengths_checked']!=7200
        or reference_observables['unresolved_saved']!=reference_observables['unresolved_recomputed']):
        raise ValueError('Reference observable audit is stale or incomplete')
    reference_replay=json.loads((ROOT/'output/benchmark_first_interval_replay_2026-09-17.json').read_text())
    reference_files={p.name:sha(p) for p in sorted(reference_folder.glob('*.npz'))}
    reference_manifest=json.loads((reference_folder/'manifest.json').read_text())
    if (reference_replay['status']!='passed' or reference_replay['replicas']!=40
        or reference_replay['raw_npz_sha256']!=reference_files
        or reference_replay['source_sha256']!=sha(ROOT/'research/replay_first_energy_interval.py')
        or reference_replay['engine_sha256']!=reference_manifest['identity']['sources']['model_b/kawasaki_engine.py']):
        raise ValueError('Reference preparation/energy replay evidence is stale or mismatched')
    audits[reference_name]['archived_observables_independently_recomputed']=True
    audits[reference_name]['first_interval_preparation_replay_matches_all_raw_files']=True
    audits[reference_name]['paper_method_match_verified_by_student']=False
    for name, replay_name in (('overnight','overnight'),
                              ('imaging_validation','repeat')):
        replay_path=ROOT/f'output/first_interval_replay_{replay_name}_2026-09-17_v2.json'
        replay=json.loads(replay_path.read_text())
        actual_files={p.name:sha(p) for p in sorted((ROOT/'research/runs'/name).glob('*.npz'))}
        manifest=json.loads((ROOT/'research/runs'/name/'manifest.json').read_text())
        if (replay['status']!='passed' or replay['replicas']!=len(actual_files)
            or replay['raw_npz_sha256']!=actual_files
            or replay['source_sha256']!=sha(ROOT/'research/replay_first_energy_interval.py')
            or replay['engine_sha256']!=manifest['identity']['sources']['model_b/kawasaki_engine.py']):
            raise ValueError(f'{name}: first-interval replay evidence is stale or mismatched')
        audits[name]['first_interval_preparation_replay_matches_all_raw_files']=True
        audits[name]['first_interval_replay_is_independent_dynamics_implementation']=False
    sample_check=json.loads((ROOT/'output/small_lattice_sampling_2026-09-17_v1.json').read_text())
    if (sample_check['status']!='passed finite-equilibrium diagnostic'
        or sample_check['source_sha256']!=sha(ROOT/'research/check_small_lattice_sampling.py')
        or sample_check['engine_sha256']!=sha(ROOT/'model_b/kawasaki_engine.py')):
        raise ValueError('Small-lattice sampler diagnostic is stale or mismatched')
    output.mkdir(parents=True)
    selected=[ROOT/p for p in ('requirements.txt','CITATION.cff','AI_USE_AND_CONTRIBUTIONS.md',
        'EXTERNAL_REVIEW.md',
        'model_a/ising_engine.py','model_a/ising_3d_engine.py',
        'model_a/visualizer.py','model_a/plot_observables_from_csv.py',
        'model_a/results/observables.csv',
        'model_a/figures/fig1_phase_transitions_corrected.png',
        'model_b/kawasaki_engine.py','model_b/kawasaki_3d_engine.py',
        'model_b/research_export.py','model_b/solara_app.py',
        'phase_diagram.py','experiments/string_lab.py',
        'docs/MEASUREMENT_STUDY_RESULTS.md','docs/PAPER_EVIDENCE_GUIDE.md','docs/OVERNIGHT_RESULTS.md',
        'docs/CLAIM_AUDIT_2026-09-17.md','docs/LITERATURE_COMPARISON_2026-09-17.md',
        'docs/ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md',
        'docs/PAIRED_WINDOW_AUDIT_2026-09-18.md',
        'docs/ALGE_REAL_IMAGE_AUDIT_2026-09-18.md',
        'docs/BINNING_DECOMPOSITION_RESULTS_2026-09-17.md',
        'docs/SMALL_LATTICE_EQUILIBRIUM_CHECK_2026-09-17.md',
        'docs/METALDAM_STATIC_PILOT_2026-09-17.md',
        'docs/METALDAM_CLEANUP_SENSITIVITY_2026-09-17.md',
        'docs/METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md',
        'docs/INDEPENDENT_AUDIT_2026-09-17.md',
        'docs/REFERENCE_RUN_INTEGRITY_2026-09-17.md',
        'docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md',
        'docs/EXTERNAL_DATASET_SCOUT_2026-09-17.md',
        'docs/EXTERNAL_USE_DECISION_2026-09-17.md',
        'docs/PARTNER_PILOT_PROTOCOL_2026-09-17.md',
        'docs/APPLIED_IMAGE_AUDIT.md','docs/MASK_RESOLUTION_AUDIT.md',
        'docs/REVIEW_RESPONSE_LOG.template.md',
        'docs/FECR_MATERIALS_CASE_STUDY_2026-09-18.md',
        'docs/REGULAR_SOLUTION_BINODAL_2026-09-18.md',
        'docs/EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md',
        'docs/TECHNICAL_REPORT_BACKBONE.md','docs/INITIAL_LENGTH_SENSITIVITY_2026-09-17.md',
        'docs/SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md',
        'manuscript/REPORT_DRAFT_2026-09-18.md',
        'docs/review_brief.html','docs/PROGRESS_AND_LIMITS.md',
        'docs/FIVE_WORKSTREAMS_STATUS_2026-09-13.md',
        'figures/fig_regular_solution_spinodal.png',
        'figures/fig_regular_solution_binodal_spinodal.png',
        'figures/fig_exact_vs_meanfield_coexistence.png',
        'figures/fig_binning_decomposition_v2.png',
        'figures/fig_binning_decomposition_v2.json',
        'figures/fig_core_window_sensitivity_v1.png',
        'figures/fig_core_observation_shift_v1.png',
        'figures/fig_core_observation_shift_v1.json',
        'figures/fig_archived_morphology_v1.png',
        'figures/fig_archived_morphology_v1.json',
        'figures/fig_alge_fixed_plane_audit.png',
        'figures/fig_alge_fixed_plane_audit.json',
        'output/archive_observable_audit_overnight_2026-09-17.json',
        'output/archive_observable_audit_repeat_2026-09-17.json',
        'output/archive_fit_audit_2026-09-17.json',
        'output/first_interval_replay_overnight_2026-09-17_v2.json',
        'output/first_interval_replay_repeat_2026-09-17_v2.json',
        'output/small_lattice_sampling_2026-09-17_v1.json')]
    selected += [ROOT/'research/runs/public_mask_pilot/reference_scale_v1/per_image.csv',
                 ROOT/'research/runs/public_mask_pilot/reference_scale_v1/summary.json']
    selected += [ROOT/'research/results/README.md',
                 ROOT/'research/results/paired_window_sensitivity_2026-09-18/paired_window_differences.csv',
                 ROOT/'research/results/paired_window_sensitivity_2026-09-18/provenance.json']
    selected += [ROOT/'research/results/alge_time_series_metadata_qa_2026-09-18/metadata_qa.json',
                 ROOT/'research/results/alge_time_series_metadata_qa_2026-09-18/common_coordinate_slice_qa.png',
                 ROOT/'research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv',
                 ROOT/'research/results/alge_static_operator_2026-09-18/summary.json']
    selected += [ROOT/'output/benchmark_observable_audit_2026-09-17.json',
                 ROOT/'output/benchmark_first_interval_replay_2026-09-17.json']
    selected+=list((ROOT/'research').glob('*.py'))+list((ROOT/'research').glob('*.md'))
    selected+=list((ROOT/'research/plans').glob('*.json'))+list((ROOT/'tests').glob('*.py'))
    selected+=list((ROOT/FROZEN_MAIN_SOURCE).rglob('*.py'))
    selected+=[ROOT/'research/experimental_images.template.json',
               ROOT/'research/reference_benchmark.template.json',
               ROOT/'research/mask_resolution_audit.template.json']
    if (ROOT/'LICENSE').exists():selected.append(ROOT/'LICENSE')
    missing=[str(p) for p in selected if not p.is_file()]
    if missing:raise FileNotFoundError(f'Missing required source files: {missing}')
    for path in selected:
        dest=output/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    for name in ('overnight','imaging_validation','majumder_das_2010_l128',
                 'experimental_source_audit','alge_feasibility',
                 'synthetic_growth_control_v2'):
        shutil.copytree(ROOT/'research/runs'/name,output/'research/runs'/name)
    (output/'VERIFICATION.json').write_text(json.dumps(audits,indent=2)+'\n')
    (output/'environment.freeze.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    with (output/'research/runs/imaging_validation/imaging_v1/paired_fits.csv').open() as f:rows=list(csv.DictReader(f))
    shown=[r for r in rows if r['condition'] in ('bin4','blur2','crop32') and r['t_min']=='1000' and r['t_max']=='20000']
    table=''.join('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in (r['c'],r['condition'],
        f'{float(r["delta_vs_full"]):.3f}',f'[{float(r["delta_low"]):.3f}, {float(r["delta_high"]):.3f}]'))+'</tr>' for r in shown)
    panels=[
        ('Model A baseline (archived data, corrected label)',
         'model_a/figures/fig1_phase_transitions_corrected.png',
         'Redrawn from the unchanged archived temperature-sweep CSV. The fourth panel is an absolute-magnetization fluctuation proxy, not the zero-field magnetic susceptibility; no new Model A run is claimed.'),
        ('Materials thermodynamics guide','figures/fig_regular_solution_binodal_spinodal.png',
         'Mean-field regular-solution binodal and spinodal from the model couplings; neither an exact 2D Ising boundary nor a measured Fe–Cr diagram. The marked metastable cases do not establish a nucleation mechanism.'),
        ('Exact 2D equilibrium check','figures/fig_exact_vs_meanfield_coexistence.png',
         'The exact infinite-lattice coexistence boundary from spontaneous magnetisation differs from the mean-field guide. It is not an exact spinodal, a finite-time kinetic result or an alloy phase diagram.'),
        ('Long-run growth','research/runs/overnight/analysis/growth_c0.png',
         'Replica standard-error bands. The z=3 display is a candidate comparison, not a fitted or demonstrated scaling collapse.'),
        ('Two compositions, two fixed archived times','figures/fig_archived_morphology_v1.png',
         'First saved L=128 replica at each composition, selected by replica number rather than appearance; sweeps 1,069 and 200,000. Illustrative morphology only, not ensemble inference or experimental microscopy. Raw hashes and seeds are in fig_archived_morphology_v1.json.'),
        ('Real Al–Ge image audit: every fixed plane','figures/fig_alge_fixed_plane_audit.png',
         'Derived from Fell 2023 labelled Al–Ge tomography, CC BY 4.0. Amber planes are unresolved, not removed. Ratios are static 4×/native lengths on correlated slices of one specimen; no ageing exponent, strength prediction or outside adoption.'),
        ('Core result: fitting-window sensitivity','figures/fig_core_window_sensitivity_v1.png',
         'Same eight trajectories per composition at L=128. Error bars are whole-replica bootstrap percentiles on correlated, overlapping windows; not evidence of an asymptotic law.'),
        ('Different observables on identical trajectories','research/runs/overnight/estimator_analysis_v1/estimators_c0.5_L128.png',
         'Different definitions of length; not four estimates of a known physical particle radius.'),
        ('Controlled observation operators','research/runs/overnight/imaging_v1/operators_c0.15.png',
         'The dynamics are unchanged; synthetic image operations change what is measured.'),
        ('Core result: paired image-processing shift','figures/fig_core_observation_shift_v1.png',
         'A separate non-periodic image estimator. Fourfold block averaging plus binary thresholding changes a fitted image exponent on the same snapshots; fresh seeds repeat the direction. Different time grids and small ensembles remain.'),
        ('Known-growth measurement control','research/runs/synthetic_growth_control_v2/known_growth_control.png',
         'Constructed square-domain width grows exactly as t^(1/3). Finite-image measurements differ and approach the imposed value with wider fields. This does not explain the low Kawasaki engine slopes.'),
        ('4× binning: block averaging versus binary threshold','figures/fig_binning_decomposition_v2.png',
         'Post-hoc point-estimate decomposition. Contributions depend on composition and fitting window; intervals are in the paired-fit tables.'),
        ('Actual simulation size versus observation window','research/runs/overnight/imaging_v1/box_vs_window_c0.15.png',
         'A descriptive comparison, not proof that cropping and physical finite size have the same cause.'),
        ('Independent seeded repeat','research/runs/imaging_validation/imaging_v1/observation_ratios_c0.15.png',
         'Four fresh replicas per composition; its checkpoint grid differs from the original study.'),
        ('Experimental feasibility — not validation','research/runs/alge_feasibility/qa/experimental_feasibility.png',
         'Selected unregistered slices; no experimental exponent or simulation-to-alloy calibration.')]
    panels.append(('Public Al–Ge labelled-stack inspection',
        'research/results/alge_time_series_metadata_qa_2026-09-18/common_coordinate_slice_qa.png',
        'Adapted from Jonas Fell, DOI 10.17632/hj9njz3rxp.1, CC BY 4.0. A fixed physical-coordinate slice shows stage-dependent specimen movement and morphology; it does not prove feature registration or a kinetics law.'))
    figures=''.join(f'<section><h2>{html.escape(title)}</h2><img src="{path}" alt="{html.escape(title)}"><p><small>{html.escape(caption)}</small></p></section>'
                    for title,path,caption in panels)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Coarsening measurement study — evidence pack</title><style>
body{font:17px/1.55 system-ui,sans-serif;color:#192c39;background:#f7f8fa;margin:0}main{max-width:1100px;margin:auto;padding:36px 24px}
h1{font-size:34px;line-height:1.15}h2{font-size:23px}section{background:white;padding:22px;margin:24px 0;border:1px solid #d5dee3;border-radius:8px}
img{display:block;max-width:100%;height:auto}a{color:#075c91}table{border-collapse:collapse;width:100%}th,td{padding:9px;text-align:left;border-bottom:1px solid #d5dee3}
.notice{border-left:4px solid #ad7732;padding:12px;background:#fff7e9}small{color:#435568}@media print{body{background:white}section{break-inside:avoid}main{padding:0}}
</style><main><p>PRIVATE WORKING EVIDENCE PACK · BUILD_DATE_PLACEHOLDER</p>
<h1>How observation choices change measured coarsening</h1>
<p>A historical Model A baseline, 64 primary Model B replicas, eight fresh-seed repeat replicas, a separately verified 40-trajectory long reference run, controlled image tests and five original experimental feasibility slices.</p>
<p class="notice">Computational findings, not an established new physical law. Experimental slices are unregistered and not validated for phase-size measurement. No academic endorsement or journal acceptance is claimed. AI assistance is documented.</p>
<section><h2>Start here</h2><p><a href="EXTERNAL_REVIEW.md">Questions for a reviewer</a> · <a href="docs/review_brief.html">One-page brief</a> · <a href="manuscript/REPORT_DRAFT_2026-09-18.md">AI-assisted working-paper draft for student revision</a> · <a href="docs/MEASUREMENT_STUDY_RESULTS.md">Results and claim boundaries</a> · <a href="research/DATA_DICTIONARY.md">Data dictionary</a> · <a href="docs/PAPER_EVIDENCE_GUIDE.md">Your writing guide</a> · <a href="research/IMAGING_PROTOCOL.md">Observation protocol</a> · <a href="research/PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md">Fixed new-seed holdout plan (not yet run)</a> · <a href="AI_USE_AND_CONTRIBUTIONS.md">Contributions</a></p>
<p>The strongest repeated finding is that binning plus segmentation changes the fitted effective exponent without changing the simulated trajectory. A <a href="docs/PAIRED_WINDOW_AUDIT_2026-09-18.md">post-result paired audit</a> separately quantifies the fitting-window shift on identical trajectories. The smallest-crop effect varies between ensembles; no universal correction is established.</p>
<p>A <a href="docs/METALDAM_STATIC_PILOT_2026-09-17.md">separate static-image pilot</a> finds that an image mask can overlap expert labels yet give a very different length. Its <a href="docs/METALDAM_CLEANUP_SENSITIVITY_2026-09-17.md">post-hoc cleanup test</a> did not establish a ready-to-use segmentation method. Source images are not redistributed here.</p></section>
<section><h2>Public Al–Ge image test: failures retained</h2><p>Four published solid-state-aged, segmented stacks were inspected under CC BY 4.0 attribution. A <a href="docs/ALGE_REAL_IMAGE_AUDIT_2026-09-18.md">fixed exploratory within-image test</a> was unable to resolve its length on all 11 central planes at 15 or 105 minutes; it did resolve all 11 at 195 and 315 minutes, with descriptive 4×/native median static length ratios 1.200 and 1.082. The source authors separated Ge lamellae from later precipitates; this initial all-Ge 2D length does not. The original TIFFs are not in this packet. This is not a four-point growth-law fit, a precipitate-size or strength prediction, an independent specimen comparison, a model-to-hours calibration or external lab adoption.</p></section>
<section><h2>Real-mask resolution sensitivity, not ageing validation</h2><p>A separate <a href="docs/METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md">predeclared exploratory audit</a> started from all 42 published austenite masks and compared each mask with lower-resolution versions on a matched field. At 4× coarser resolution, the measured static correlation length increased for all 42 masks (median ratio 1.050); at 8× the median ratio was 1.195. The <a href="research/runs/public_mask_pilot/reference_scale_v1/per_image.csv">per-image table</a> and <a href="research/runs/public_mask_pilot/reference_scale_v1/summary.json">summary</a> are included, but the producer's pixels are not. These are pixel-unit descriptive comparisons, not independent-specimen inference, external use or a Kawasaki-to-alloy validation.</p></section>
<section><h2>Physics checks and literature boundary</h2><p>A <a href="docs/SMALL_LATTICE_EQUILIBRIUM_CHECK_2026-09-17.md">126-state exact-sector check</a> tests the exchange rule and a tiny equilibrium sampler; it is not growth-law validation. The <a href="docs/LITERATURE_COMPARISON_2026-09-17.md">source comparison</a> identifies prior Kawasaki work and a distinct Cahn–Hilliard study with off-critical sub-one-third results.</p><p>The <a href="docs/REGULAR_SOLUTION_BINODAL_2026-09-18.md">common-tangent derivation</a> places coexistence and local instability on the approximate materials diagram; an <a href="docs/EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md">exact 2D equilibrium check</a> shows where its coexistence guide differs from known lattice theory. A <a href="docs/FECR_MATERIALS_CASE_STUDY_2026-09-18.md">published Fe–Cr case study</a> shows actual structure, measurement-method and hardness relationships; none of its physical values are predictions from this code.</p></section>
<section><h2>Completed reference data, not yet a paper replication</h2><p>The separate 50:50, 0.6 Tc, L=128 campaign completed 40 trajectories to 4.5 million sweeps. Its archived measurements and energy accounting passed the <a href="docs/REFERENCE_RUN_INTEGRITY_2026-09-17.md">integrity audit</a>. A <a href="docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md">paper-to-code crosswalk</a> identifies matches and remaining ambiguities. No fitted growth exponent is presented here: the student still needs to verify the literature observation method before a matched comparison. The concurrent 0.65 Tc multi-size extension is incomplete and is not included.</p><p>The <a href="docs/EXTERNAL_DATASET_SCOUT_2026-09-17.md">Al–Cu series</a> remains a candidate, not analysed here; its solid–liquid physics differs. The Al–Ge series has a bounded real-image observation audit above, but its solid-state processing is still not a kinetic match for this model. Prior two-point and feature analyses limit novelty. The <a href="docs/PARTNER_PILOT_PROTOCOL_2026-09-17.md">partner-pilot protocol</a> is a question-and-stop-rule proposal, not external use.</p></section>
<section><h2>Fresh-seed repeat: paired exponent changes</h2><p>Four replicas per composition; nominal 1,000–20,000 sweeps, actual 1,224–20,000. Difference from full finite-window image reference; 95% whole-replica bootstrap intervals, not total uncertainty.</p>
<table><tr><th>Composition</th><th>Operator</th><th>Difference</th><th>Interval</th></tr>'''+table+'''</table></section>'''+figures+'''
<section><h2>Reproduction and limitations</h2><p>See README.md for commands. Source snapshots and all raw files are included, with SHA-256 hashes in MANIFEST.json. Keep the source files paired with their recorded environment and analysis manifests.</p>
<p>Original experimental data: Jonas Fell, <a href="https://doi.org/10.5281/zenodo.14923133">Zenodo 14923133</a>, CC-BY-4.0. The five TIFFs are unchanged selected members; archive-wide checksums were not verified. See THIRD_PARTY_DATA.md.</p>
<p>Independent understanding, prior-art reconciliation, a defensible experimental sampling/segmentation procedure and external technical review remain necessary before submission.</p></section></main></html>'''
    page=page.replace('BUILD_DATE_PLACEHOLDER',datetime.now(timezone.utc).date().isoformat())
    (output/'index.html').write_text(page)
    (output/'README.md').write_text('''# Private coarsening evidence pack

Open index.html for the figure index. Read docs/MEASUREMENT_STUDY_RESULTS.md
and docs/PAPER_EVIDENCE_GUIDE.md before writing. This pack is not a finished
paper, endorsement, or proof of novelty. Nothing was submitted automatically.
The repository's own source code has an MIT LICENSE file. The included
experimental images carry a separate verified CC-BY-4.0 licence; preserve
their attribution and do not infer that the MIT licence covers them.

## Reproduce in a compatible scientific Python environment

The tested environment is recorded in environment.freeze.txt; installing the
entire freeze on another platform is not guaranteed to work. Numerical core:
Python 3.11, NumPy 2.0.2, SciPy 1.17.1, Numba 0.60.0, Matplotlib and Pillow.
From the unpacked root (new output directories preserve original analyses),
use writable local caches. On some macOS machines, Matplotlib's font scan may
otherwise stall or warn that its default cache is not writable:

```bash
mkdir -p .numba_cache_tests .mplconfig .cache_tests
XDG_CACHE_HOME=.cache_tests NUMBA_CACHE_DIR=.numba_cache_tests MPLCONFIGDIR=.mplconfig python -m unittest discover -s tests -v
MPLCONFIGDIR=.mplconfig python -m research.verify_study research/runs/overnight --source-root research/frozen_sources/2026-09-10
MPLCONFIGDIR=.mplconfig python -m research.verify_study research/runs/imaging_validation --source-root research/frozen_sources/2026-09-10
MPLCONFIGDIR=.mplconfig python -m research.verify_study research/runs/majumder_das_2010_l128 --source-root .
MPLCONFIGDIR=.mplconfig python -m research.compare_estimators research/runs/overnight --output reproduced_estimators
MPLCONFIGDIR=.mplconfig python -m research.imaging_benchmark research/runs/overnight --output reproduced_imaging
MPLCONFIGDIR=.mplconfig python -m research.imaging_benchmark research/runs/imaging_validation --output reproduced_repeat
MPLCONFIGDIR=.mplconfig python -m research.replay_first_energy_interval research/runs/overnight --source-root research/frozen_sources/2026-09-10 --output reproduced_first_interval.json
```

For scientific-image import, run python -m research.analyse_images --help.
No experimental input manifest is populated automatically: phase thresholds,
calibration, ROI and specimen identity require scientific justification.

The archived campaign runner is in research/frozen_sources/2026-09-10. The
current research/campaign.py is intentionally different; verifying these
older overnight/repeat NPZ files against the current runner should fail its
source-hash check. The separate 40-run reference campaign uses the current
runner and is verified with --source-root .; the two provenance paths must
not be interchanged.
The bounded Al–Ge static operator table can be checked against its recorded
source hashes, but the four original Mendeley ROI TIFF stacks are **not** in
this packet. Download them from DOI 10.17632/hj9njz3rxp.1, verify their
SHA-256 hashes in the included metadata_qa.json, and keep the 260-nm
overview scan out of the 60-nm ROI comparison. The source paper has already
analysed 3D feature evolution; this packet supplies no new ageing exponent.
The basic campaign verifier checks only later heat intervals. A separate
source-matched preparation replay checks the first recorded interval in all
72 archived files; see docs/ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md. This is
not an independent dynamics implementation and does not prove every model
detail is correct. The study is primarily Model B; no new Model A results are
claimed.
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

Separate source: Jonas Fell (2023), "Microstructural evolution of an Al-Ge
alloy revealed by nano-CT", Mendeley Data V1,
https://doi.org/10.17632/hj9njz3rxp.1, CC BY 4.0.
The four original ROI TIFF stacks at 15, 105, 195 and 315 minutes were
retrieved and hashed locally but are **not redistributed** in this packet.
The included common_coordinate_slice_qa.png is an adapted visual display
of labelled slices from that dataset. It is not a registered time series or
an experimental validation of the simulation. The numerical table and
metadata record the exact source hashes and analysis choices.
''')
    (output/'BUILD_CONTEXT.json').write_text(json.dumps(dict(
        built_utc=datetime.now(timezone.utc).isoformat(),
        git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        note='MANIFEST.json hashes included files. The base commit alone does not include uncommitted work; unrelated local filenames and application notes are intentionally omitted.'
    ),indent=2)+'\n')
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
