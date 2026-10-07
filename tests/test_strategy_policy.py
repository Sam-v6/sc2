import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.bots.terran_primitives import scripted_targets
from src.learning.strategy_policy import (
    HEADS, StrategyPolicy, decode_targets, encode_targets, strategy_features)

TYPES = {
    45: dict(unit_id=45, attributes=[1, 3, 4], mineral_cost=50, vespene_cost=0, food_required=1.0, race=1),
    48: dict(unit_id=48, attributes=[1, 3], mineral_cost=50, vespene_cost=0, food_required=1.0, race=1),
    21: dict(unit_id=21, attributes=[2, 4, 8], mineral_cost=150, vespene_cost=0, race=1),
    18: dict(unit_id=18, attributes=[2, 4, 8], mineral_cost=400, vespene_cost=0, race=1),
    108: dict(unit_id=108, attributes=[1, 3], mineral_cost=100, vespene_cost=100, food_required=2.0,
              race=2, weapons=[dict(type=3)]),
    104: dict(unit_id=104, attributes=[1, 3, 4], mineral_cost=50, vespene_cost=0, food_required=1.0, race=2),
}


def state(loop=4480, **player):
    own = [dict(alliance=1, unit_type=45, tag=i, build_progress=1.0) for i in range(30)]
    own += [dict(alliance=1, unit_type=18, tag=100, build_progress=1.0),
            dict(alliance=1, unit_type=21, tag=101, build_progress=1.0),
            dict(alliance=1, unit_type=21, tag=102, build_progress=.5),
            dict(alliance=1, unit_type=48, tag=103, build_progress=1.0, health=45)]
    visible = [dict(alliance=4, unit_type=108, tag=200, is_flying=True, display_type=1)]
    memory = [dict(tag=200, unit_type=108, last_seen_loop=loop),
              dict(tag=201, unit_type=104, last_seen_loop=loop - 3000),
              dict(tag=202, unit_type=21, last_seen_loop=None)]  # fog snapshot, never seen
    return dict(game_loop=loop, units=own + visible, memory=memory,
                player=dict(dict(minerals=300, vespene=100, food_used=31, food_cap=39), **player))


class StrategyPolicyTests(unittest.TestCase):
    def test_features_are_fixed_length_finite_and_fog_safe(self):
        a = strategy_features(state(), False, 'Zerg', TYPES)
        self.assertEqual(a.dtype, np.float32)
        self.assertTrue(np.isfinite(a).all())
        b = strategy_features(state(), True, 'Protoss', TYPES)
        self.assertEqual(a.shape, b.shape)
        self.assertFalse(np.array_equal(a, b))
        # Removing the remembered enemy changes the enemy block only.
        s = state()
        s['memory'] = []
        s['units'] = [u for u in s['units'] if u['alliance'] != 4]
        self.assertFalse(np.array_equal(strategy_features(s, False, 'Zerg', TYPES), a))

    def test_scripted_targets_round_trip_through_heads(self):
        targets = scripted_targets(state())
        self.assertEqual(decode_targets(encode_targets(targets, True)), (
            {k: v for k, v in targets.items() if k != 'supply'}, True))

    def test_out_of_range_targets_are_clipped_to_head_bounds(self):
        targets = dict(scripted_targets(state()), workers=200, tanks=-3)
        decoded, _ = decode_targets(encode_targets(targets, False))
        self.assertEqual(decoded['workers'], HEADS['workers'][-1])
        self.assertEqual(decoded['tanks'], HEADS['tanks'][0])

    def test_greedy_policy_round_trips_through_npz(self):
        rng = np.random.default_rng(0)
        x = strategy_features(state(), False, 'Zerg', TYPES)
        policy = StrategyPolicy.initialize(x.size, hidden=8, rng=rng)
        before = policy.act(x)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'policy.npz'
            policy.save(path)
            loaded = StrategyPolicy.load(path)
        self.assertEqual(loaded.act(x), before)
        targets, attack = before
        self.assertEqual(set(targets), set(HEADS) - {'attack'})
        self.assertIsInstance(attack, bool)

    def test_sampling_is_seeded_and_returns_choice_indices(self):
        x = strategy_features(state(), False, 'Zerg', TYPES)
        policy = StrategyPolicy.initialize(x.size, hidden=8, rng=np.random.default_rng(0))
        a = policy.sample(x, np.random.default_rng(3))
        b = policy.sample(x, np.random.default_rng(3))
        self.assertEqual(a, b)
        self.assertEqual(set(a[2]), set(HEADS))


    def test_trace_examples_label_targets_and_carry_attack_hysteresis(self):
        from src.learning.strategy_imitation import trace_examples
        frames = []
        for loop, marines in ((24, 0), (48, 40), (72, 25), (96, 10)):
            s = state(loop)
            s['units'] = [u for u in s['units'] if u['unit_type'] != 48]
            s['units'] += [dict(alliance=1, unit_type=48, tag=500 + i, build_progress=1.0, health=45)
                           for i in range(marines)]
            frames.append(dict(loop=loop, observation=s, targets=scripted_targets(s)))
            frames.append(dict(loop=loop + 8, observation=None, targets=None))
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'game.primitives.jsonl.gz'
            with gzip.open(path, 'wt') as f:
                f.writelines(json.dumps(frame) + '\n' for frame in frames)
            x, y = trace_examples(path, 'Zerg', TYPES)
        self.assertEqual(x.shape[0], 4)
        self.assertEqual([HEADS['attack'][i] for i in y['attack']], [False, True, True, False])
        self.assertEqual(x[2, 5], 1.0)  # previous attack flag feeds the next decision
        self.assertEqual(HEADS['workers'][y['workers'][0]], scripted_targets(frames[0]['observation'])['workers'])


if __name__ == '__main__':
    unittest.main()
