"""Package each tile as a 3MF project: one object, two parts (black base,
white squares), centred on a 270 x 270 mm bed. Parts carry extruder 1 and 2
in the Orca/Bambu-style model_settings.config that QIDI Studio reads, so a
QIDI Box can print both colours unattended; on a single spool, add one colour
change at the first layer above the base.

Usage: python -m research.print_test.make_3mf --out output/print_test_3mf
"""
import argparse
import zipfile
from pathlib import Path

import numpy as np

from research.print_test.make_tiles import (BASE_MM, RAISE_MM, RUN_DIR,
                                            SOURCES, TIMES, slab_mesh,
                                            tile_layout)

BED = 270.0

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="config" ContentType="text/xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


def indexed(tris):
    """Deduplicate triangle corners into a vertex list and index triples."""
    pts = np.round(tris.reshape(-1, 3).astype(float), 4)
    verts, inverse = np.unique(pts, axis=0, return_inverse=True)
    return verts, inverse.reshape(-1, 3)


def mesh_xml(object_id, name, tris):
    verts, faces = indexed(tris)
    v = '\n'.join(f'<vertex x="{x:g}" y="{y:g}" z="{z:g}"/>' for x, y, z in verts)
    f = '\n'.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return (f'<object id="{object_id}" name="{name}" type="model"><mesh>'
            f'<vertices>\n{v}\n</vertices><triangles>\n{f}\n</triangles>'
            f'</mesh></object>')


def model_xml(tile_id, base_tris, white_tris, size_mm):
    offset = (BED - size_mm) / 2
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Title">{tile_id}</metadata>
 <resources>
{mesh_xml(1, 'base_black', base_tris)}
{mesh_xml(2, 'squares_white', white_tris)}
<object id="3" name="{tile_id}" type="model"><components>
 <component objectid="1"/>
 <component objectid="2"/>
</components></object>
 </resources>
 <build>
  <item objectid="3" transform="1 0 0 0 1 0 0 0 1 {offset:g} {offset:g} 0"/>
 </build>
</model>
"""


def settings_xml(tile_id):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="3">
    <metadata key="name" value="{tile_id}"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="base_black"/>
      <metadata key="extruder" value="1"/>
    </part>
    <part id="2" subtype="normal_part">
      <metadata key="name" value="squares_white"/>
      <metadata key="extruder" value="2"/>
    </part>
  </object>
</config>
"""


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for comp, name in SOURCES.items():
        data = np.load(RUN_DIR / name)
        for t in TIMES:
            i = int(np.flatnonzero(data['t'] == t)[0])
            white = tile_layout(data['snapshots'][i].astype(float))
            tile_id = f'{comp}_t{t:05d}'
            base = slab_mesh(np.ones_like(white), 0.0, BASE_MM)
            top = slab_mesh(white, BASE_MM, BASE_MM + RAISE_MM)
            path = out / f'{tile_id}.3mf'
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('[Content_Types].xml', CONTENT_TYPES)
                z.writestr('_rels/.rels', RELS)
                z.writestr('3D/3dmodel.model',
                           model_xml(tile_id, base, top, white.shape[0]))
                z.writestr('Metadata/model_settings.config', settings_xml(tile_id))
            written.append(path)
    return written


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=Path('output/print_test_3mf'))
    for path in build(p.parse_args().out):
        print(path, path.stat().st_size // 1024, 'KB')
