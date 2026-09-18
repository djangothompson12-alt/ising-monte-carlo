from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.build_extension_review_pack import (
    REVIEW_DOCS, build, check_core_links, selected_files,
)


class ExtensionReviewPackTests(unittest.TestCase):
    def test_pack_refuses_a_path_outside_private_output(self):
        with TemporaryDirectory() as temporary:
            target = Path(temporary) / "review"
            with self.assertRaisesRegex(ValueError, "ignored output"):
                build(target)
            self.assertFalse(target.exists())

    def test_selection_excludes_unrelated_private_and_experimental_inputs(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            required = (
                "README.md", "CLAUDE.md", "EXTERNAL_REVIEW.md", "LICENSE", "CITATION.cff",
                "requirements.txt", "AI_USE_AND_CONTRIBUTIONS.md",
                "model_a/ising_engine.py", "model_b/kawasaki_engine.py",
                "phase_diagram.py", "comparative_analysis.py",
                "manuscript/main.tex", "manuscript/WRITING_GUIDE.md",
                "manuscript/REPORT_DRAFT_2026-09-18.md",
                "experiments/PROTOCOL.md",
                "model_a/figures/fig1_phase_transitions_corrected.png",
                "model_a/figures/fig2_spin_domains.png",
                "model_a/figures/fig3_kinetics_entropy.png",
                "docs/CLAIM_AUDIT_2026-09-17.md",
                "docs/PROGRESS_AND_LIMITS.md", "docs/review_brief.html",
                "docs/LITERATURE_COMPARISON_2026-09-17.md",
                "docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md",
                "docs/SECOND_ASSISTANT_AUDIT_TASK.md",
                "docs/TECHNICAL_REPORT_BACKBONE.md",
                "docs/MEASUREMENT_STUDY_RESULTS.md",
                "docs/OVERNIGHT_RESULTS.md",
            )
            for name in (*required, *(f"docs/{doc}" for doc in REVIEW_DOCS)):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            expected = root / "research/runs/main_065_multisize_v1/c0_L32_rep000.npz"
            expected.parent.mkdir(parents=True)
            expected.write_bytes(b"synthetic fixture")
            private = root / "output/private_contact_notes.md"
            private.parent.mkdir()
            private.write_text("not in the review packet")
            experimental = root / "research/runs/alge_time_series_source_v1/roi.tif"
            experimental.parent.mkdir(parents=True)
            experimental.write_bytes(b"not included")
            selected = selected_files(root)
            self.assertIn(expected, selected)
            self.assertNotIn(private, selected)
            self.assertNotIn(experimental, selected)

    def test_primary_review_link_check_reports_missing_local_target(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("README.md", "EXTERNAL_REVIEW.md",
                         "docs/PROGRESS_AND_LIMITS.md", "docs/START_HERE.md",
                         "docs/review_brief.html"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("working note")
            (root / "README.md").write_text(
                "[stale PDF](manuscript/main.pdf) and [result](docs/result.md)")
            with self.assertRaisesRegex(FileNotFoundError, "Broken review link"):
                check_core_links(root)
            (root / "docs/result.md").write_text("result")
            self.assertEqual(check_core_links(root), 1)


if __name__ == "__main__":
    unittest.main()
