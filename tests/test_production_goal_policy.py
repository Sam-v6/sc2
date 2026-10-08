import copy
import unittest
from src.learning.production_goal_policy import current_features


class ProductionGoalFeatureTests(unittest.TestCase):
    def test_masked_fields_and_human_action_history_cannot_change_policy_input(self):
        state = dict(game_loop=100, map_size=[100, 100], player=dict(minerals=50,
                     food_used=12), upgrades=[], units=[dict(tag=1, unit_type=45,
                     alliance=1, position=[20, 20, 0], energy=20)],
                     unknown_fields=dict(player=['food_used'], units=['energy'], world=[]),
                     recent_commands=[])
        first = current_features(state, (60, 4000, 20), {})
        changed = copy.deepcopy(state)
        changed['units'][0]['energy'] = 200
        changed['player']['food_used'] = 200
        changed['recent_commands'] = [dict(game_loop=99, ability=524, units=[1])]
        second = current_features(changed, (60, 4000, 20), {})
        self.assertEqual((first - second).nnz, 0)
