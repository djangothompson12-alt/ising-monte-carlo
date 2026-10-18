"""Integrity, exact-input provenance and local replay of an audit handoff."""

import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from research.mask_resolution_audit import _mask_snapshot, audit
from research.verify_mask_audit_delivery import verify
from tests import test_mask_resolution_audit


class MaskAuditDeliveryTests(unittest.TestCase):
    def fixture(self, folder):
        return test_mask_resolution_audit.MaskResolutionAuditTests().fixture(folder)

    def test_clean_delivery_can_be_checked_and_replayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, _ = self.fixture(folder)
            audit(plan, folder / "audit")
            result = verify(folder / "audit", input_plan=plan, require_current_sources=True)
            self.assertEqual(result["output_hashes_verified"], 4)
            self.assertTrue(result["current_sources_match"])
            self.assertTrue(result["numerical_tables_replayed"])
            self.assertNotIn(str(folder), json.dumps(result))
            self.assertFalse(verify(folder / "audit")["numerical_tables_replayed"])

    def test_changed_delivery_or_manifest_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, _ = self.fixture(folder)
            audit(plan, folder / "audit")
            table = folder / "audit" / "measurements.csv"
            table.write_text(table.read_text() + "altered\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify(folder / "audit")
            manifest = folder / "audit" / "manifest.json"
            record = json.loads(manifest.read_text())
            record["output_sha256"]["../not-an-audit-output"] = "0" * 64
            manifest.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "four named audit outputs"):
                verify(folder / "audit")

    def test_rehashing_altered_numbers_is_not_enough_to_pass_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, _ = self.fixture(folder)
            audit(plan, folder / "audit")
            table = folder / "audit" / "measurements.csv"
            rows = table.read_text().splitlines()
            columns = rows[0].split(",")
            # Use DictReader/Writer because the ROI field contains commas.
            import csv
            with table.open(newline="") as stream:
                values = list(csv.DictReader(stream))
            values[0]["length"] = "123.0"
            with table.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                writer.writerows(values)
            manifest = folder / "audit" / "manifest.json"
            record = json.loads(manifest.read_text())
            record["output_sha256"][table.name] = hashlib.sha256(table.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(record))
            self.assertEqual(verify(folder / "audit")["output_hashes_verified"], 4)
            with self.assertRaisesRegex(ValueError, "Replay differs"):
                verify(folder / "audit", input_plan=plan)

    def test_replay_rejects_changed_mask_or_calibration_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, document = self.fixture(folder)
            audit(plan, folder / "audit")
            mask_path = folder / "expert_mask.npy"
            values = np.load(mask_path)
            values[10, 10] = 255 - values[10, 10]
            np.save(mask_path, values)
            with self.assertRaisesRegex(ValueError, "mask hashes differ"):
                verify(folder / "audit", input_plan=plan)
            document["records"][0]["pixel_size"] = .12
            plan.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, "Input plan hash differs"):
                verify(folder / "audit", input_plan=plan)

    def test_old_source_version_is_visible_not_silently_certified_current(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, _ = self.fixture(folder)
            audit(plan, folder / "audit")
            manifest = folder / "audit" / "manifest.json"
            record = json.loads(manifest.read_text())
            record["source_sha256"]["mask_resolution_audit.py"] = "0" * 64
            manifest.write_text(json.dumps(record))
            self.assertFalse(verify(folder / "audit")["current_sources_match"])
            with self.assertRaisesRegex(ValueError, "source version differs"):
                verify(folder / "audit", require_current_sources=True)

    def test_replay_comparison_does_not_lose_relative_accuracy_in_small_units(self):
        from research.verify_mask_audit_delivery import _same_tables
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            before, after = folder / "before.csv", folder / "after.csv"
            before.write_text("id,length\na,1e-20\n")
            after.write_text("id,length\na,2e-20\n")
            with self.assertRaisesRegex(ValueError, "Replay differs"):
                _same_tables(before, after)

    def test_source_change_during_audit_is_rejected_before_output_creation(self):
        import research.mask_resolution_audit as implementation
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, _ = self.fixture(folder)
            original_sha = implementation.sha
            calls = {}
            def changing_source(path):
                count = calls.get(path.name, 0)
                calls[path.name] = count + 1
                if path.name == "mask_resolution_audit.py" and count:
                    return "0" * 64
                return original_sha(path)
            with patch.object(implementation, "sha", side_effect=changing_source):
                with self.assertRaisesRegex(RuntimeError, "sources changed"):
                    audit(plan, folder / "audit")
            self.assertFalse((folder / "audit").exists())

    def test_mask_digest_is_from_the_bytes_loaded_not_a_second_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mask.npy"
            buffer = BytesIO()
            np.save(buffer, np.indices((16, 16)).sum(axis=0) % 2)
            payload = buffer.getvalue()
            with patch.object(Path, "read_bytes", return_value=payload) as read:
                mask, digest = _mask_snapshot(path, 1, 0)
            self.assertEqual(read.call_count, 1)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest())
            self.assertEqual(np.count_nonzero(mask), 128)

    def test_manifest_digest_is_from_the_document_actually_parsed(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan, _ = self.fixture(folder)
            payload = plan.read_bytes()
            from research.mask_resolution_audit import measure as original_measure
            def measure_and_change_plan(*args, **kwargs):
                plan.write_text('{"changed_after_read": true}')
                return original_measure(*args, **kwargs)
            with patch("research.mask_resolution_audit.measure", side_effect=measure_and_change_plan):
                audit(plan, folder / "audit")
            record = json.loads((folder / "audit" / "manifest.json").read_text())
            self.assertEqual(record["input_manifest_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertNotEqual(record["input_manifest_sha256"], hashlib.sha256(plan.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
