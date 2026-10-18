"""The static audit must not need the simulation or plotting/UI environments."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class MinimalMaskAuditTests(unittest.TestCase):
    def test_demo_and_verification_work_with_optional_stacks_blocked(self):
        root = Path(__file__).resolve().parents[1]
        script = r'''
import builtins
import sys
from pathlib import Path
blocked = {"matplotlib", "numba", "solara", "plotly", "anywidget", "pandas"}
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split(".")[0] in blocked:
        raise ImportError("Optional dependency deliberately unavailable: " + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from research.make_mask_resolution_demo import make
from research.verify_mask_audit_delivery import verify
from research.verify_mask_resolution_audit import run
destination = Path(sys.argv[1])
make(destination / "demo")
result = verify(destination / "demo/audit", input_plan=destination / "demo/input_plan.json",
                require_current_sources=True)
assert result["numerical_tables_replayed"]
assert run(destination / "exact")["measurement_comparisons"] == 324
assert not (blocked & set(sys.modules))
print("minimal-stack workflow passed")
'''
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, "-c", script, folder], cwd=root,
                                    capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("minimal-stack workflow passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
