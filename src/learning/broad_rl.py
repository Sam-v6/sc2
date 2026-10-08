"""CPU PPO over raw ability logits, with frozen human command components."""

import json
from pathlib import Path
import numpy as np


def advantages(rewards, values, elapsed_loops):
    """One finite-horizon episode; native timeouts end this 600-second task too."""
    result = np.zeros(len(rewards))
    following = carry = 0.0
    for i in reversed(range(len(rewards))):
        seconds = elapsed_loops[i] / 112.0  # discount measured in five-second units
        discount, trace = 0.99**seconds, 0.95**seconds
        delta = rewards[i] + discount * following - values[i]
        carry = delta + discount * trace * carry
        result[i] = carry
        following = values[i]
    return result, result + values


class ResidualPPO:
    def __init__(self, features, abilities, base_sha256, epsilon=0.1):
        self.base_sha256 = base_sha256
        self.epsilon = epsilon
        self.parameters = {
            "actor": np.zeros((features, abilities)),
            "actor_bias": np.zeros(abilities),
            "value": np.zeros(features),
            "value_bias": np.array(0.0),
        }
        self.m = {k: np.zeros_like(v) for k, v in self.parameters.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.parameters.items()}
        self.updates = 0

    def distribution(self, x, prior, masks):
        masks = np.asarray(masks, dtype=bool)
        if not masks.any(axis=1).all():
            raise ValueError("No legal ability, including WAIT")
        logits = (
            np.asarray(prior)
            + x @ self.parameters["actor"]
            + self.parameters["actor_bias"]
        )
        logits = np.where(masks, logits, -np.inf)
        weights = np.exp(logits - logits.max(axis=1, keepdims=True))
        pi = weights / weights.sum(axis=1, keepdims=True)
        q = (1 - self.epsilon) * pi + self.epsilon * masks / masks.sum(
            axis=1, keepdims=True
        )
        value = x @ self.parameters["value"] + self.parameters["value_bias"]
        return q, pi, value

    def loss_gradients(
        self, x, prior, masks, actions, old_log_probs, advantage, returns
    ):
        q, pi, value = self.distribution(x, prior, masks)
        n = len(x)
        rows = np.arange(n)
        selected = np.maximum(q[rows, actions], 1e-12)
        ratio = np.exp(np.log(selected) - old_log_probs)
        active = ((advantage >= 0) & (ratio <= 1.2)) | (
            (advantage < 0) & (ratio >= 0.8)
        )
        surrogate = np.minimum(ratio * advantage, np.clip(ratio, 0.8, 1.2) * advantage)
        # PPO likelihood is the ACTUAL exploration mixture, not its softmax part.
        responsibility = (1 - self.epsilon) * pi[rows, actions] / selected
        delta = pi.copy()
        delta[rows, actions] -= 1
        delta *= (active * ratio * advantage * responsibility / n)[:, None]
        log_q = np.log(np.maximum(q, 1e-12))
        entropy = -(q * log_q).sum(axis=1).mean()
        delta += (
            0.01
            * (1 - self.epsilon)
            * pi
            * (log_q - (pi * log_q).sum(axis=1, keepdims=True))
            / n
        )
        error = value - returns
        return float(
            -surrogate.mean() + 0.5 * np.square(error).mean() - 0.01 * entropy
        ), {
            "actor": x.T @ delta,
            "actor_bias": delta.sum(axis=0),
            "value": x.T @ error / n,
            "value_bias": np.asarray(error.mean()),
        }

    def update(self, arrays, seed):
        x, prior, masks, actions, old, adv, returns = arrays
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        rng = np.random.default_rng(seed)
        losses = []
        for _ in range(4):
            order = rng.permutation(len(x))
            for start in range(0, len(x), 128):
                i = order[start : start + 128]
                loss, grad = self.loss_gradients(
                    x[i], prior[i], masks[i], actions[i], old[i], adv[i], returns[i]
                )
                self.updates += 1
                losses.append(loss)
                norm = np.sqrt(sum(np.square(g).sum() for g in grad.values()))
                for key, g in grad.items():
                    g = g * min(1.0, 0.5 / max(norm, 1e-8))
                    self.m[key] = 0.9 * self.m[key] + 0.1 * g
                    self.v[key] = 0.999 * self.v[key] + 0.001 * g * g
                    self.parameters[key] -= (
                        0.0003
                        * (self.m[key] / (1 - 0.9**self.updates))
                        / (np.sqrt(self.v[key] / (1 - 0.999**self.updates)) + 1e-5)
                    )
        return {
            "samples": len(x),
            "mean_loss": float(np.mean(losses)),
            "updates": self.updates,
        }

    def save(self, path):
        path = Path(path)
        metadata = {
            "schema": 1,
            "kind": "frozen_human_ability_residual_ppo",
            "base_sha256": self.base_sha256,
            "epsilon": self.epsilon,
            "updates": self.updates,
            "scope": "ability choice only; frozen unit/target components; no strength acceptance",
        }
        arrays = {"metadata": np.array(json.dumps(metadata)), **self.parameters}
        arrays.update({"m_" + k: v for k, v in self.m.items()})
        arrays.update({"v_" + k: v for k, v in self.v.items()})
        with path.with_suffix(".tmp").open("wb") as stream:
            np.savez_compressed(stream, **arrays)
        path.with_suffix(".tmp").replace(path)

    @classmethod
    def load(cls, path, base_sha256):
        with np.load(path, allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata"]))
            if (
                metadata["schema"] != 1
                or metadata["kind"] != "frozen_human_ability_residual_ppo"
                or metadata["base_sha256"] != base_sha256
            ):
                raise ValueError(
                    "Residual checkpoint does not match the frozen human macro"
                )
            p = cls(*data["actor"].shape, base_sha256, metadata["epsilon"])
            for group, prefix in [(p.parameters, ""), (p.m, "m_"), (p.v, "v_")]:
                for key in group:
                    value = data[prefix + key]
                    if value.shape != group[key].shape or not np.isfinite(value).all():
                        raise ValueError("Invalid residual parameters")
                    group[key] = value.copy()
            p.updates = metadata["updates"]
            return p


def episode_arrays(records, result, final_killed, end_loop):
    """Retain every selected ability, including rejected/undecodable attempts."""
    if not records:
        raise ValueError("No RL decisions")
    elapsed = np.diff([*[r["loop"] for r in records], end_loop])
    rewards = np.diff([*[r["killed"] for r in records], final_killed]) / 100.0
    if np.any(elapsed <= 0) or np.any(rewards < -1e-6):
        raise ValueError("Invalid episode clock or decreasing cumulative kill score")
    rewards[-1] += {"Victory": 100.0, "Defeat": -100.0, "Tie": 0.0}[result]
    values = np.array([r["value"] for r in records])
    adv, returns = advantages(rewards, values, elapsed)
    return {
        "states": np.stack([r["state"] for r in records]),
        "priors": np.stack([r["prior"] for r in records]),
        "masks": np.stack([r["mask"] for r in records]),
        "actions": np.array([r["action"] for r in records], dtype=int),
        "log_probs": np.array([r["log_prob"] for r in records]),
        "advantages": adv,
        "returns": returns,
        "rewards": rewards,
        "elapsed_loops": elapsed,
    }
