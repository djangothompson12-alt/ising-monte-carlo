"""Small shared I/O contracts for the static mask audit, without plotting imports.

The validation conventions are retained from image_audit_report.py. The
historical module and frozen analyses are deliberately left unchanged.
"""

import csv
import hashlib
import math
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty mask-audit table")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Declare a nonempty {label}")
    return value.strip()


def _positive_number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive number")
    return number


def _roi_bounds(value: object, shape: tuple[int, int]) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4 or any(
        isinstance(v, bool) or not isinstance(v, int) for v in value
    ):
        raise ValueError("ROI must be [row_start,row_stop,col_start,col_stop] integers")
    y0, y1, x0, x1 = value
    if y0 < 0 or x0 < 0 or y1 > shape[0] or x1 > shape[1] or y1 - y0 < 4 or x1 - x0 < 4:
        raise ValueError("ROI must lie inside the image and leave at least four pixels per axis")
    return y0, y1, x0, x1
