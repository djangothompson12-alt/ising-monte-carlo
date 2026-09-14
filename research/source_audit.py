"""Bounded metadata audit of the candidate AlGe experiment, not a data analysis.

Fetches the public record and optionally a ZIP directory / small text metadata
using validated HTTP ranges. Never downloads an entire multi-GB volume.
"""
import argparse
import io
import json
import urllib.request
import zipfile
from pathlib import Path
from datetime import datetime,timezone

URL='https://zenodo.org/api/records/14923133'


class RemoteRange(io.RawIOBase):
    def __init__(self,url,size,budget=2000000):
        self.url=url;self.size=size;self.position=0;self.remaining=budget
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self,offset,whence=0):
        p=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
        if p<0:raise ValueError('Negative position')
        self.position=p;return p
    def read(self,n=-1):
        if n<0:n=self.size-self.position
        n=min(n,self.size-self.position)
        if n<=0:return b''
        if n>self.remaining:raise ValueError('Metadata transfer budget exceeded')
        start=self.position;end=start+n-1
        request=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}','User-Agent':'IsingResearchSourceAudit/1.0'})
        with urllib.request.urlopen(request,timeout=30) as response:
            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':
                raise ValueError('Server did not honour byte range; full transfer refused')
            data=response.read(n+1)
        if len(data)!=n:raise ValueError('Unexpected range length')
        self.position+=n;self.remaining-=n
        return data


def audit(output,inspect_zip=False):
    if output.exists():raise FileExistsError('Use a new audit folder')
    with urllib.request.urlopen(URL,timeout=30) as response:
        raw=response.read(1000000)
    record=json.loads(raw)
    output.mkdir(parents=True)
    (output/'record.json').write_bytes(raw)
    summary=dict(checked_utc=datetime.now(timezone.utc).isoformat(),record_url=URL,
        doi=record['doi'],license=record['metadata'].get('license'),
        total_bytes=sum(f['size'] for f in record['files']),experimental_analysis_complete=False,
        files=[dict(name=f['key'],bytes=f['size'],checksum=f['checksum'],url=f['links']['self']) for f in record['files']])
    if inspect_zip:
        item=next(f for f in record['files'] if f['key']=='AlGe_15min_rec.zip')
        try:
            remote=RemoteRange(item['links']['self'],item['size'])
            with zipfile.ZipFile(remote) as archive:
                summary['zip_members']=[dict(name=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size) for i in archive.infolist()]
                text_metadata={}
                for info in archive.infolist():
                    if Path(info.filename).suffix.lower() in ('.txt','.json','.xml','.ini','.log') and info.file_size<100000:
                        text_metadata[info.filename]=archive.read(info).decode('utf-8',errors='replace')
                summary['text_metadata']=text_metadata
        except Exception as error:
            summary['inspection_error']=str(error)
    (output/'AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--inspect-zip',action='store_true');a=p.parse_args();audit(a.output,a.inspect_zip)
