"""Optional CPU supervised controller: intention, target, then actor group."""

import json

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class GoalFirstPolicy(nn.Module):
    def __init__(self, dimensions, delays, hidden=64, seed=8140, type_status=False):
        super().__init__()
        self.dimensions = tuple(dimensions)
        self.delays = tuple(delays)
        self.hidden, self.seed = hidden, seed
        self.type_status = type_status
        features, scene, roles, types, abilities, points = dimensions
        if features < 6:
            raise ValueError("Ownership pooling requires six entity features")
        if type_status and features not in (94, 188):
            raise ValueError("Type status requires native entity field layout")
        with torch.random.fork_rng(devices=[]), torch.device("cpu"):
            torch.manual_seed(seed)
            self.entity = nn.Linear(features, hidden)
            self.type_embedding = nn.Embedding(types, hidden, padding_idx=0)
            self.ability_embedding = nn.Embedding(abilities, hidden, padding_idx=0)
            self.scene = nn.Linear(scene, hidden)
            self.history_roles = nn.Linear(roles, hidden)
            self.history = nn.GRU(hidden, hidden, batch_first=True)
            self.pool = nn.Linear(4 * (hidden + 1), hidden)
            self.point = nn.Linear(points, hidden)
            self.ability = nn.Linear(hidden, abilities)
            self.mode = nn.Linear(hidden, 4)
            self.target_unit = nn.Linear(hidden, hidden, bias=False)
            self.target_point = nn.Linear(hidden, hidden, bias=False)
            self.offset = nn.Linear(2 * hidden, 2)
            self.goal = nn.Linear(2 * hidden, hidden)
            self.actor = nn.Linear(hidden, hidden, bias=False)
            self.actor_geometry = nn.Linear(hidden, 4, bias=False)
            self.actor_cutoff = nn.Linear(hidden, 1)
            self.arguments = nn.Linear(2 * hidden, hidden)
            self.queue = nn.Linear(hidden, 2)
            self.delay = nn.Linear(hidden, len(delays))
            if type_status:
                self.status_projection = nn.Linear(types * 10, hidden, bias=False)
                nn.init.zeros_(self.status_projection.weight)

    @property
    def missing_fields(self):
        return self.dimensions[0] == 188

    @property
    def spatial_features(self):
        return self.dimensions[5]

    @property
    def engine_vocabulary(self):
        features, scene, roles, types, abilities, points = self.dimensions
        multiplier = 2 if self.missing_fields else 1
        if (
            features not in (94, 188)
            or scene < 13 * multiplier
            or scene % multiplier
            or roles != 9
            or points not in (2, 401 if self.missing_fields else 386)
        ):
            raise ValueError("Goal-first checkpoint lacks a native observation schema")
        return types, abilities, scene // multiplier - 13

    @staticmethod
    def _tensor(values, dtype=torch.float32):
        return torch.as_tensor(np.asarray(values), dtype=dtype, device="cpu")

    @staticmethod
    def _choose(logits, mask=None, gold=None):
        if mask is not None:
            logits = logits.masked_fill(~mask, -torch.inf)
        if gold is None:
            if not torch.isfinite(logits).any():
                raise ValueError("No eligible command candidate")
            return int(logits.argmax()), logits
        if not 0 <= gold < len(logits) or not torch.isfinite(logits[gold]):
            raise ValueError("Human label outside eligible candidates")
        return int(gold), logits

    def _forward(
        self,
        inputs,
        label=None,
        ability_override=None,
        actors_override=None,
        ability_rng=None,
    ):
        raw, types, orders, scene, history, roles = inputs["encoder"]
        raw = self._tensor(raw)
        entities = torch.tanh(
            self.entity(raw)
            + self.type_embedding(self._tensor(types, torch.long))
            + self.ability_embedding(self._tensor(orders, torch.long))
        )
        observed = raw[:, 5] > 0
        groups = torch.stack([observed & (raw[:, i] > 0) for i in (2, 3, 4)], dim=1)
        groups = torch.cat((groups, ~groups.any(dim=1, keepdim=True)), dim=1)
        counts = groups.sum(dim=0)
        pools = groups.float().T @ entities / counts.clamp(min=1)[:, None]
        pooled = torch.cat(
            (pools, counts.float().log1p()[:, None] / 5), dim=1
        ).flatten()
        temporal = torch.zeros(self.hidden)
        if len(history):
            if len(history) > 32:
                raise ValueError("Causal history window is at most32events")
            events = torch.tanh(
                self.ability_embedding(self._tensor(history, torch.long))
                + self.history_roles(self._tensor(roles))
            )
            temporal = self.history(events[None])[1][0, 0]
        status = torch.zeros(self.hidden)
        if self.type_status:
            from src.learning.entity_type_status import unit_type_status

            status = self.status_projection(
                self._tensor(unit_type_status(inputs, self.dimensions[3]))
            )
        context = torch.tanh(
            self.scene(self._tensor(scene)) + self.pool(pooled) + temporal + status
        )
        point_inputs = inputs.get("point_features", inputs["points"])
        points = torch.tanh(self.point(self._tensor(point_inputs)))
        actors_mask = self._tensor(inputs["actor_mask"], torch.bool)
        targets_mask = self._tensor(inputs["target_mask"], torch.bool)
        ability_mask = torch.ones(self.dimensions[4], dtype=torch.bool)
        candidates = inputs.get("command_candidates")
        if candidates is not None:
            ability_mask[:] = False
            for candidate in candidates:
                ability_mask[candidate] = True
        ability_mask[0] = False
        ability, ability_logits = self._choose(
            self.ability(context),
            ability_mask,
            label["ability"] if label else ability_override,
        )
        if ability_rng is not None and label is None and ability_override is None:
            probabilities = (
                torch.softmax(ability_logits.double(), dim=0).detach().numpy()
            )
            ability = int(ability_rng.choice(len(probabilities), p=probabilities))
        conditioned = torch.tanh(context + self.ability_embedding.weight[ability])
        mode_mask = torch.tensor(
            [True, bool(targets_mask.any()), len(points) > 0, True]
        )
        if candidates is not None:
            mode_mask[:3] &= bool(candidates[ability]["normal"])
            mode_mask[3] = bool(candidates[ability]["autocast"])
        mode, mode_logits = self._choose(
            self.mode(conditioned), mode_mask, label["mode"] if label else None
        )
        unit_logits = entities @ self.target_unit(conditioned)
        point_logits = points @ self.target_point(conditioned)
        target = torch.zeros(self.hidden)
        location = self._tensor(inputs["entity_positions"])[actors_mask].mean(dim=0)
        result = dict(ability=ability, mode=mode)
        offset = None
        if mode == 1:
            index, unit_logits = self._choose(
                unit_logits, targets_mask, label["target"] if label else None
            )
            result["target"] = index
            target = entities[index]
            location = self._tensor(inputs["entity_positions"])[index]
        elif mode == 2:
            index, point_logits = self._choose(
                point_logits, gold=label["point"] if label else None
            )
            result["point"] = index
            target = points[index]
            offset = torch.tanh(self.offset(torch.cat((conditioned, target))))
            used_offset = self._tensor(label["offset"]) if label else offset
            location = (
                self._tensor(inputs["world_points"])[index]
                + used_offset * self._tensor(inputs["point_radii"])[index]
            )
            result["offset"] = tuple(float(x) for x in offset.detach())
        goal = torch.tanh(self.goal(torch.cat((conditioned, target))))
        delta = (self._tensor(inputs["entity_positions"]) - location) / 32
        geometry = torch.cat((delta, delta**2), dim=1)
        actor_logits = (
            entities @ self.actor(goal)
            + geometry @ self.actor_geometry(goal)
            + self.actor_cutoff(goal)[0]
        )
        if candidates is not None:
            caster_mask = torch.zeros_like(actors_mask)
            caster_mask[candidates[ability]["autocast" if mode == 3 else "normal"]] = (
                True
            )
            actors_mask = actors_mask & caster_mask
        eligible = torch.nonzero(actors_mask).flatten()
        if label or actors_override is not None:
            actors = tuple(label["actors"] if label else actors_override)
            if (
                not actors
                or len(set(actors)) != len(actors)
                or any(i not in eligible.tolist() for i in actors)
            ):
                raise ValueError("Human actor group outside eligible candidates")
        else:
            actors = tuple(int(i) for i in eligible if actor_logits[i] >= 0)
            if not actors:
                actors = (int(eligible[actor_logits[eligible].argmax()]),)
        result["actors"] = actors
        arguments = torch.tanh(
            self.arguments(torch.cat((goal, entities[list(actors)].mean(dim=0))))
        )
        queue_logits, delay_logits = self.queue(arguments), self.delay(arguments)
        result["queue"] = bool(queue_logits.argmax()) if mode != 3 else False
        result["delay"] = self.delays[int(delay_logits.argmax())]
        return dict(
            ability=ability_logits,
            mode=mode_logits,
            target=unit_logits,
            point=point_logits,
            offset=offset,
            actor=actor_logits,
            queue=queue_logits,
            delay=delay_logits,
        ), result

    def predict(self, inputs, ability=None, actors=None, ability_rng=None):
        if not np.asarray(inputs["actor_mask"]).any() or (
            "command_candidates" in inputs and not inputs["command_candidates"]
        ):
            return None
        with torch.no_grad():
            return self._forward(
                inputs,
                ability_override=ability,
                actors_override=actors,
                ability_rng=ability_rng,
            )[1]

    def loss(self, inputs, label):
        scores, _ = self._forward(inputs, label)
        losses = {}
        for key in ("ability", "mode", "queue", "delay"):
            if (key == "queue" and label["mode"] == 3) or label.get(key) is None:
                continue
            losses[key] = F.cross_entropy(scores[key][None], torch.tensor([label[key]]))
        if label["mode"] in (1, 2):
            key = "target" if label["mode"] == 1 else "point"
            losses[key] = F.cross_entropy(scores[key][None], torch.tensor([label[key]]))
            if key == "point":
                error = (
                    scores["offset"] - self._tensor(label["offset"])
                ) * self._tensor(inputs["point_radii"])[label["point"]]
                losses["offset"] = 0.5 * error.square().sum()
        eligible = self._tensor(inputs["actor_mask"], torch.bool)
        logits = scores["actor"][eligible]
        gold = torch.zeros(len(scores["actor"]))
        gold[list(label["actors"])] = 1
        gold = gold[eligible]
        losses["actor"] = (
            F.binary_cross_entropy_with_logits(logits, gold)
            + logits.logsumexp(0)
            - logits[gold.bool()].mean()
            - gold.sum().log()
        )
        return losses

    def clear_unseen_inputs(self, support):
        """Zero never-taught input weights, retaining their future gradients."""
        with torch.no_grad():
            for name, layer in (
                ("entity", self.entity),
                ("scene", self.scene),
                ("history_roles", self.history_roles),
                ("point", self.point),
            ):
                mask = self._tensor(support[name], torch.bool)
                if mask.shape != (layer.in_features,):
                    raise ValueError("Input support dimensions do not match")
                layer.weight[:, ~mask] = 0
            for name, layer in (
                ("types", self.type_embedding),
                ("abilities", self.ability_embedding),
            ):
                mask = self._tensor(support[name], torch.bool)
                if mask.shape != (layer.num_embeddings,):
                    raise ValueError("Input support dimensions do not match")
                layer.weight[~mask] = 0

    def save(self, path, metadata):
        configuration = dict(
            dimensions=self.dimensions,
            delays=self.delays,
            hidden=self.hidden,
            seed=self.seed,
            metadata=metadata,
            type_status=self.type_status,
        )
        arrays = {k: v.detach().numpy() for k, v in self.state_dict().items()}
        if any(not np.isfinite(v).all() for v in arrays.values()):
            raise ValueError("Nonfinite goal-first checkpoint")
        np.savez_compressed(path, **arrays, configuration=json.dumps(configuration))

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as archive:
            c = json.loads(str(archive["configuration"]))
            policy = cls(
                c["dimensions"],
                c["delays"],
                c["hidden"],
                c["seed"],
                type_status=c.get("type_status", False),
            )
            values = {k: cls._tensor(archive[k]) for k in policy.state_dict()}
            if any(not torch.isfinite(v).all() for v in values.values()):
                raise ValueError("Nonfinite goal-first checkpoint")
            policy.load_state_dict(values)
        return policy, c["metadata"]
