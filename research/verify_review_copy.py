"""Check every recorded file in an unpacked private review copy.

This checks file identity, not scientific correctness or package provenance.
It reads without modifying any archive, source file, or result.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


def verify(folder: Path) -> dict:
    folder = folder.resolve()
    manifest = json.loads((folder / "MANIFEST.json").read_text())
    inventory = manifest.get("files")
    if not isinstance(inventory, dict) or not inventory:
        raise ValueError("Review manifest has no file inventory")
    checked = 0
    for name, expected in inventory.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"Unsafe review-manifest path: {name!r}")
        relative = Path(name)
        if (relative.is_absolute() or not relative.parts
                or ".." in relative.parts or relative.parts[0] == "."):
            raise ValueError(f"Unsafe review-manifest path: {name!r}")
        if (not isinstance(expected, str) or len(expected) != 64
                or any(char not in "0123456789abcdef" for char in expected)):
            raise ValueError(f"Invalid digest for: {name}")
        path = folder / relative
        if not path.is_file() or not path.resolve().is_relative_to(folder):
            raise FileNotFoundError(f"Missing or unsafe review file: {name}")
        actual = sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Changed review file: {name}")
        checked += 1
    return {"status": "passed", "files_checked": checked,
            "boundary": "File-integrity check only; not scientific or external validation"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    print(json.dumps(verify(args.folder), indent=2))
