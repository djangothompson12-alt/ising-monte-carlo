"""Focused-copy safety/navigation tests; not tests of physical applicability."""

import json
from pathlib import Path
import tempfile
import unittest

from research.build_focused_review_bundle import (
    FRESH, compare_replay, copy_context, local_links, redact_campaign_manifest, safe_relative, source_graph)


class FocusedBundleTests(unittest.TestCase):
    def test_context_refuses_unapproved_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("private_notes.md", "../secret", "/etc/passwd"):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "allowlist"):
                    copy_context(root, root / "out", {"context": {"sources": {name: "0"*64}}})
            self.assertFalse((root / "out").exists())

    def test_context_navigation_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / FRESH).mkdir(parents=True)
            (root / "README.md").write_text("[context](CONTEXT.md)")
            (root / FRESH / "report.html").write_text("")
            (root / "CONTEXT.md").write_text("[missing](missing.csv)")
            with self.assertRaisesRegex(ValueError, "CONTEXT"):
                local_links(root)

    def test_replay_comparison_reports_roundoff_not_byte_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "old", Path(tmp) / "new"
            for p in (a, b):
                p.mkdir()
                (p / "observations.csv").write_text("a,b\n1,2\n")
                (p / "manifest.json").write_text("{}\n")
            (a / "fits.csv").write_text("alpha,label\n0.25,outside\n")
            (b / "fits.csv").write_text("alpha,label\n0.25000000000000006,outside\n")
            report = compare_replay(a, b)
            self.assertEqual(report["status"], "passed_numeric")
            self.assertFalse(report["fits_byte_identical"])
            self.assertTrue(report["observations_byte_identical"])
            for replacement in ("0.3,outside", "0.25,within"):
                (b / "fits.csv").write_text("alpha,label\n" + replacement + "\n")
                with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                    compare_replay(a, b)

    def test_redaction_preserves_numeric_identity_and_does_not_mutate_original(self):
        original = {"identity": {"plan": {"replicas": 8}, "sources": {"engine": "hash"}},
                    "git_status": "?? private admissions notes.md", "git_commit": "abc"}
        before = json.dumps(original, sort_keys=True)
        derived, record = redact_campaign_manifest(original)
        self.assertEqual(json.dumps(original, sort_keys=True), before)
        self.assertNotIn("git_status", derived)
        self.assertNotIn("private admissions", json.dumps(derived))
        self.assertEqual(derived["identity"], original["identity"])
        self.assertEqual(derived["git_commit"], "abc")
        self.assertEqual(record["removed_fields"], ["git_status"])
        self.assertTrue(record["numerical_identity_unchanged"])
        self.assertFalse(record["original_manifest_included"])

    def test_safe_paths_reject_traversal_absolute_and_empty(self):
        for value in ("", ".", "../secrets", "/etc/passwd", "a/../b"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_relative(value)
        self.assertEqual(safe_relative("research/file.py"), Path("research/file.py"))

    def test_import_graph_includes_transitive_project_modules_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "research").mkdir()
            (root / "research/main.py").write_text("import numpy\nfrom research.helper import f\n")
            (root / "research/helper.py").write_text("from research.leaf import x\nf=1\n")
            (root / "research/leaf.py").write_text("x=1\n")
            (root / "research/private.py").write_text("secret=1\n")
            self.assertEqual(source_graph(root, {"research/main.py"}), [
                Path("research/helper.py"), Path("research/leaf.py"), Path("research/main.py")])

    def test_import_graph_resolves_from_package_import_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "research").mkdir()
            (root / "model_b").mkdir()
            (root / "research/main.py").write_text("from model_b import kawasaki_engine as engine\n")
            (root / "model_b/kawasaki_engine.py").write_text("x=1\n")
            self.assertIn(Path("model_b/kawasaki_engine.py"),
                          source_graph(root, {"research/main.py"}))

    def test_import_graph_rejects_missing_entry(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            source_graph(Path(tmp), {"research/missing.py"})

    def test_import_graph_rejects_escape_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "copy"
            root.mkdir()
            (base / "external.py").write_text("secret=1\n")
            (root / "linked.py").symlink_to(base / "external.py")
            with self.assertRaises(FileNotFoundError):
                source_graph(root, {"linked.py"})

    def test_local_links_check_md_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / FRESH).mkdir(parents=True)
            (root / "README.md").write_text("[data](data.csv) [outside](https://example.com)\n")
            (root / "data.csv").write_text("a,b\n")
            (root / FRESH / "report.html").write_text('<a href="fits.csv">Fits</a>')
            (root / FRESH / "fits.csv").write_text("x,y\n")
            self.assertEqual(local_links(root)["local_links_checked"], 2)

    def test_local_links_reject_broken_and_outside_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "copy"
            (root / FRESH).mkdir(parents=True)
            (root / FRESH / "report.html").write_text("")
            for target in ("missing.csv", "../outside.csv"):
                (root / "README.md").write_text(f"[bad]({target})")
                with self.subTest(target=target), self.assertRaises(ValueError):
                    local_links(root)


if __name__ == "__main__":
    unittest.main()
