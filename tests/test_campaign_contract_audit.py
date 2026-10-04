import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research import audit_campaign_contracts as audit


class CampaignContractAuditTests(unittest.TestCase):
    def fixture(self,root):
        names=('research/audit_campaign_contracts.py','research/verify_study.py',
               'research/replay_first_energy_interval.py','model_b/kawasaki_engine.py')
        for name in names:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
        folder=root/'research/runs/tiny';folder.mkdir(parents=True)
        (folder/'manifest.json').write_text(json.dumps({'identity':{'sources':{
            'model_b/kawasaki_engine.py':audit.sha(root/'model_b/kawasaki_engine.py')}}}))
        (folder/'c0_L4_rep000.npz').write_bytes(b'fixture checked by mocked verifier')

    def test_first_interval_status_is_updated_only_after_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            with patch.object(audit,'ROOT',root),patch.object(audit,'CAMPAIGNS',(('tiny','.'),)),\
                 patch.object(audit,'verify',return_value=dict(replicas=1,snapshots=2,first_energy_interval_independently_checked=False)),\
                 patch.object(audit,'replay_file',return_value=(-4.,-4.)):
                result=audit.run(root/'result.json')
            self.assertEqual(result['replicas'],1)
            self.assertTrue(result['campaigns'][0]['first_energy_interval_independently_checked'])
            self.assertEqual(result['campaigns'][0]['first_interval_max_absolute_energy_difference'],0)

    def test_failed_replay_does_not_write_success_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root);out=root/'result.json'
            with patch.object(audit,'ROOT',root),patch.object(audit,'CAMPAIGNS',(('tiny','.'),)),\
                 patch.object(audit,'verify',return_value={}),\
                 patch.object(audit,'replay_file',side_effect=ValueError('energy mismatch')):
                with self.assertRaisesRegex(ValueError,'energy mismatch'):audit.run(out)
            self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
