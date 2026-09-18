import unittest

from research.inspect_alge_time_series import bounding_box, common_crop


class AlGeMetadataTests(unittest.TestCase):
    def test_parse_bounding_box_and_intersect_grid(self):
        a = bounding_box("BoundingBox 0 12 0 12 0 6\n")
        b = bounding_box("BoundingBox 1.2 13.2 2.4 14.4 0 6")
        area, crops = common_crop([a, b], [(100, 200, 200), (100, 200, 200)])
        self.assertEqual(area["width_pixels"], 180)
        self.assertEqual(area["height_pixels"], 160)
        self.assertEqual(crops[0][0].start, 40)
        self.assertEqual(crops[1][1].start, 0)

    def test_reject_bad_metadata(self):
        with self.assertRaises(ValueError):
            bounding_box("not a box")
        with self.assertRaises(ValueError):
            bounding_box("BoundingBox 2 1 0 1 0 1")


if __name__ == "__main__":
    unittest.main()
