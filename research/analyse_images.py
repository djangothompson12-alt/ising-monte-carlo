"""Analyse explicitly calibrated, single-plane binary/grayscale image records.

This is a measurement utility, not automatic validation of Ising kinetics.
Input JSON: {"source":..., "license":..., "phase_definition":..., "records":
[{"id":...,"specimen":...,"path":...,"time":...,"time_unit":...,
"pixel_size":...,"length_unit":...,"threshold":...,"foreground":"above"}]}
Relative image paths resolve against the input manifest's directory. No threshold
is guessed. Only NPY or single-frame, scalar PNG/TIFF images are accepted.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from research.imaging import image_length,validate_image
from research.imaging_benchmark import sha,write_csv


def analyse(manifest_path,output):
    document=json.loads(manifest_path.read_text())
    for key in ('source','license','phase_definition'):
        if not isinstance(document.get(key),str) or not document[key].strip():
            raise ValueError(f'Missing documented {key}')
    records=document.get('records')
    if not isinstance(records,list) or not records:raise ValueError('No real image records supplied')
    if output.exists():raise FileExistsError('Use a new output directory')
    rows=[];seen=set();units=set();hashes={}
    for r in records:
        for key in ('id','specimen','path','time','time_unit','pixel_size','length_unit','threshold','foreground'):
            if key not in r:raise ValueError(f'Missing {key}')
        if not r['id'] or r['id'] in seen:raise ValueError('Missing/duplicate image id')
        seen.add(r['id']);units.add((r['time_unit'],r['length_unit']))
        if not r['specimen'] or not r['time_unit'] or not r['length_unit']:
            raise ValueError('Specimen and units must be named')
        if not np.isfinite(r['time']) or r['time']<0 or not np.isfinite(r['threshold']):raise ValueError('Invalid time/threshold')
        path=manifest_path.parent/r['path']
        if path.suffix.lower()=='.npy':img=np.load(path,allow_pickle=False)
        elif path.suffix.lower() in ('.png','.tif','.tiff'):
            with Image.open(path) as source:
                if getattr(source,'n_frames',1)!=1:raise ValueError('Choose and document a 2D slice, not a multipage volume')
                img=np.asarray(source)
        else:raise ValueError('Use NPY, PNG or single-plane TIFF')
        img=validate_image(img)
        if r['foreground'] not in ('above','below'):raise ValueError('Foreground must be above or below threshold')
        binary=img>=r['threshold'] if r['foreground']=='above' else img<r['threshold']
        result=image_length(2*binary.astype(float)-1,r['pixel_size'])
        hashes[r['id']]=sha(path)
        rows.append(dict(id=r['id'],specimen=r['specimen'],time=r['time'],time_unit=r['time_unit'],
            length_unit=r['length_unit'],pixel_size=r['pixel_size'],phase_fraction=float(binary.mean()),
            threshold=r['threshold'],foreground=r['foreground'],**result))
    if len(units)!=1:raise ValueError('Convert records to common time/length units explicitly')
    output.mkdir(parents=True)
    write_csv(output/'measurements.csv',rows)
    (output/'manifest.json').write_text(json.dumps(dict(input_manifest_sha256=sha(manifest_path),
        image_sha256=hashes,source=document['source'],license=document['license'],
        phase_definition=document['phase_definition'],source_hashes={p.name:sha(p) for p in
            (Path(__file__),Path(__file__).with_name('imaging.py'),Path(__file__).with_name('metrology.py'))}),indent=2)+'\n')
    (output/'REPORT.md').write_text('# Image measurements\n\nThese are finite-window, threshold-dependent 2D measurements, not calibrated particle radii.\n'
        'No growth-law exponent is fitted automatically. Independent specimens, registration, imaging changes, segmentation uncertainty and 2D/3D comparability require review.\n'
        'Slices of one volume are not independent specimens. No simulation-to-material time conversion is supplied.\n')
    print(output/'measurements.csv')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyse(a.manifest,a.output)
