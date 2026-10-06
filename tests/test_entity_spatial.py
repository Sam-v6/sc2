import base64
import unittest

import numpy as np

try:
    from src.learning.entity_spatial import spatial_features
except ImportError:
    spatial_features = None


class EntitySpatialTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(spatial_features, "spatial inputs are missing")
        self.terrain = {}
        self.state = {"map_size": [10, 6], "map": {}}
        for name in (
            "terrain_height",
            "pathing_grid",
            "placement_grid",
            "visibility",
            "creep",
        ):
            values = np.zeros((6, 10), np.uint8)
            values[1, 2] = (
                255 if name == "terrain_height" else 2 if name == "visibility" else 1
            )
            bits = 8 if name in ("terrain_height", "visibility") else 1
            data = (
                values.tobytes() if bits == 8 else np.packbits(values.ravel()).tobytes()
            )
            image = dict(
                width=10,
                height=6,
                bits_per_pixel=bits,
                data=base64.b64encode(data).decode(),
            )
            (self.state["map"] if name in ("visibility", "creep") else self.terrain)[
                name
            ] = image
        self.points = np.array([[4.0, 3.0], [9.0, 3.0]])
        self.radii = np.array([[4.0, 3.0], [1.0, 3.0]])

    def test_pixels_and_padding_are_preserved_in_native_orientation(self):
        features = spatial_features(self.state, self.terrain, self.points, self.radii)
        self.assertEqual(features.shape, (2, 386))
        np.testing.assert_allclose(features[:, :2], [[0.4, 0.5], [0.9, 0.5]])
        patch = features[0, 2:322].reshape(8, 8, 5)
        np.testing.assert_array_equal(patch[1, 2], [1, 1, 1, 1, 1])
        np.testing.assert_array_equal(patch[2, 1], [0, 0, 0, 0, 0])
        masks = features[:, 322:].reshape(2, 8, 8)
        self.assertEqual(int(masks[0].sum()), 48)
        self.assertEqual(int(masks[1].sum()), 12)
        np.testing.assert_array_equal(masks[1][:6, :2], np.ones((6, 2)))
        np.testing.assert_array_equal(masks[1][:, 2:], np.zeros((8, 6)))

    def test_visibility_changes_features_without_discarding_candidates(self):
        first = spatial_features(self.state, self.terrain, self.points, self.radii)
        image = self.state["map"]["visibility"]
        image["data"] = base64.b64encode(bytes([2]) * 60).decode()
        second = spatial_features(self.state, self.terrain, self.points, self.radii)
        self.assertEqual(second.shape, first.shape)
        self.assertGreater(np.linalg.norm(second - first), 0)
        np.testing.assert_array_equal(second[:, :2], first[:, :2])
        np.testing.assert_array_equal(second[:, 322:], first[:, 322:])
