"""Fetch one deterministic central slice per annealing stage for feasibility QA.

Not registered, not independent specimens, not a kinetics dataset by itself.
Reads <=12 MB per archive by validated ranges, not the 25 GB full dataset.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from datetime import datetime,timezone
from research.source_audit import RemoteRange


def fetch(audit_folder,output):
    if output.exists():raise FileExistsError('Use a new subset directory')
    record=json.loads((audit_folder/'record.json').read_text())
    if record['metadata'].get('license',{}).get('id')!='cc-by-4.0':
        raise ValueError('Unexpected licence; review before downloading')
    output.mkdir(parents=True)
    provenance=dict(source_doi=record['doi'],creator='Jonas Fell',license='CC-BY-4.0',
        fetched_utc=datetime.now(timezone.utc).isoformat(),selection='middle sorted TIFF member at each stage, specified before viewing',
        raw_images_modified=False,registered=False,independent_specimens=False,
        use='feasibility inspection only; no experimental coarsening exponent',stages=[])
    for time in (0,15,105,195,315):
        file=next(f for f in record['files'] if f['key']==f'AlGe_{time}min_rec.zip')
        remote=RemoteRange(file['links']['self'],file['size'],budget=12000000)
        with zipfile.ZipFile(remote) as archive:
            images=sorted((i for i in archive.infolist() if i.filename.lower().endswith('.tif')),key=lambda i:i.filename)
            selected=images[len(images)//2]
            if selected.file_size>10000000 or selected.compress_size>10000000:
                raise ValueError('Slice exceeds download/decompression budget')
            raw=archive.read(selected) # zipfile verifies member CRC
            local=f'AlGe_{time}min_middle.tif';(output/local).write_bytes(raw)
            metadata={i.filename:archive.read(i).decode('cp1252',errors='replace') for i in archive.infolist()
                if i.filename.lower().endswith('.txt') and i.file_size<100000}
        provenance['stages'].append(dict(time_min=time,path=local,archive=file['key'],member=selected.filename,
            slice_index=len(images)//2,slice_count=len(images),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
            zip_member_crc32=f'{selected.CRC:08x}',archive_md5_not_verified=file['checksum'],text_metadata=metadata))
        (output/'manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
        print(f'Fetched {local}: {len(raw)} bytes; member CRC verified',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audit_folder',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();fetch(a.audit_folder,a.output)
