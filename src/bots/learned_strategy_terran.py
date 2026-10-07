"""Scripted Terran primitives driven by a learned strategy head.

Only build targets (except reactive supply) and the attack/hold decision come
from the policy; every decision is recorded in the trace as ``strategy``.
"""
from src.bots.primitive_terran import PrimitiveTerranBot
from src.bots.terran_primitives import scripted_targets
from src.learning.strategy_policy import StrategyPolicy, strategy_features


class LearnedStrategyTerranBot(PrimitiveTerranBot):
    policy_path = None

    async def on_start(self):
        await super().on_start()
        self.policy = StrategyPolicy.load(self.policy_path)
        self.learned_targets, self.learned_attack = None, False

    def strategy_targets(self, state, macro):
        if macro or self.learned_targets is None:
            x = strategy_features(state, self.attacking, self.enemy_race.name, self.types)
            self.learned_targets, self.learned_attack = self.policy.act(x)
            self.strategy_record = dict(targets=self.learned_targets, attack=self.learned_attack)
        # Reactive supply remains a scripted execution assist.
        return dict(self.learned_targets, supply=scripted_targets(state)['supply'])

    def strategy_attack(self, state):
        return self.learned_attack
