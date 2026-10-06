"""Execute joint-model commands with causal, model-owned action history."""

from copy import deepcopy

import numpy as np

from src.learning.entity_examples import state_inputs, decode_command
from src.learning.teacher_states import remember_command


def validate_order_aliases(profile, catalog):
    for specific, generic in profile["order_aliases"].items():
        if catalog.get(int(specific), {}).get("remaps_to_ability_id") != generic:
            raise ValueError("Observation order alias differs from engine catalog")


def project_observation(state, profile):
    """Match an explicit partial-source contract without changing the raw trace."""
    if profile is None:
        return state
    projected = deepcopy(state)
    unknown = deepcopy(profile["unknown_fields"])
    # Native dispatched history is known even when the replay history is partial.
    unknown["world"] = [k for k in unknown.get("world", []) if k != "command_history"]
    projected["unknown_fields"] = unknown
    for unit in projected["units"]:
        for order in unit.get("orders", []):
            order["ability_id"] = profile["order_aliases"].get(
                str(order["ability_id"]), order["ability_id"]
            )
    return projected


class JointCommandAgent:
    def __init__(
        self,
        policy,
        vocabulary,
        products,
        terrain=None,
        observation_profile=None,
        ability_seed=None,
    ):
        self.policy = policy
        self.vocabulary = tuple(vocabulary)
        self.products, self.terrain = products, terrain
        self.observation_profile = observation_profile
        self.ability_rng = (
            np.random.default_rng(ability_seed) if ability_seed is not None else None
        )
        self.history = []
        self.next_loop = 0

    def decide(self, state, candidates=None):
        if state["game_loop"] < self.next_loop:
            return None, None
        # PlayerView may contain engine echoes. Only this agent's issued decisions
        # enter the learned history, with roles frozen at their issue time.
        features = project_observation(
            dict(state, recent_commands=self.history[-32:]), self.observation_profile
        )
        inputs = state_inputs(
            features,
            *self.vocabulary,
            products=self.products,
            missing_fields=self.policy.missing_fields,
            terrain=self.terrain if self.policy.spatial_features > 2 else None,
        )
        if candidates is not None:
            indices = {
                tag: i
                for i, tag in enumerate(inputs["tags"])
                if inputs["actor_mask"][i]
            }
            inputs["command_candidates"] = {
                ability: {
                    mode: [indices[tag] for tag in tags if tag in indices]
                    for mode, tags in modes.items()
                }
                for ability, modes in candidates.items()
            }
            inputs["command_candidates"] = {
                a: modes
                for a, modes in inputs["command_candidates"].items()
                if any(modes.values())
            }
        decision = (
            self.policy.predict(inputs, ability_rng=self.ability_rng)
            if self.ability_rng is not None
            else self.policy.predict(inputs)
        )
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


def command_candidates(response, autocast_response, catalog):
    """Engine-derived cast/toggle candidates, including equivalent raw aliases."""

    def canonical(ability):
        return catalog.get(ability, {}).get("remaps_to_ability_id") or ability

    def casters(packet):
        result = {}
        for row in packet.abilities:
            for ability in row.abilities:
                result.setdefault(canonical(ability.ability_id), set()).add(
                    row.unit_tag
                )
        return result

    normal, toggles = casters(response), casters(autocast_response)
    result = {}
    for ability, entry in catalog.items():
        raw = sorted(normal.get(canonical(ability), ()))
        auto = (
            sorted(toggles.get(canonical(ability), ()))
            if entry.get("allow_autocast")
            else []
        )
        if ability and (raw or auto):
            result[ability] = dict(normal=raw, autocast=auto)
    return result


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
