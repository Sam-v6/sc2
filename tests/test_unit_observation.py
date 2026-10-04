import unittest
from types import SimpleNamespace as NS
import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as U
from src.rl.unit_observation import observe_units, FEATURES, TYPE_IDS, CHANNELS


def unit(kind=U.MARINE, x=10, y=10, health=45, ground=6, snapshot=False):
    return NS(type_id=kind, position=NS(x=x,y=y), health=health, shield=0,
              ground_dps=ground, air_dps=0, is_flying=False, is_structure=False,
              detect_range=0, is_cloaked=False, is_snapshot=snapshot,
              is_visible=not snapshot)


class UnitObservationTests(unittest.TestCase):
    def test_type_health_capability_position_and_side_are_distinguishable(self):
        bounds=NS(x=0,y=0,width=80,height=80)
        original=observe_units([], [unit()], bounds)
        variants=[unit(kind=U.ZERGLING),unit(health=20),unit(ground=0),unit(x=60)]
        for variant in variants:
            self.assertFalse(np.array_equal(original,observe_units([], [variant],bounds)))
        self.assertFalse(np.array_equal(original,observe_units([unit()],[],bounds)))
        self.assertEqual(original.shape,(len(FEATURES),))
        self.assertTrue(np.isfinite(original).all())

    def test_permutation_invariance_and_playable_edges(self):
        bounds=NS(x=20,y=30,width=80,height=80)
        units=[unit(x=20,y=30),unit(x=100,y=110),unit(x=-1,y=200)]
        np.testing.assert_array_equal(observe_units(units,[],bounds),observe_units(units[::-1],[],bounds))
        observed=observe_units(units,[],bounds)
        self.assertAlmostEqual(observed[FEATURES.index('own_cell_0_0_count')],1/40)
        self.assertAlmostEqual(observed[FEATURES.index('own_cell_7_7_count')],1/40)
        self.assertAlmostEqual(observed[FEATURES.index('own_cell_7_0_count')],1/40)

    def test_snapshot_and_visible_counts_are_distinct(self):
        bounds=NS(x=0,y=0,width=80,height=80)
        visible=observe_units([], [unit()], bounds)
        remembered=observe_units([], [unit(snapshot=True)], bounds)
        self.assertFalse(np.array_equal(visible,remembered))
        self.assertEqual(remembered[FEATURES.index('enemy_cell_1_1_visible')],0)
        self.assertEqual(remembered[FEATURES.index('enemy_cell_1_1_snapshots')],1/40)

    def test_schema_covers_protocol_types_and_empty_unknown_space_is_zero(self):
        bounds=NS(x=0,y=0,width=80,height=80)
        self.assertEqual(TYPE_IDS,list(U))
        np.testing.assert_array_equal(observe_units([],[],bounds),np.zeros(len(FEATURES)))
        swarm=observe_units([], [unit()]*100,bounds)
        self.assertLessEqual(swarm.max(),2)
