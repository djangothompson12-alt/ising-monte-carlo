"""Replay contracts for the complete known cohort; not a new independent test set."""

import unittest

from research.audit_kinetic_error_budget import DEFAULT_COHORT, analyse, read_rows


class AuditKineticErrorBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = read_rows(DEFAULT_COHORT / "observations.csv")
        cls.fits = read_rows(DEFAULT_COHORT / "fits.csv")

    def test_all_comparisons_reproduce_archived_slopes_without_new_selection(self):
        results, histories = analyse(self.observations, self.fits)
        self.assertEqual(len(results), 72)
        self.assertEqual(len(histories), 72 * 24)
        self.assertTrue(all(r["trajectories"] == 8 and r["retained_points"] == 24 for r in results))
        primary = {r["composition"]: r for r in results if r["factor"] == 4
                   and r["origin"] == 0 and r["stage"] == "matched"}
        self.assertAlmostEqual(primary[.5]["delta"], -.05047, places=5)
        self.assertAlmostEqual(primary[.15]["delta"], -.07651, places=5)
        self.assertTrue(all(abs(r["delta"]) <= r["observed_ratio_envelope_bound"] + 1e-12 for r in results))

    def test_duplicate_or_missing_observations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate archived observation"):
            analyse(self.observations + self.observations[:1], self.fits)
        with self.assertRaisesRegex(ValueError, "Missing or extra observations"):
            analyse(self.observations[1:], self.fits)

    def test_changed_archived_fit_is_not_silently_accepted(self):
        fits = [dict(r) for r in self.fits]
        for row in fits:
            if row["observable"] == "half":
                row["alpha"] = "9.5"
                break
        with self.assertRaisesRegex(ArithmeticError, "differs from the frozen fit"):
            analyse(self.observations, fits)


if __name__ == "__main__":
    unittest.main()
