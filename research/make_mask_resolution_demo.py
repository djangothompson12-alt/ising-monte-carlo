"""Make a deterministic, synthetic demonstration of the mask-audit workflow.

The circles are constructed pixels, not a micrograph, alloy or Kawasaki run.
Use this only to inspect input/output format and failure handling.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from research.mask_resolution_audit import audit


def make(output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new demo folder; do not overwrite an earlier one")
    y, x = np.indices((128, 128))
    foreground = (((x - 37) ** 2 + (y - 43) ** 2 <= 17 ** 2)
                  | ((x - 89) ** 2 + (y - 84) ** 2 <= 22 ** 2))
    output.mkdir(parents=True)
    np.save(output / "synthetic_mask.npy", foreground.astype(np.uint8))
    np.save(output / "empty_mask.npy", np.zeros((128, 128), dtype=np.uint8))
    plan = dict(
        source="Deterministic artificial two-circle example; not materials data",
        license="Synthetic demonstration generated in this repository",
        phase_definition="white artificial circles, not physical precipitates",
        tie_rule="background",
        records=[
            dict(id="synthetic_circles", specimen_id="first artificial image",
                 mask_path="synthetic_mask.npy", foreground_value=1,
                 background_value=0,
                 mask_authority="analytic circle equations in demo source",
                 roi=[0, 128, 0, 128],
                 roi_reason="entire artificial field, fixed before audit",
                 pixel_size=1, length_unit="arbitrary pixel units"),
            dict(id="empty_field", specimen_id="second artificial image",
                 mask_path="empty_mask.npy", foreground_value=1,
                 background_value=0,
                 mask_authority="analytic all-background field in demo source",
                 roi=[0, 128, 0, 128],
                 roi_reason="entire artificial field, fixed before audit",
                 pixel_size=1, length_unit="arbitrary pixel units"),
        ],
    )
    (output / "input_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    return audit(output / "input_plan.json", output / "audit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(make(args.output))
