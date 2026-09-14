"""Lossless numeric exports, separate from dashboard display transformations."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np

FIELDS = ('sweep', 'batch_sweeps', 'length_x_sites', 'length_y_sites',
          'delta_energy', 'bath_entropy_flow_per_spin_per_sweep')


def export_zip(records, lattice, metadata):
    """Serialize a paused snapshot. NaNs remain NaNs, signed heat stays signed."""
    table = io.StringIO(newline='')
    writer = csv.DictWriter(table, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(records)
    snapshot = io.BytesIO()
    np.save(snapshot, np.asarray(lattice), allow_pickle=False)
    meta = dict(metadata, exported_utc=datetime.now(timezone.utc).isoformat(),
        format_version=1, units={'length': 'lattice sites', 'time': 'Monte Carlo sweeps', 'energy': 'coupling units, k_B=1'},
        trajectory_kind='Single exploratory live trajectory, not a replica ensemble.',
        seed_scope='Seed describes lattice initialization only; live dynamics RNG state is not recorded. Use research.campaign for reproducible replicas.',
        transformations='None in raw.csv. Dashboard length floors and heat smoothing are not exported. NaN means unresolved threshold crossing.',
        source_sha256={name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                       for name in ('kawasaki_engine.py', 'solara_app.py', 'research_export.py')})
    contents = io.BytesIO()
    with zipfile.ZipFile(contents, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('raw.csv', table.getvalue())
        archive.writestr('snapshot.npy', snapshot.getvalue())
        archive.writestr('metadata.json', json.dumps(meta, indent=2, allow_nan=False))
    return contents.getvalue()
