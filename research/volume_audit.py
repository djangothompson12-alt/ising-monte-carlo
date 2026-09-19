"""Local 3D phase-mask audit with a portable interactive HTML report.

Input is an explicit JSON plan plus a 3D NPY volume or multipage TIFF.
No network connection or experimental time-series fitting is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.volume_metrology import block_mean, measure


def sha(path):
    """Stream hashes without loading an entire tomography stack into memory."""
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def required_text(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Declare {key}')
    return value


def load_box(path, roi):
    """Read only the explicitly selected TIFF planes/XY region."""
    bounds = np.asarray(roi)
    if bounds.shape != (3, 2) or bounds.dtype.kind not in 'iu':
        raise ValueError('roi_zyx must contain three integer [start, stop] pairs')
    if np.any(bounds[:, 0] < 0) or np.any(bounds[:, 1] <= bounds[:, 0]):
        raise ValueError('Invalid ROI bounds')
    slices = tuple(slice(int(a), int(b)) for a, b in bounds)
    shape = bounds[:, 1]-bounds[:, 0]
    if min(shape) < 32 or np.prod(shape) > 256**3:
        raise ValueError('Each side must be at least 32 voxels; maximum box is 256^3 voxels')
    if path.suffix.lower() == '.npy':
        source = np.load(path, mmap_mode='r', allow_pickle=False)
        if source.ndim != 3 or np.any(bounds[:, 1] > source.shape):
            raise ValueError('ROI outside a single 3D NPY volume')
        return np.asarray(source[slices]).copy()
    if path.suffix.lower() not in ('.tif', '.tiff'):
        raise ValueError('Use a 3D NPY or multipage TIFF')
    with Image.open(path) as source:
        if np.any(bounds[:, 1] > (source.n_frames, source.height, source.width)):
            raise ValueError('ROI outside TIFF volume')
        planes = []
        for z in range(*bounds[0]):
            source.seek(z)
            plane = np.asarray(source)
            if plane.ndim != 2:
                raise ValueError('TIFF must contain scalar label planes, not RGB images')
            planes.append(plane[slices[1:]].copy())
        return np.stack(planes)


def audit_box(labels, record):
    spacing = np.asarray(record['spacing_zyx'], dtype=float)
    if spacing.shape != (3,) or not np.all(np.isfinite(spacing) & (spacing > 0)):
        raise ValueError('Declare positive finite spacing_zyx')
    fg, bg = record['foreground'], record['background']
    if (any(isinstance(v, bool) or not isinstance(v, int) for v in (fg, bg))
            or fg == bg):
        raise ValueError('Declare different integer foreground/background labels')
    if any(n % 16 for n in labels.shape):
        raise ValueError('Box sides must divide by 16 for the fixed nested crops')
    if record['tie_rule'] not in ('foreground', 'background'):
        raise ValueError('Declare tie_rule: foreground or background')
    rows = []
    unknown = int(np.count_nonzero((labels != fg) & (labels != bg)))
    for numerator in (4, 3, 2):
        shape = tuple(n*numerator//4 for n in labels.shape)
        origin = tuple((n-m)//2 for n, m in zip(labels.shape, shape))
        field = (labels[tuple(slice(a, a+n) for a,n in zip(origin, shape))] == fg)
        for factor, stage in ((1, 'native'), (2, 'integrated'), (2, 'segmented'),
                              (4, 'integrated'), (4, 'segmented')):
            base = dict(id=record['id'], specimen=record['specimen'],
                        crop_fraction=numerator/4, crop_origin_zyx=json.dumps(origin),
                        crop_shape_zyx=json.dumps(shape), factor=factor, stage=stage,
                        unit=record['unit'], spacing_zyx=json.dumps((spacing*factor).tolist()),
                        unknown_voxels_in_full_box=unknown)
            if unknown:
                result = dict(mean_value=np.nan, half_height=np.nan, positive_lobe=np.nan,
                              half_height_status='ineligible: undeclared labels in full box',
                              chord_length=np.nan, complete_chords=0, censored_boundary_runs=0)
                result.update({f'{metric}_{axis}': np.nan
                               for metric in ('half_height', 'positive_lobe')
                               for axis in ('z', 'y', 'x')})
                base.update(integration_mean_error=np.nan, tie_fraction=np.nan)
            else:
                observed = block_mean(field, factor)
                error = float(observed.mean()-field.mean())
                if abs(error) > 1e-12:
                    raise ArithmeticError('Block integration did not preserve the field mean')
                ties = float(np.mean(observed == .5))
                if stage == 'segmented':
                    observed = (observed >= .5 if record['tie_rule'] == 'foreground'
                                else observed > .5)
                result = measure(observed, spacing*factor, binary=stage != 'integrated')
                base.update(integration_mean_error=error, tie_fraction=ties)
            rows.append({**base, **result})
    full = rows[0]
    for row in rows:
        native = next(r for r in rows if r['crop_fraction'] == row['crop_fraction']
                      and r['stage'] == 'native')
        for metric in ('half_height', 'positive_lobe', 'chord_length'):
            for name, ref in (('same_crop', native), ('full_box', full)):
                a,b = row[metric], ref[metric]
                row[f'{metric}_ratio_to_{name}'] = (a/b if np.isfinite(a)
                                                   and np.isfinite(b) and b > 0 else np.nan)
    return rows


def render_report(plan, rows):
    resolved=sum(r['half_height_status']=='resolved' for r in rows)
    columns = [('id','Volume'), ('crop_fraction','Field fraction per axis'),
               ('stage','Processing'), ('factor','Resolution factor'),
               ('mean_value','Mean / phase volume fraction'),
               ('half_height','Mean half-height length'), ('half_height_z','Z length'),
               ('half_height_y','Y length'), ('half_height_x','X length'),
               ('half_height_ratio_to_same_crop','Length / same crop native'),
               ('half_height_ratio_to_full_box','Length / full box native'),
               ('positive_lobe','Positive-lobe length'), ('chord_length','Complete chord mean'),
               ('complete_chords','Complete chords'), ('censored_boundary_runs','Censored runs'),
               ('unit','Unit'), ('half_height_status','Half-height status')]
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return f'{v:.5g}' if np.isfinite(v) else 'unresolved / not applicable'
        return str(v)
    body = ''.join('<tr data-volume="'+escape(str(r['id']), quote=True)+'">'+
                   ''.join('<td>'+escape(fmt(r[k]))+'</td>' for k,_ in columns)+'</tr>'
                   for r in rows)
    options = ''.join('<option>'+escape(r['id'])+'</option>' for r in plan['records'])
    headers = ''.join('<th>'+escape(name)+'</th>' for _,name in columns)
    context = ''.join('<li><b>'+escape(r['id'])+'</b>: '+escape(r['phase_definition'])+
                      '; '+escape(r['mask_authority'])+'; voxel spacing z/y/x '+
                      escape(str(r['spacing_zyx']))+' '+escape(r['unit'])+'. '+
                      escape(r['roi_reason'])+'</li>' for r in plan['records'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>3D microstructure audit</title>
<style>body{{margin:0;background:#edf2f1;color:#16353d;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1250px;margin:24px auto;padding:32px;background:white;border-top:6px solid #237e75}}
h1{{line-height:1.15}}h2{{font-size:20px}}.scroll{{overflow:auto;max-height:65vh}}
table{{border-collapse:collapse;font-size:13px}}th,td{{padding:10px;border-bottom:1px solid #ddd;white-space:nowrap;text-align:left}}
th{{position:sticky;top:0;background:#e3eeeb}}select,a.button{{padding:9px;border:1px solid #237e75;border-radius:4px}}
a{{color:#14695f}}.note{{padding:14px;background:#fff3db}}li{{margin:8px 0}}
@media print{{main{{margin:0;padding:0}}.scroll{{max-height:none;overflow:visible}}table{{font-size:8px}}}}
</style></head><body><main><p>MICROSTRUCTURE MEASUREMENT · LOCAL RESEARCH PROTOTYPE</p>
<h1>Does the measurement survive a smaller field or coarser voxels?</h1>
<p>Compare the same 3D phase mask at three field sizes and three resolutions.
Integration keeps partial-volume values; segmentation assigns each voxel to one phase.</p>
<p><b>Source:</b> {escape(plan['source'])}<br><b>Rights:</b> {escape(plan['license'])}</p>
<p><b>{len(rows)} comparisons; {resolved} resolved three-axis half-height lengths;
{len(rows)-resolved} unresolved or ineligible.</b> Resolution is a numerical crossing
condition, not evidence that a sparse field is representative.</p>
<p class="note">The reference is the supplied segmentation, whose accuracy is not established by this audit.
Phase volume fraction is not chemical composition. These overlapping fields are paired observations,
not independent specimens. No ageing exponent or property prediction is fitted.
Very sparse fields can be unrepresentative even when a crossing resolves. A length comparable
to or smaller than one voxel is interpolation, not recovered sub-voxel information.</p>
<h2>How to read the comparisons</h2><p>To test resolution, compare a processed length with the
native length of the <b>same crop</b>. To test field size, compare <b>native</b> crop rows with
the full box. A ratio of 1 means unchanged measured length. A missing crossing stays unresolved.
Chords exclude boundary-touching runs and may therefore favour shorter features in small fields.</p>
<p>Volume <select id="volume"><option value="">All volumes</option>{options}</select>
<a class="button" href="measurements.csv">Download all measurements</a>
<a class="button" href="manifest.json">Provenance</a></p>
<div class="scroll"><table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>
<h2>Declared fields and calibration</h2><ul>{context}</ul>
<p>Lengths use nonperiodic z/y/x correlations with local mean subtraction and actual pair counts.
The displayed mean requires a half-height crossing in all three directions. Axis-specific values
remain available when that mean is unresolved. No opposite volume faces are joined.</p>
<p>Use this report to ask a materials researcher whether the chosen quantity answers their measurement
question and what size of change matters. A stable result in these selected fields alone cannot establish
representativeness, segmentation accuracy or laboratory adoption.</p>
<script>document.getElementById('volume').addEventListener('change',function(){{
document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!!this.value&&r.dataset.volume!==this.value);}});</script>
</main></body></html>'''


def run(plan_path, output):
    if output.exists():
        raise FileExistsError('Choose a new output directory')
    plan = json.loads(plan_path.read_text())
    for key in ('source','license'):
        required_text(plan,key)
    if not isinstance(plan.get('records'), list) or not plan['records']:
        raise ValueError('Declare at least one volume')
    rows, provenance, seen = [], [], set()
    for record in plan['records']:
        for key in ('id','specimen','path','unit','roi_reason','phase_definition','mask_authority'):
            required_text(record,key)
        if record['id'] in seen:
            raise ValueError('Duplicate volume ID')
        seen.add(record['id'])
        path = plan_path.parent / record['path']
        digest = sha(path)
        if record.get('sha256') and digest != record['sha256']:
            raise ValueError('Volume changed since plan was declared')
        labels = load_box(path,record['roi_zyx'])
        rows.extend(audit_box(labels, record))
        provenance.append({**{k:v for k,v in record.items() if k != 'path'},
                           'sha256':digest, 'label_counts':{
                               str(v):int(n) for v,n in zip(*np.unique(labels,return_counts=True))}})
    output.mkdir(parents=True)
    with (output/'measurements.csv').open('x',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (output/'report.html').write_text(render_report(plan,rows))
    meta = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                source=plan['source'], license=plan['license'], records=provenance,
                input_plan_sha256=sha(plan_path),
                declared_protocol_sha256=plan.get('protocol_sha256'),
                sources={name:sha(Path(__file__).with_name(name)) for name in
                         ('volume_audit.py','volume_metrology.py','metrology.py')},
                outputs={name:sha(output/name) for name in ('measurements.csv','report.html')},
                boundary='Static 3D measurement sensitivity; no kinetic fit or external validation')
    (output/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    return output/'report.html'


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(run(args.plan,args.output))
