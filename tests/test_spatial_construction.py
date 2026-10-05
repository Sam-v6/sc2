import base64
import unittest
import numpy as np


class SpatialConstructionTests(unittest.TestCase):
    def test_uniform_candidates_cover_map_and_keep_footprint_alignment(self):
        from src.learning.spatial_construction import spatial_candidates

        points = spatial_candidates([88, 96], 2.5)
        self.assertTrue(np.all(points >= 0))
        self.assertTrue(np.all(points < [88, 96]))
        self.assertLess(np.linalg.norm(points - [60.5, 36.5], axis=1).min(), 3.0)
        np.testing.assert_allclose(points % 1, 0.5)
        np.testing.assert_allclose(spatial_candidates([88, 96], 1.0) % 1, 0.0)

    def test_grid_pixels_use_native_y_x_orientation_and_big_endian_bits(self):
        from src.learning.spatial_construction import decode_terrain

        image = {
            "width": 4,
            "height": 2,
            "bits_per_pixel": 1,
            "data": base64.b64encode(bytes([128])).decode(),
        }
        terrain = decode_terrain({"placement_grid": image})
        self.assertEqual(terrain["placement_grid"][0, 0], 1)
        self.assertEqual(terrain["placement_grid"][1, 0], 0)
