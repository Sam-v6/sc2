"""Execute joint-model commands with causal, model-owned action history."""

from src.learning.entity_examples import state_inputs, decode_command
from src.learning.teacher_states import remember_command


class JointCommandAgent:
    def __init__(self, policy, vocabulary, products, terrain=None):
        self.policy = policy
        self.vocabulary = tuple(vocabulary)
        self.products, self.terrain = products, terrain
        self.history = []
        self.next_loop = 0

    def decide(self, state):
        if state["game_loop"] < self.next_loop:
            return None, None
        # PlayerView may contain engine echoes. Only this agent's issued decisions
        # enter the learned history, with roles frozen at their issue time.
        features = dict(state, recent_commands=self.history[-32:])
        inputs = state_inputs(
            features,
            *self.vocabulary,
            products=self.products,
            missing_fields=self.policy.missing_fields,
            terrain=self.terrain if self.policy.spatial_features > 2 else None,
        )
        decision = self.policy.predict(inputs)
        if decision is None:
            return None, None
        return decode_command(decision, inputs), decision["delay"]

    def record_issued(self, command, state, delay):
        self.history.append(
            remember_command(command.as_dict(), state, state["game_loop"])
        )
        self.history = self.history[-32:]
        # This first live adapter issues one command per observation. Zero delay
        # advances one loop; same-observation batching remains future work.
        self.next_loop = state["game_loop"] + max(1, delay)


def command_available(command, response, catalog):
    """Check unit-command castability; autocast toggles remain engine-validated."""
    if command.autocast:
        return True

    def canonical(ability):
        return catalog.get(ability, {}).get("remaps_to_ability_id") or ability

    available = {
        row.unit_tag: {canonical(a.ability_id) for a in row.abilities}
        for row in response.abilities
    }
    return all(
        canonical(command.ability) in available.get(tag, set()) for tag in command.units
    )
