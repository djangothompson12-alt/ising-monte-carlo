"""Visual/metadata feasibility review of unregistered original tomography slices.

No phase segmentation, growth-law fit or Ising validation is inferred here.
"""
import argparse
import json
import re
from pathlib import Path
import numpy as np
from PIL import Image
from research.analyse_campaign import plt
from research.imaging_benchmark import sha


def inspect(folder,output):
    if output.exists():raise FileExistsError('Use a new QA folder')
    manifest=json.loads((folder/'manifest.json').read_text())
    if len(manifest['stages'])!=5:raise ValueError('Subset is incomplete')
    output.mkdir(parents=True)
    fig,axes=plt.subplots(2,5,figsize=(15,6),layout='constrained')
    results=[]
    for column,stage in enumerate(manifest['stages']):
        path=folder/stage['path']
        if sha(path)!=stage['sha256']:raise ValueError('Raw slice hash mismatch')
        with Image.open(path) as image:
            x=np.asarray(image)
        if x.ndim!=2 or not np.all(np.isfinite(x)):raise ValueError('Not a finite scalar plane')
        quantiles=np.percentile(x,[1,50,99])
        text='\n'.join(stage['text_metadata'].values())
        voxel=re.search(r'Size of Voxel.*?:\s*([0-9.]+)',text)
        spacing=float(voxel.group(1)) if voxel else None
        axes[0,column].imshow(x,cmap='gray',vmin=quantiles[0],vmax=quantiles[-1])
        axes[0,column].set_title(f'{stage["time_min"]} min; central z={stage["slice_index"]}')
        axes[0,column].set_axis_off()
        axes[1,column].hist(x.ravel(),bins=100,color='#486e87')
        axes[1,column].set(xlabel='Native reconstructed intensity',ylabel='Pixel count',yscale='log')
        results.append(dict(time_min=stage['time_min'],shape=list(x.shape),dtype=str(x.dtype),
            min=float(x.min()),max=float(x.max()),p01_p50_p99=quantiles.tolist(),
            voxel_size_um_from_header=spacing,registered=False,phase_segmentation_validated=False))
    fig.suptitle('AlGe experimental feasibility only — independent 1–99% display scaling per panel; NOT registered sections\nOriginal data: Jonas Fell, Zenodo 14923133, CC-BY-4.0; no kinetics inferred')
    fig.savefig(output/'experimental_feasibility.png',dpi=160);plt.close(fig)
    (output/'QA.json').write_text(json.dumps(dict(input_manifest_sha256=sha(folder/'manifest.json'),
        source_sha256=sha(Path(__file__)),stages=results),indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();inspect(a.folder,a.output)
