import unittest

from research.plot_core_results import observation_rows, one, window_rows


class PlotCoreResultsTests(unittest.TestCase):
    def test_unique_selection_rejects_absent_or_duplicate(self):
        rows = [{"c": "0.5", "L": "128", "condition": "bin4", "t_min": "1000", "t_max": "20000"}]
        self.assertIs(one(rows, c=0.5, L=128, condition="bin4", t_min=1000, t_max=20000), rows[0])
        with self.assertRaises(ValueError):
            one(rows, c=0.15)
        with self.assertRaises(ValueError):
            one(rows + rows, c=0.5)

    def test_window_selector_keeps_all_six_declared_rows(self):
        rows = [dict(c=str(c), L="128", t_min=str(start), t_max="200000", n="8",
                     alpha="0.25", bootstrap_low="0.24", bootstrap_high="0.26")
                for c in (0.5, 0.15) for start in (2, 100, 1000)]
        self.assertEqual(len(window_rows(rows)), 6)
        with self.assertRaises(ValueError):
            window_rows(rows[:-1])

    def test_observation_selector_checks_replica_counts(self):
        def rows(n):
            return [dict(c=str(c), L="128", condition="bin4", t_min="1000", t_max="20000",
                         n=str(n), delta_vs_full="-0.06", delta_low="-0.07", delta_high="-0.05")
                    for c in (0.5, 0.15)]
        self.assertEqual(len(observation_rows(rows(8), rows(4))), 4)
        with self.assertRaises(ValueError):
            observation_rows(rows(8), rows(8))


if __name__ == "__main__":
    unittest.main()
