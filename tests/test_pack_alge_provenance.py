import json
from pathlib import Path
import tempfile
import unittest

from research.build_evidence_pack import (
    verify_alge_audit_provenance,
    verify_alge_figure_provenance,
)
from research.imaging_benchmark import sha


class AlGePackProvenanceTests(unittest.TestCase):
    def test_detects_stale_figure_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = (
                "research/plot_alge_static_operator.py",
                "research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv",
                "research/results/alge_static_operator_2026-09-18/summary.json",
                "figures/fig_alge_fixed_plane_audit.png",
            )
            for relative in paths:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative)
            (root / "figures/fig_alge_fixed_plane_audit.json").write_text(
                json.dumps(dict(
                    source_sha256=sha(root / paths[0]),
                    table_sha256=sha(root / paths[1]),
                    summary_sha256=sha(root / paths[2]),
                ))
            )
            verify_alge_figure_provenance(root)
            (root / paths[1]).write_text("altered")
            with self.assertRaisesRegex(ValueError, "figure provenance"):
                verify_alge_figure_provenance(root)

    def test_detects_changed_source_stack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            methods = ("research/inspect_alge_time_series.py",
                       "research/ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md",
                       "research/alge_static_operator_test.py", "research/imaging.py")
            for relative in methods:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative)
            source = root / "research/runs/alge_time_series_source_v1"
            source.mkdir(parents=True)
            records = []
            for minute in (15, 105, 195, 315):
                path = source / f"ROI_{minute}min.tif"
                path.write_text(path.name)
                records.append(dict(file=path.name, sha256=sha(path)))
            qa_path = root / "research/results/alge_time_series_metadata_qa_2026-09-18/metadata_qa.json"
            qa_path.parent.mkdir(parents=True)
            qa_path.write_text(json.dumps(dict(analysis_source_sha256=sha(root / methods[0]),
                                               records=records)))
            summary = root / "research/results/alge_static_operator_2026-09-18/summary.json"
            summary.parent.mkdir(parents=True)
            summary.write_text(json.dumps(dict(qa_manifest_sha256=sha(qa_path),
                protocol_sha256=sha(root / methods[1]),
                source_sha256={name: sha(root / name) for name in methods[2:]},
                input_tiff_sha256={row["file"]: row["sha256"] for row in records})))
            verify_alge_audit_provenance(root)
            (source / "ROI_15min.tif").write_text("changed")
            with self.assertRaisesRegex(ValueError, "source changed"):
                verify_alge_audit_provenance(root)


if __name__ == "__main__":
    unittest.main()
