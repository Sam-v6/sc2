"""Learned strategy head plus searched per-race offsets (src.learning.strategy_offsets)."""
import numpy as np

from src.bots.learned_strategy_terran import LearnedStrategyTerranBot
from src.learning.strategy_offsets import apply_offsets


class SearchedStrategyTerranBot(LearnedStrategyTerranBot):
    offsets = None  # {race: {'offsets': [[...]], 'attack': [hold, force]}} as JSON lists

    async def on_start(self):
        await super().on_start()
        self.params = {race: {k: np.asarray(v, dtype=float) for k, v in p.items()}
                       for race, p in self.offsets.items()}

    def strategy_targets(self, state, macro):
        targets = super().strategy_targets(state, macro)
        if macro or not hasattr(self, 'searched_attack'):
            self.searched_targets, self.searched_attack = apply_offsets(
                self.learned_targets, self.learned_attack, self.params, self.enemy_race.name,
                state['game_loop'] / 22.4, state['player']['food_army'])
            self.strategy_record = dict(self.strategy_record, searched_targets=self.searched_targets,
                                        searched_attack=self.searched_attack)
        return dict(self.searched_targets, supply=targets['supply'])

    def strategy_attack(self, state):
        return self.searched_attack
