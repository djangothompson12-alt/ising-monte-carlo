import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from research.fraction_matched_external import run


class ExternalFractionTests(unittest.TestCase):
    def test_user_mask_report_and_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); z,y,x=np.indices((32,32,32))
            data=((z-16)**2+(y-16)**2+(x-16)**2<49).astype(np.uint8); np.save(root/'mask.npy',data)
            record=dict(id='<example>',specimen='synthetic',path='mask.npy',unit='um',spacing_zyx=[.1]*3,
                foreground=1,background=0,roi_zyx=[[0,32]]*3,roi_reason='Complete example',phase_definition='Sphere',mask_authority='Synthetic known mask')
            plan=dict(source='test',license='test',records=[record]); file=root/'plan.json'; file.write_text(json.dumps(plan))
            report=run(file,root/'out')
            self.assertIn('&lt;example&gt;',report.read_text()); self.assertNotIn('<example>',report.read_text())
            manifest=json.loads((root/'out/manifest.json').read_text()); self.assertEqual(manifest['rows'],24)
            self.assertNotIn('path',manifest['records'][0])
            with self.assertRaises(FileExistsError): run(file,root/'out')
            record['spacing_zyx']=[.1,.2,.1]; file.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,'equal'): run(file,root/'bad')
            record['spacing_zyx']=[.1]*3; data[0,0,0]=7; np.save(root/'mask.npy',data); file.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,'undeclared'): run(file,root/'bad')
