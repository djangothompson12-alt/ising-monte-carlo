"""The short brief must use the fresh primary comparison, not a stale cohort."""

import json
from pathlib import Path
import tempfile
import unittest

from research.build_fraction_matching_brief import ANALYSIS, ROOT, load_evidence, load_context


class FractionMatchingBriefTests(unittest.TestCase):
    def test_local_context_keeps_campaigns_and_static_fields_separate(self):
        if not (ROOT / "output/fem_mask_audit_2026-09-22_v2/field_summary.csv").exists():
            self.skipTest("Local-only contextual audit output not distributed")
        context = load_context(ROOT)
        self.assertEqual([r["composition"] for r in context["late"]], ["0.5", "0.15"])
        for row in context["late"]:
            self.assertEqual((row["used_t_min"], row["used_t_max"]), ("21336", "1000000"))
        self.assertAlmostEqual(float(context["late"][0]["alpha"]), .3001, places=4)
        self.assertAlmostEqual(float(context["late"][1]["alpha"]), .2811, places=4)
        self.assertLess(float(context["fem"][0][1]["length_change_percent_median"]), 0)
        self.assertGreater(float(context["fem"][1][1]["length_change_percent_median"]), 0)

    def test_current_primary_rows_and_plot_are_consistent(self):
        manifest, primary, curves = load_evidence(ROOT)
        self.assertEqual(manifest["cohort"], "fresh")
        self.assertEqual(len(primary), 2)
        self.assertEqual([float(r["composition"]) for r in primary], [.5, .15])
        for row, (_, points) in zip(primary, curves):
            self.assertEqual(len(points), 24)
            self.assertEqual((points[0][0], points[-1][0]), (1119, 20000))
            self.assertAlmostEqual(float(row["alpha"])-float(row["native_alpha"]),
                                   float(row["delta"]), places=14)
            self.assertLess(float(row["high"]), 0)

    def test_wrong_cohort_is_rejected_before_reading_results(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / ANALYSIS
            folder.mkdir(parents=True)
            (folder / "manifest.json").write_text(json.dumps({
                "cohort":"development", "independent_replica_count":16}))
            with self.assertRaisesRegex(ValueError, "fresh cohort"):
                load_evidence(Path(temp))

    def test_wrong_run_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / ANALYSIS
            folder.mkdir(parents=True)
            (folder / "manifest.json").write_text(json.dumps({
                "cohort":"fresh", "independent_replica_count":32}))
            with self.assertRaisesRegex(ValueError, "fresh cohort"):
                load_evidence(Path(temp))

    def test_changed_frozen_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / ANALYSIS
            folder.mkdir(parents=True)
            (folder / "fits.csv").write_text("changed result")
            (folder / "manifest.json").write_text(json.dumps({
                "cohort":"fresh", "independent_replica_count":16,
                "outputs":{"fits.csv":"0"*64}}))
            with self.assertRaisesRegex(ValueError, "output changed"):
                load_evidence(Path(temp))


if __name__ == "__main__":
    unittest.main()
