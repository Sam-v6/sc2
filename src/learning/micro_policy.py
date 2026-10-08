"""Small learned movement/targeting experiment; not the final full-game policy."""

import json
from pathlib import Path
import numpy as np
from src.learning.gameplay import Command


def combat_view(state):
    """Initial transfer scope: Marines within 15 tiles of a currently visible enemy."""
    enemies = [u for u in state["units"] if u["alliance"] == 4]
    own = [
        u
        for u in state["units"]
        if u["alliance"] == 1
        and u["unit_type"] == 48
        and any(
            sum((a - b) ** 2 for a, b in zip(u["position"][:2], e["position"][:2]))
            <= 225
            for e in enemies
        )
    ]
    return dict(state, units=own + enemies)


def candidates(unit, enemies):
    if not enemies:
        return [], np.empty((0, 12))
    position = np.asarray(unit["position"][:2], dtype=float)
    points = np.asarray([e["position"][:2] for e in enemies])
    distances = np.linalg.norm(points - position, axis=1)
    nearest = int(np.argmin(distances))
    health = unit.get("health", 0.0) / max(unit.get("health_max", 1.0), 1.0)
    cooldown = min(unit.get("weapon_cooldown", 0.0) / 15.0, 2.0)
    commands, features = [], []
    for enemy, distance in zip(enemies, distances):
        commands.append(Command(23, (unit["tag"],), target_unit=enemy["tag"]))
        features.append(
            [
                1.0,
                min(distance / 15.0, 2.0),
                enemy.get("health", 0.0) / 200.0,
                cooldown,
                health,
                min(distances[nearest] / 10.0, 2.0),
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )
    away = position - points[nearest]
    angle = np.arctan2(away[1], away[0])
    for length in (1.5, 3.0):
        for offset in np.arange(8) * np.pi / 4:
            delta = length * np.array([np.cos(angle + offset), np.sin(angle + offset)])
            target = position + delta
            projected = float(np.min(np.linalg.norm(points - target, axis=1)))
            commands.append(Command(16, (unit["tag"],), target_point=tuple(target)))
            features.append(
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    cooldown,
                    health,
                    min(projected / 10.0, 2.0),
                    np.cos(offset),
                    length / 3.0,
                ]
            )
    return commands, np.asarray(features, dtype=float)


class MicroPolicy:
    dimension = 12

    def __init__(self, weights):
        self.weights = np.asarray(weights, dtype=float)
        if (
            self.weights.shape != (self.dimension,)
            or not np.isfinite(self.weights).all()
        ):
            raise ValueError("Expected finite micro policy weights")

    def commands(self, state):
        enemies = [u for u in state["units"] if u["alliance"] == 4]
        result = []
        for unit in (u for u in state["units"] if u["alliance"] == 1):
            choices, features = candidates(unit, enemies)
            if choices:
                result.append(choices[int(np.argmax(features @ self.weights))])
        return result

    def save(self, path, evidence):
        Path(path).write_text(
            json.dumps(
                {
                    "schema": 1,
                    "kind": "linear_combat_candidates",
                    "scope": "movement_and_visible_targeting_only",
                    "weights": self.weights.tolist(),
                    "training": evidence,
                },
                indent=2,
            )
            + "\n"
        )

    @classmethod
    def load(cls, path):
        value = json.loads(Path(path).read_text())
        if value["schema"] != 1 or value["kind"] != "linear_combat_candidates":
            raise ValueError("Unsupported micro checkpoint")
        return cls(value["weights"])


def episode_return(receipt):
    if receipt["status"] not in ("completed", "truncated"):
        raise ValueError("Worker failure is not an RL return")
    score = receipt["score"]
    return (
        score["killed_value"]
        + 0.2 * score["damage_dealt"]
        - 0.5 * score["damage_taken"]
        + receipt["game_seconds"]
        + (1000.0 if receipt["sandbox_result"] == "Victory" else 0.0)
    )


def update_distribution(weights, returns, elite_count):
    """Cross-entropy policy search: refit to parameters with the best episode returns."""
    weights, returns = np.asarray(weights), np.asarray(returns)
    if len(weights) != len(returns) or not 1 <= elite_count <= len(weights):
        raise ValueError("Invalid policy-search batch")
    elite = weights[np.argsort(returns)[-elite_count:]]
    return elite.mean(axis=0), np.maximum(elite.std(axis=0), 0.1)
