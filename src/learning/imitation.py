"""CPU-only factorized behavior cloning of raw commands from individual entities."""

import json
from pathlib import Path
import numpy as np

DELAYS = np.array([1, 4, 8, 16, 32, 64, 128, 256, 512, 1024])


def unit_features(state, unit, unit_types):
    lookup = {kind: index for index, kind in enumerate(unit_types)}
    n = len(unit_types)
    categorical = np.zeros(3 * n, dtype=np.float32)
    if unit["unit_type"] in lookup:
        categorical[lookup[unit["unit_type"]]] = 1.0
    for other in state["units"]:
        if other["alliance"] == 1 and other["unit_type"] in lookup:
            categorical[n + lookup[other["unit_type"]]] += 0.05
    enemies = [e for e in state["units"] if e["alliance"] == 4]
    enemy = (
        min(
            enemies,
            key=lambda e: sum(
                (a - b) ** 2 for a, b in zip(e["position"][:2], unit["position"][:2])
            ),
        )
        if enemies
        else None
    )
    if enemy and enemy["unit_type"] in lookup:
        categorical[2 * n + lookup[enemy["unit_type"]]] = 1.0
    p = state["player"]
    orders = unit.get("orders", [])
    age = 1.0
    for command in reversed(state.get("recent_commands", [])):
        if unit["tag"] in command["units"]:
            age = min((state["game_loop"] - command["game_loop"]) / 224.0, 2.0)
            break
    x, y = unit["position"][:2]
    ex, ey = enemy["position"][:2] if enemy else (x, y)
    values = [
        p.get("minerals", 0) / 2000.0,
        p.get("vespene", 0) / 1000.0,
        p.get("food_used", 0) / 200.0,
        p.get("food_cap", 0) / 200.0,
        p.get("food_workers", 0) / 80.0,
        p.get("food_army", 0) / 200.0,
        state["game_loop"] / 30000.0,
        x / 256.0,
        y / 256.0,
        unit.get("health", 0) / max(unit.get("health_max", 1), 1),
        unit.get("shield", 0) / 500.0,
        unit.get("energy", 0) / 200.0,
        unit.get("weapon_cooldown", 0) / 64.0,
        unit.get("build_progress", 1.0),
        float(unit.get("is_flying", False)),
        len(orders) / 5.0,
        orders[0].get("progress", 0.0) if orders else 0.0,
        unit.get("assigned_harvesters", 0) / 24.0,
        unit.get("ideal_harvesters", 0) / 24.0,
        (ex - x) / 128.0,
        (ey - y) / 128.0,
        enemy.get("health", 0) / 500.0 if enemy else 0.0,
        enemy.get("shield", 0) / 500.0 if enemy else 0.0,
        float(bool(enemy)),
        age,
        float(unit.get("observed", True)),
        min(
            (state["game_loop"] - unit.get("last_seen_loop", state["game_loop"]))
            / 224.0,
            2.0,
        ),
    ]
    return np.concatenate((np.clip(values, -2.0, 2.0), categorical)).astype(np.float32)


def action_labels(command, state, unit, unit_types, delay):
    labels = {
        "ability": 0,
        "mode": 0,
        "target_type": -1,
        "alliance": -1,
        "queue": 0,
        "delay": -1,
        "point_valid": 0,
    }
    point = np.zeros(2, dtype=np.float32)
    if command is None:
        return labels, point
    labels.update(
        ability=command["ability"],
        queue=int(command["queue"]),
        delay=int(np.argmin(abs(DELAYS - delay))) if delay is not None else -1,
    )
    if command["autocast"]:
        labels["mode"] = 3
    elif command["target_unit"] is not None:
        labels["mode"] = 2
        target = next(
            (u for u in state["units"] if u["tag"] == command["target_unit"]), None
        )
        if target:
            labels["point_valid"] = 1
            labels["target_type"] = (
                unit_types.index(target["unit_type"]) + 1
                if target["unit_type"] in unit_types
                else 0
            )
            labels["alliance"] = target["alliance"]
            point = (np.asarray(target["position"][:2]) - unit["position"][:2]) / 128.0
    elif command["target_point"] is not None:
        labels["mode"] = 1
        labels["point_valid"] = 1
        point = (np.asarray(command["target_point"]) - unit["position"][:2]) / 128.0
    return labels, np.asarray(point, dtype=np.float32)


def softmax(logits):
    weights = np.exp(logits - logits.max(axis=1, keepdims=True))
    return weights / weights.sum(axis=1, keepdims=True)


class FactorPolicy:
    def __init__(
        self,
        features,
        abilities,
        unit_types,
        seed=7,
        extra_sizes=None,
        point_dimensions=2,
        autoregressive=False,
    ):
        self.unit_types = list(unit_types)
        self.autoregressive = autoregressive
        self.feature_mean = np.zeros(features, dtype=np.float32)
        self.feature_scale = np.ones(features, dtype=np.float32)
        self.sizes = {
            "ability": abilities,
            "mode": 4,
            "target_type": len(unit_types) + 1,
            "alliance": 5,
            "queue": 2,
            "delay": len(DELAYS),
        }
        self.sizes.update(extra_sizes or {})
        rng = np.random.default_rng(seed)
        hidden = 32
        self.parameters = {
            "input": rng.normal(0, 1 / np.sqrt(features), (features, hidden)).astype(
                np.float32
            ),
            "bias": np.zeros(hidden, dtype=np.float32),
        }
        for name, size in dict(self.sizes, point=point_dimensions).items():
            self.parameters[name] = rng.normal(0, 0.01, (hidden, size)).astype(
                np.float32
            )
            self.parameters[name + "_bias"] = np.zeros(size, dtype=np.float32)
        if autoregressive:
            self.parameters["ability_embedding"] = rng.normal(
                0, 0.1, (abilities, hidden)
            ).astype(np.float32)
        self.m = {k: np.zeros_like(v) for k, v in self.parameters.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.parameters.items()}
        self.updates = 0

    def predict(self, x, abilities=None):
        x = (np.asarray(x) - self.feature_mean) / self.feature_scale
        hidden = np.tanh(x @ self.parameters["input"] + self.parameters["bias"])
        ability_logits = (
            hidden @ self.parameters["ability"] + self.parameters["ability_bias"]
        )
        selected = (
            ability_logits.argmax(axis=1)
            if abilities is None
            else np.asarray(abilities)
        )
        arguments = (
            np.tanh(hidden + self.parameters["ability_embedding"][selected])
            if self.autoregressive
            else hidden
        )
        output = {
            name: arguments @ self.parameters[name] + self.parameters[name + "_bias"]
            for name in dict(self.sizes, point=2)
            if name != "ability"
        }
        return dict(output, ability=ability_logits)

    def command_context(self, x, ability):
        normalized = (np.asarray(x) - self.feature_mean) / self.feature_scale
        hidden = np.tanh(
            normalized @ self.parameters["input"] + self.parameters["bias"]
        )
        return (
            np.tanh(hidden + self.parameters["ability_embedding"][ability])
            if self.autoregressive
            else hidden
        )

    def gradients(self, x, labels, points, weights=None):
        weights = np.ones(len(x)) if weights is None else np.asarray(weights)
        x = (np.asarray(x) - self.feature_mean) / self.feature_scale
        hidden = np.tanh(x @ self.parameters["input"] + self.parameters["bias"])
        arguments = (
            np.tanh(hidden + self.parameters["ability_embedding"][labels["ability"]])
            if self.autoregressive
            else hidden
        )
        back = np.zeros_like(hidden)
        argument_back = np.zeros_like(hidden)
        gradients = {}
        loss = 0.0
        for name, size in self.sizes.items():
            head_input = hidden if name == "ability" else arguments
            logits = (
                head_input @ self.parameters[name] + self.parameters[name + "_bias"]
            )
            target = np.asarray(labels[name])
            valid = target >= 0
            delta = np.zeros_like(logits)
            if valid.any():
                probability = softmax(logits[valid])
                indices = np.arange(valid.sum())
                norm = weights[valid].sum()
                loss -= float(
                    (
                        np.log(np.maximum(probability[indices, target[valid]], 1e-12))
                        * weights[valid]
                    ).sum()
                    / norm
                )
                probability[indices, target[valid]] -= 1.0
                delta[valid] = probability * weights[valid, None] / norm
            gradients[name] = head_input.T @ delta
            gradients[name + "_bias"] = delta.sum(axis=0)
            if name == "ability":
                back += delta @ self.parameters[name].T
            else:
                argument_back += delta @ self.parameters[name].T
        output = arguments @ self.parameters["point"] + self.parameters["point_bias"]
        valid = np.isfinite(points)
        valid[:, :2] &= np.asarray(
            labels.get(
                "point_valid",
                (np.asarray(labels["mode"]) == 1) | (np.asarray(labels["mode"]) == 2),
            ),
            dtype=bool,
        )[:, None]
        delta = np.zeros_like(output)
        if valid.any():
            error = np.where(valid, output - np.nan_to_num(points), 0.0)
            norm = weights[valid.any(axis=1)].sum()
            coordinate_loss = 0.5 * np.square(error)
            slope = error.copy()
            spatial = error[:, : min(4, output.shape[1])]
            # Positions are measured in 128-tile units. Balance their loss against
            # categorical heads, while bounding influence of distant target errors.
            absolute = np.abs(spatial)
            coordinate_loss[:, : spatial.shape[1]] = 100 * np.where(
                absolute <= 0.05, 0.5 * np.square(spatial), 0.05 * (absolute - 0.025)
            )
            slope[:, : spatial.shape[1]] = 100 * np.clip(spatial, -0.05, 0.05)
            loss += float((coordinate_loss.sum(axis=1) * weights).sum() / norm)
            delta = slope * weights[:, None] / norm
        gradients["point"] = arguments.T @ delta
        gradients["point_bias"] = delta.sum(axis=0)
        argument_back += delta @ self.parameters["point"].T
        if self.autoregressive:
            argument_back *= 1 - arguments * arguments
            gradients["ability_embedding"] = np.zeros_like(
                self.parameters["ability_embedding"]
            )
            np.add.at(gradients["ability_embedding"], labels["ability"], argument_back)
        back += argument_back
        back *= 1 - hidden * hidden
        gradients["input"] = x.T @ back
        gradients["bias"] = back.sum(axis=0)
        return loss, gradients

    def loss(self, x, labels, points):
        return self.gradients(x, labels, points)[0]

    def learn(self, x, labels, points, rate=0.001, weights=None):
        loss, gradients = self.gradients(x, labels, points, weights)
        self.updates += 1
        norm = np.sqrt(sum(float(np.square(g).sum()) for g in gradients.values()))
        for key, gradient in gradients.items():
            gradient *= min(1.0, 5.0 / max(norm, 1e-8))
            self.m[key] = 0.9 * self.m[key] + 0.1 * gradient
            self.v[key] = 0.999 * self.v[key] + 0.001 * gradient * gradient
            self.parameters[key] -= (
                rate
                * (self.m[key] / (1 - 0.9**self.updates))
                / (np.sqrt(self.v[key] / (1 - 0.999**self.updates)) + 1e-8)
            )
        return loss

    def save(self, path, evidence):
        path = Path(path)
        metadata = {
            "schema": 1,
            "kind": "factorized_entity_imitation",
            "unit_types": self.unit_types,
            "sizes": self.sizes,
            "updates": self.updates,
            "evidence": evidence,
            "autoregressive": self.autoregressive,
            "scope": "initial entity-and-context baseline; map grids and recurrent memory not yet encoded",
        }
        arrays = {
            "metadata": np.array(json.dumps(metadata)),
            "feature_mean": self.feature_mean,
            "feature_scale": self.feature_scale,
            **self.parameters,
        }
        arrays.update({"m_" + k: v for k, v in self.m.items()})
        arrays.update({"v_" + k: v for k, v in self.v.items()})
        with path.with_suffix(path.suffix + ".tmp").open("wb") as stream:
            np.savez_compressed(stream, **arrays)
        path.with_suffix(path.suffix + ".tmp").replace(path)

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata"]))
            if (
                metadata["schema"] != 1
                or metadata["kind"] != "factorized_entity_imitation"
            ):
                raise ValueError("Unsupported imitation checkpoint")
            extras = {
                key: value
                for key, value in metadata["sizes"].items()
                if key
                not in ("ability", "mode", "target_type", "alliance", "queue", "delay")
            }
            policy = cls(
                data["input"].shape[0],
                metadata["sizes"]["ability"],
                metadata["unit_types"],
                extra_sizes=extras,
                point_dimensions=data["point"].shape[1],
                autoregressive=metadata.get("autoregressive", False),
            )
            if "feature_mean" in data:
                policy.feature_mean = data["feature_mean"].copy()
                policy.feature_scale = data["feature_scale"].copy()
            policy.parameters = {key: data[key].copy() for key in policy.parameters}
            policy.m = {key: data["m_" + key].copy() for key in policy.m}
            policy.v = {key: data["v_" + key].copy() for key in policy.v}
            policy.updates = metadata["updates"]
            policy.evidence = metadata["evidence"]
            return policy
