import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from research.analyse_images import analyse
from research.segmentation_sensitivity import analyse as analyse_sensitivity


class ImageImportTests(unittest.TestCase):
    def fixture(self,folder):
        image=np.random.default_rng(92).choice([0.,100.],size=(32,32))
        np.save(folder/'synthetic.npy',image)
        document=dict(source='SYNTHETIC UNIT TEST',license='synthetic test fixture',phase_definition='pixels >=50',records=[
            dict(id='test-1',specimen='synthetic',path='synthetic.npy',time=0,time_unit='s',
                pixel_size=.06,length_unit='um',threshold=50,foreground='above')])
        path=folder/'input.json';path.write_text(json.dumps(document))
        return path,document

    def test_calibration_provenance_and_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name);path,_=self.fixture(folder);out=folder/'result';analyse(path,out)
            self.assertIn('um',(out/'measurements.csv').read_text())
            manifest=json.loads((out/'manifest.json').read_text())
            self.assertEqual(len(manifest['image_sha256']['test-1']),64)
            with self.assertRaises(FileExistsError):analyse(path,out)

    def test_missing_source_and_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name);path,doc=self.fixture(folder)
            doc['records'].append(doc['records'][0]);path.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):analyse(path,folder/'result')
            self.assertFalse((folder/'result').exists())
            doc['records']=[];path.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):analyse(path,folder/'empty')

    def test_declared_threshold_sensitivity_keeps_every_threshold(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name)
            image=np.tile(np.array([-1.,-1.,1.,1.,1.,-1.,-1.,1.]),(8,1))
            np.save(folder/'image.npy',image)
            document=dict(source='synthetic test image',license='test only',phase_definition='positive values',records=[
                dict(id='a',specimen='one',path='image.npy',time=0,time_unit='min',pixel_size=1.,
                     length_unit='um',foreground='above',thresholds=[-0.2,0.,0.2])])
            path=folder/'input.json';path.write_text(json.dumps(document));out=folder/'out'
            analyse_sensitivity(path,out)
            rows=(out/'measurements_by_threshold.csv').read_text().strip().splitlines()
            self.assertEqual(len(rows),4)  # Header plus every declared threshold.
            self.assertTrue((out/'threshold_summaries.csv').exists())
            self.assertIn('No threshold is selected automatically',(out/'REPORT.md').read_text())


if __name__=='__main__':unittest.main()
