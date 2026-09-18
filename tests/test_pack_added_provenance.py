import json
from pathlib import Path
import tempfile
import unittest

from research.build_evidence_pack import verify_added_figure_sources
from research.imaging_benchmark import sha


class AddedFigureProvenanceTests(unittest.TestCase):
    def test_pack_rejects_stale_input_or_method(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = (
                "research/runs/overnight/analysis/exponents.csv",
                "research/runs/overnight/imaging_v1/paired_fits.csv",
                "research/runs/imaging_validation/imaging_v1/paired_fits.csv",
                "research/plot_core_results.py", "research/synthetic_growth_control.py",
                "research/imaging.py", "research/plot_archived_morphology.py",
                "research/runs/overnight/c0_L128_rep000.npz",
                "research/runs/overnight/c1_L128_rep000.npz",
                "research/paired_window_sensitivity.py",
                "research/analyse_campaign.py",
                "research/runs/overnight/manifest.json",
                "research/runs/overnight/status.json",
            )
            for relative in files:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative)
            figure = root / "figures/fig_core_observation_shift_v1.json"
            figure.parent.mkdir()
            figure.write_text(json.dumps(dict(
                input_sha256={name: sha(root / name) for name in files[:3]},
                source_sha256=sha(root / files[3]),
            )))
            control = root / "research/runs/synthetic_growth_control_v2/provenance.json"
            control.parent.mkdir(parents=True)
            control.write_text(json.dumps(dict(
                source_sha256=sha(root / files[4]), imaging_sha256=sha(root / files[5]),
            )))
            morphology = root / "figures/fig_archived_morphology_v1.json"
            morphology.write_text(json.dumps(dict(
                source_sha256=sha(root / files[6]),
                raw_npz_sha256={Path(name).name: sha(root / name) for name in files[7:9]},
            )))
            paired = root / "research/results/paired_window_sensitivity_2026-09-18/provenance.json"
            paired.parent.mkdir(parents=True)
            paired.write_text(json.dumps(dict(
                source_sha256={name: sha(root / name) for name in files[9:11]},
                input_manifest_sha256=sha(root / files[11]),
                input_status_sha256=sha(root / files[12]),
                input_sha256={Path(name).name: sha(root / name) for name in files[7:9]},
            )))
            verify_added_figure_sources(root)
            (root / files[0]).write_text("changed after figure")
            with self.assertRaisesRegex(ValueError, "stale input"):
                verify_added_figure_sources(root)
            (root / files[0]).write_text(files[0])
            (root / files[7]).write_text("changed after morphology")
            with self.assertRaisesRegex(ValueError, "Morphology figure raw input is stale"):
                verify_added_figure_sources(root)
            (root / files[7]).write_text(files[7])
            (root / files[11]).write_text("changed after paired audit")
            with self.assertRaisesRegex(ValueError, "Paired fitting-window audit provenance is stale"):
                verify_added_figure_sources(root)


if __name__ == "__main__":
    unittest.main()
