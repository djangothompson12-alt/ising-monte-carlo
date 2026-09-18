"""Finish the two predeclared long campaigns sequentially in bounded blocks.

Run from the repository root with the tested .venv311 Python. The campaign
runner owns source/plan manifests, immutable replicas, and its own run lock.
This queue stops on any failure or on a block that makes no progress.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BLOCK_HOURS = 6
CAMPAIGNS = (
    ("majumder_das_2010_l128", 40),
    ("main_065_multisize_v1", 128),
)


def status_for(name: str) -> dict:
    path = ROOT / "research" / "runs" / name / "status.json"
    return json.loads(path.read_text()) if path.exists() else {}


def run_campaign(name: str, expected: int, env: dict[str, str]) -> None:
    plan = ROOT / "research" / "plans" / f"{name}.json"
    output = ROOT / "research" / "runs" / name
    while True:
        before = status_for(name)
        if before.get("state") == "complete" and before.get("completed") == expected:
            print(f"{name}: already complete ({expected}/{expected})", flush=True)
            return

        completed_before = int(before.get("completed", 0))
        print(f"{name}: starting block at {completed_before}/{expected}", flush=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m", "research.campaign",
                "--plan", str(plan),
                "--output", str(output),
                "--hours", str(BLOCK_HOURS),
            ],
            cwd=ROOT,
            env=env,
            check=False,
        )
        after = status_for(name)
        if result.returncode != 0:
            raise RuntimeError(f"{name}: campaign exited {result.returncode}; status={after}")
        if after.get("total") != expected:
            raise RuntimeError(f"{name}: unexpected job count; status={after}")
        if after.get("state") == "complete" and after.get("completed") == expected:
            print(f"{name}: complete ({expected}/{expected})", flush=True)
            return
        if after.get("state") != "budget_exhausted":
            raise RuntimeError(f"{name}: unexpected status after block: {after}")
        if int(after.get("completed", 0)) <= completed_before:
            raise RuntimeError(f"{name}: block made no completed-replica progress: {after}")


def main() -> None:
    env = os.environ.copy()
    env["NUMBA_CACHE_DIR"] = str(ROOT / ".numba_cache_campaign")
    env["MPLCONFIGDIR"] = str(ROOT / ".mplconfig")
    for name, expected in CAMPAIGNS:
        run_campaign(name, expected, env)
    print("All queued campaigns complete. Analysis has not been run.", flush=True)


if __name__ == "__main__":
    main()
