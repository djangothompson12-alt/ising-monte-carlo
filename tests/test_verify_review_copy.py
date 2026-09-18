"""Tests for the private review-copy integrity reader."""

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from research.verify_review_copy import verify


class ReviewCopyIntegrityTests(unittest.TestCase):
    def test_valid_copy_and_changed_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample = root / "sample.txt"
            sample.write_text("original")
            (root / "MANIFEST.json").write_text(json.dumps({"files": {
                "sample.txt": sha256(sample.read_bytes()).hexdigest()}}))
            self.assertEqual(verify(root)["files_checked"], 1)
            sample.write_text("changed")
            with self.assertRaisesRegex(ValueError, "Changed review file"):
                verify(root)

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "MANIFEST.json").write_text(json.dumps({"files": {
                "../outside": "0" * 64}}))
            with self.assertRaisesRegex(ValueError, "Unsafe review-manifest path"):
                verify(root)


if __name__ == "__main__":
    unittest.main()
