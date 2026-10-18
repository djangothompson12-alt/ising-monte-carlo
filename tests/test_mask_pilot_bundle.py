"""The local pilot copy must be small, explicit and free of original microscopy."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from research.build_mask_pilot_bundle import SOURCES, build


class MaskPilotBundleTests(unittest.TestCase):
    def test_explicit_copy_and_every_member_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "bundle"
            result = build(output)
            with zipfile.ZipFile(result["archive"]) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
                self.assertEqual(names, set(manifest["members_sha256"]) | {"BUNDLE_MANIFEST.json"})
                for name, digest in manifest["members_sha256"].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                self.assertTrue(set(SOURCES) <= names)
                self.assertTrue(all(not name.startswith("/") and ".." not in Path(name).parts
                                    for name in names))
                masks = {name for name in names if name.endswith(".npy")}
                self.assertEqual(masks, {"synthetic_demo/synthetic_mask.npy", "synthetic_demo/empty_mask.npy"})
                self.assertNotIn("AGENTS.md", names)
                self.assertNotIn("docs/admissions_and_external_validation_strategy.md", names)
                self.assertLess(result["bytes"], 250000)
                self.assertIn("substantial Codex AI", archive.read("README.md").decode())
            with self.assertRaises(FileExistsError):
                build(output)


if __name__ == "__main__":
    unittest.main()
