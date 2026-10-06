import base64
import copy
import unittest

import numpy as np

from src.learning.entity_spatial import spatial_features
from tests import test_entity_spatial


class SourceGeometryTests(unittest.TestCase):
    def setUp(self):
        fixture = test_entity_spatial.EntitySpatialTests()
        fixture.setUp()
        self.state, self.terrain = fixture.state, fixture.terrain
        self.points, self.radii = fixture.points, fixture.radii

    def coarse(self):
        values = np.arange(16, dtype=np.uint8).reshape(4, 4)
        image = dict(
            width=4,
            height=4,
            bits_per_pixel=8,
            data=base64.b64encode(values.tobytes()).decode(),
            coordinate_system="feature_minimap",
            world_size=[10, 6],
            transform="world_y_flip_then_uniform_max_dimension_scale",
        )
        self.terrain["terrain_height"] = image

    def test_coarse_grid_uses_world_flip_uniform_scale_and_exposes_resolution(self):
        self.coarse()
        features = spatial_features(
            self.state, self.terrain, self.points, self.radii, source_geometry=True
        )
        self.assertEqual(features.shape, (2, 401))
        patch = features[0, 2:322].reshape(8, 8, 5)
        self.assertAlmostEqual(patch[1, 2, 0], 5 / 255)
        self.assertAlmostEqual(patch[4, 7, 0], 3 / 255)
        self.assertAlmostEqual(patch[0, 0, 0], 8 / 255)
        np.testing.assert_array_equal(
            features[:, 386:396], [[2.5, 2.5, 1, 1, 1, 1, 1, 1, 1, 1]] * 2
        )
        self.assertEqual(int(features[1, 322:386].sum()), 12)

    def test_native_values_remain_identical_with_explicit_native_resolution(self):
        legacy = spatial_features(self.state, self.terrain, self.points, self.radii)
        new = spatial_features(
            self.state, self.terrain, self.points, self.radii, source_geometry=True
        )
        np.testing.assert_array_equal(new[:, :386], legacy)
        np.testing.assert_array_equal(new[:, 386:396], np.ones((2, 10)))

    def test_unverified_transform_or_wrong_map_identity_is_rejected(self):
        self.coarse()
        for change in (dict(world_size=[12, 6]), dict(transform="unknown")):
            terrain = copy.deepcopy(self.terrain)
            terrain["terrain_height"].update(change)
            with self.assertRaisesRegex(ValueError, "geometry"):
                spatial_features(
                    self.state, terrain, self.points, self.radii, source_geometry=True
                )

    def test_coarse_grids_cannot_silently_enter_legacy_spatial_inputs(self):
        self.coarse()
        with self.assertRaises(ValueError):
            spatial_features(self.state, self.terrain, self.points, self.radii)

    def test_unavailable_terrain_is_masked_and_its_source_bytes_are_not_read(self):
        self.terrain["terrain_height"] = dict(known=False, data="not an image")
        self.terrain.pop("pathing_grid")
        features = spatial_features(
            self.state, self.terrain, self.points, self.radii, source_geometry=True
        )
        patch = features[0, 2:322].reshape(8, 8, 5)
        np.testing.assert_array_equal(patch[:, :, :2], np.zeros((8, 8, 2)))
        np.testing.assert_array_equal(features[:, 386:390], np.zeros((2, 4)))
        np.testing.assert_array_equal(features[:, -5:], [[0, 0, 1, 1, 1]] * 2)
