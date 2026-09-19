import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from research.external_length_reliability import run


class ExternalReliabilityTests(unittest.TestCase):
    def test_static_intake_and_unknown_labels(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);coords=np.indices((32,32,32));a=(((coords-16)**2).sum(axis=0)<80).astype(np.uint8)
            np.save(root/'mask.npy',a)
            record=dict(id='sphere <test>',path='mask.npy',specimen='synthetic',unit='um',
                roi_reason='test only',phase_definition='binary sphere',mask_authority='synthetic',
                foreground=1,background=0,spacing_zyx=[.1]*3,roi_zyx=[[0,32]]*3)
            plan=dict(source='synthetic test',license='test',records=[record]);p=root/'plan.json';p.write_text(json.dumps(plan))
            run(p,root/'out');m=json.loads((root/'out/manifest.json').read_text())
            self.assertEqual(m['rows'],24)
            self.assertNotIn('path',m['records'][0])
            self.assertIn('sphere &lt;test&gt;',(root/'out/report.html').read_text())
            with self.assertRaises(FileExistsError):run(p,root/'out')
            a[0,0,0]=2;np.save(root/'mask.npy',a)
            with self.assertRaises(ValueError):run(p,root/'bad')


if __name__=='__main__':unittest.main()
