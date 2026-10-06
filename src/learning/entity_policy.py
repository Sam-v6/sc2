"""Joint command heads; every supervised loss trains the shared entity encoder."""

import json

import numpy as np

from src.learning.entity_encoder import JointEntityEncoder


def categorical(logits, mask=None):
    mask = np.ones(len(logits), dtype=bool) if mask is None else np.asarray(mask)
    if not mask.any():
        raise ValueError("No eligible categorical candidate")
    values = np.where(mask, logits, -np.inf)
    probability = np.exp(values - values.max())
    return probability / probability.sum()


def categorical_loss(logits, label, mask=None):
    if not 0 <= label < len(logits) or (mask is not None and not mask[label]):
        raise ValueError("Human label is outside eligible candidates")
    probability = categorical(logits, mask)
    # Log-sum-exp retains finite loss even when a probability underflows.
    allowed = logits if mask is None else logits[np.asarray(mask)]
    loss = np.log(np.exp(allowed - allowed.max()).sum()) + allowed.max() - logits[label]
    probability[label] -= 1
    return float(loss), probability


class JointEntityPolicy:
    def __init__(
        self,
        encoder,
        delays,
        seed=0,
        refinement=False,
        actor_cutoff=False,
        spatial_features=2,
        actor_count=False,
        missing_fields=False,
        actor_relative_points=False,
        actor_geometry=False,
    ):
        self.actor_geometry = actor_geometry
        self.actor_relative_points = actor_relative_points
        self.missing_fields = missing_fields
        if missing_fields and (
            encoder.parameters["entity"].shape[0] != 188
            or encoder.parameters["scene"].shape[0] < 26
            or encoder.parameters["scene"].shape[0] % 2
        ):
            raise ValueError("Incompatible missing-field encoder dimensions")
        self.encoder, self.delays = encoder, tuple(delays)
        self.refinement = refinement
        self.actor_cutoff = actor_cutoff
        self.actor_count = actor_count
        self.spatial_features = spatial_features
        hidden = encoder.parameters["entity"].shape[1]
        abilities = len(encoder.parameters["abilities"])
        rng = np.random.default_rng(seed)
        self.heads = {}
        for name, rows, columns in (
            ("ability", hidden, abilities),
            ("actor", hidden, hidden),
            ("group", hidden, hidden),
            ("mode", hidden, 4),
            ("queue", hidden, 2),
            ("delay", hidden, len(delays)),
            ("target", hidden, hidden),
            ("point_input", 2, hidden),
            ("point_query", hidden, hidden),
            ("offset", hidden, 2),
        ):
            self.heads[name] = rng.normal(0, 1 / np.sqrt(rows), (rows, columns)).astype(
                np.float32
            )
        for name in ("ability", "mode", "queue", "delay", "offset"):
            self.heads[name + "_bias"] = np.zeros(self.heads[name].shape[1], np.float32)

        if refinement:
            self.heads["offset_cell"] = rng.normal(0, 0.1, (2, 2)).astype(np.float32)

        if actor_cutoff:
            self.heads["actor_cutoff"] = np.zeros(hidden, np.float32)

        if actor_count:
            self.heads["actor_count"] = np.zeros(hidden, np.float32)
            self.heads["actor_count_bias"] = np.zeros(1, np.float32)

        if spatial_features > 2:
            coordinates = self.heads["point_input"]
            self.heads["point_input"] = np.zeros((spatial_features, hidden), np.float32)
            self.heads["point_input"][:2] = coordinates
            self.heads["point_bias"] = np.zeros(hidden, np.float32)
            self.heads["spatial_context"] = np.zeros((hidden, hidden), np.float32)

        if actor_relative_points:
            # A zero residual preserves every existing initialization and score.
            self.heads["point_relative"] = np.zeros((4, hidden), np.float32)
        if actor_geometry:
            self.heads["actor_geometry"] = np.zeros((hidden, 4), np.float32)

    @property
    def parameters(self):
        return {
            **{"encoder." + k: v for k, v in self.encoder.parameters.items()},
            **self.heads,
        }

    def _forward(self, inputs, ability=None, actors=None, point=None):
        p = self.heads
        context, entities, encoder_cache = self.encoder.forward(*inputs["encoder"])
        point_inputs = np.asarray(
            inputs["point_features"] if self.spatial_features > 2 else inputs["points"]
        )
        points = np.tanh(
            point_inputs @ p["point_input"]
            + (p["point_bias"] if self.spatial_features > 2 else 0)
        )
        if self.spatial_features > 2:
            context = context + points.mean(axis=0) @ p["spatial_context"]
        ability_logits = context @ p["ability"] + p["ability_bias"]
        if ability is None:
            ability = int(np.argmax(ability_logits[1:])) + 1
        if not 0 < ability < len(ability_logits):
            raise ValueError("Command ability must be in the native vocabulary")
        conditioned = np.tanh(context + self.encoder.parameters["abilities"][ability])
        actor_query = conditioned @ p["actor"]
        actor_logits = entities @ actor_query
        eligible = np.flatnonzero(inputs["actor_mask"])
        geometry = None
        if self.actor_geometry:
            positions = np.asarray(inputs["entity_positions"], dtype=np.float32)
            center = (
                positions[eligible].mean(axis=0)
                if len(eligible)
                else np.zeros(2, np.float32)
            )
            delta = (positions - center) / 32
            geometry = np.concatenate((delta, delta**2), axis=1)
            actor_logits = actor_logits + geometry @ (conditioned @ p["actor_geometry"])
        if self.actor_cutoff:
            actor_logits = actor_logits + conditioned @ p["actor_cutoff"]
        count_log = (
            float(conditioned @ p["actor_count"] + p["actor_count_bias"][0])
            if self.actor_count
            else None
        )
        if actors is None and self.actor_count and len(eligible):
            # A continuous log-count can represent any physically present group
            # size. Only inference rounds/clamps; supervision uses human log(K).
            count = int(np.rint(np.exp(np.clip(count_log, 0, np.log(len(eligible))))))
            ranked = eligible[np.argsort(-actor_logits[eligible], kind="stable")]
            actors = tuple(sorted(int(i) for i in ranked[:count]))
        if actors is None:
            actors = tuple(int(i) for i in eligible if actor_logits[i] >= 0)
            if not actors and len(eligible):
                actors = (int(eligible[np.argmax(actor_logits[eligible])]),)
        if (
            not actors
            or any(i not in eligible for i in actors)
            or len(set(actors)) != len(actors)
        ):
            raise ValueError("A command needs a nonempty eligible actor group")
        group = entities[list(actors)].mean(axis=0)
        arguments = np.tanh(conditioned + group @ p["group"])
        output = {
            "ability": ability_logits,
            "actor": actor_logits,
            "target": entities @ (arguments @ p["target"]),
            "point": points @ (arguments @ p["point_query"]),
            "offset": np.tanh(arguments @ p["offset"] + p["offset_bias"]),
        }
        relative = None
        if self.actor_relative_points:
            centroid = np.asarray(inputs["entity_positions"])[list(actors)].mean(axis=0)
            displacement = (np.asarray(inputs["world_points"]) - centroid) / 32
            relative = np.concatenate((displacement, displacement**2), axis=1)
            output["point"] += relative @ p["point_relative"] @ arguments
        cell_coordinate = None
        if self.refinement and len(points):
            cell = int(np.argmax(output["point"])) if point is None else point
            if not 0 <= cell < len(points):
                raise ValueError("Chosen point cell is outside map candidates")
            cell_coordinate = np.asarray(inputs["points"])[cell]
            output["offset"] = np.tanh(
                arguments @ p["offset"]
                + cell_coordinate @ p["offset_cell"]
                + p["offset_bias"]
            )
        for name in ("mode", "queue", "delay"):
            output[name] = arguments @ p[name] + p[name + "_bias"]
        cache = dict(
            context=context,
            entities=entities,
            encoder=encoder_cache,
            ability=ability,
            conditioned=conditioned,
            actor_query=actor_query,
            actors=actors,
            group=group,
            arguments=arguments,
            points=points,
            point_inputs=point_inputs,
            cell_coordinate=cell_coordinate,
            count_log=count_log,
            point_relative=relative,
            actor_geometry=geometry,
        )
        return output, cache

    def scores(self, inputs, ability=None, actors=None, point=None):
        """Explicit conditioning is for supervised/oracle diagnostics only."""
        return self._forward(inputs, ability, actors, point)[0]

    def predict(self, inputs, ability=None, actors=None):
        """Ordinary inference predicts all choices; explicit oracles are diagnostic."""
        if not np.asarray(inputs["actor_mask"]).any():
            return None
        scores, cache = self._forward(inputs, ability, actors)
        modes = np.array(
            [
                True,
                np.asarray(inputs["target_mask"]).any(),
                len(inputs["points"]) > 0,
                True,
            ]
        )
        mode = int(np.argmax(np.where(modes, scores["mode"], -np.inf)))
        result = dict(
            ability=cache["ability"],
            actors=cache["actors"],
            mode=mode,
            queue=bool(np.argmax(scores["queue"])) if mode != 3 else False,
            delay=self.delays[int(np.argmax(scores["delay"]))],
        )
        if mode == 1:
            result["target"] = int(
                np.argmax(np.where(inputs["target_mask"], scores["target"], -np.inf))
            )
        elif mode == 2:
            result["point"] = int(np.argmax(scores["point"]))
            result["offset"] = tuple(float(x) for x in scores["offset"])
        return result

    def loss_and_gradients(self, inputs, label):
        scores, c = self._forward(
            inputs,
            label["ability"],
            tuple(label["actors"]),
            point=label["point"] if self.refinement and label["mode"] == 2 else None,
        )
        p = self.heads
        gradients = {k: np.zeros_like(v) for k, v in p.items()}
        entity_gradient = np.zeros_like(c["entities"])
        context_gradient = np.zeros_like(c["context"])
        argument_gradient = np.zeros_like(c["arguments"])
        conditioned_gradient = np.zeros_like(c["conditioned"])
        loss = 0.0
        mask = np.arange(len(scores["ability"])) > 0
        value, delta = categorical_loss(scores["ability"], label["ability"], mask)
        loss += value
        gradients["ability"] = np.outer(c["context"], delta)
        gradients["ability_bias"] = delta
        context_gradient += delta @ p["ability"].T

        eligible = np.flatnonzero(inputs["actor_mask"])
        actor_labels = np.isin(eligible, label["actors"]).astype(float)
        logits = scores["actor"][eligible]
        loss += float(np.mean(np.logaddexp(0, logits) - actor_labels * logits))
        actor_delta = np.zeros(len(c["entities"]))
        probability = np.exp(-np.logaddexp(0, -logits))
        actor_delta[eligible] = (probability - actor_labels) / len(eligible)
        if self.refinement:
            selected_count = actor_labels.sum()
            ranking_probability = categorical(logits)
            loss += float(
                np.log(np.exp(logits - logits.max()).sum())
                + logits.max()
                - logits[actor_labels.astype(bool)].mean()
                - np.log(selected_count)
            )
            actor_delta[eligible] += ranking_probability - actor_labels / selected_count
        if self.actor_count:
            count_delta = c["count_log"] - np.log(len(label["actors"]))
            loss += 0.5 * count_delta**2
            gradients["actor_count"] = c["conditioned"] * count_delta
            gradients["actor_count_bias"][0] = count_delta
            conditioned_gradient += p["actor_count"] * count_delta
        if self.actor_cutoff:
            cutoff_delta = actor_delta.sum()
            gradients["actor_cutoff"] = c["conditioned"] * cutoff_delta
            conditioned_gradient += p["actor_cutoff"] * cutoff_delta
        if self.actor_geometry:
            geometry_delta = c["actor_geometry"].T @ actor_delta
            gradients["actor_geometry"] = np.outer(c["conditioned"], geometry_delta)
            conditioned_gradient += geometry_delta @ p["actor_geometry"].T
        query_gradient = c["entities"].T @ actor_delta
        gradients["actor"] = np.outer(c["conditioned"], query_gradient)
        conditioned_gradient += query_gradient @ p["actor"].T
        entity_gradient += np.outer(actor_delta, c["actor_query"])

        for name in ("mode", "queue", "delay"):
            if (name == "delay" and label["delay"] is None) or (
                name == "queue" and label["mode"] == 3
            ):
                continue
            value, delta = categorical_loss(scores[name], int(label[name]))
            loss += value
            gradients[name] = np.outer(c["arguments"], delta)
            gradients[name + "_bias"] = delta
            argument_gradient += delta @ p[name].T

        if label["mode"] in (1, 2):
            name = "target" if label["mode"] == 1 else "point"
            candidates = c["entities"] if name == "target" else c["points"]
            query_name = "target" if name == "target" else "point_query"
            mask = inputs["target_mask"] if name == "target" else None
            value, delta = categorical_loss(scores[name], label[name], mask)
            loss += value
            query_gradient = candidates.T @ delta
            gradients[query_name] = np.outer(c["arguments"], query_gradient)
            argument_gradient += query_gradient @ p[query_name].T
            candidate_gradient = np.outer(delta, c["arguments"] @ p[query_name])
            if name == "target":
                entity_gradient += candidate_gradient
            else:
                if self.actor_relative_points:
                    relative_delta = c["point_relative"].T @ delta
                    gradients["point_relative"] = np.outer(
                        relative_delta, c["arguments"]
                    )
                    argument_gradient += relative_delta @ p["point_relative"]
                point_delta = candidate_gradient * (1 - c["points"] ** 2)
                gradients["point_input"] = c["point_inputs"].T @ point_delta
                if self.spatial_features > 2:
                    gradients["point_bias"] = point_delta.sum(axis=0)
                error = scores["offset"] - np.asarray(label["offset"])
                radii = (
                    np.asarray(inputs["point_radii"])[label["point"]]
                    if self.refinement
                    else np.ones(2)
                )
                loss += float(0.5 * np.square(error * radii).sum())
                offset_delta = error * radii**2 * (1 - scores["offset"] ** 2)
                if self.refinement:
                    gradients["offset_cell"] = np.outer(
                        c["cell_coordinate"], offset_delta
                    )
                gradients["offset"] = np.outer(c["arguments"], offset_delta)
                gradients["offset_bias"] = offset_delta
                argument_gradient += offset_delta @ p["offset"].T

        argument_delta = argument_gradient * (1 - c["arguments"] ** 2)
        gradients["group"] = np.outer(c["group"], argument_delta)
        group_gradient = argument_delta @ p["group"].T / len(c["actors"])
        entity_gradient[list(c["actors"])] += group_gradient
        conditioned_gradient += argument_delta
        conditioned_delta = conditioned_gradient * (1 - c["conditioned"] ** 2)
        context_gradient += conditioned_delta
        if self.spatial_features > 2:
            gradients["spatial_context"] = np.outer(
                c["points"].mean(axis=0), context_gradient
            )
            spatial_delta = (
                (context_gradient @ p["spatial_context"].T) / len(c["points"])
            ) * (1 - c["points"] ** 2)
            gradients["point_input"] += c["point_inputs"].T @ spatial_delta
            gradients["point_bias"] += spatial_delta.sum(axis=0)
        encoder_gradients = self.encoder.backward(
            c["encoder"], context_gradient, entity_gradient
        )
        encoder_gradients["abilities"][c["ability"]] += conditioned_delta
        return float(loss), {
            **{"encoder." + k: v for k, v in encoder_gradients.items()},
            **gradients,
        }

    def save(self, path, metadata):
        dimensions = [
            self.encoder.parameters[k].shape[0]
            for k in ("entity", "scene", "history_roles", "types", "abilities")
        ]
        configuration = dict(
            dimensions=dimensions,
            hidden=self.heads["actor"].shape[0],
            delays=self.delays,
            metadata=metadata,
            refinement=self.refinement,
            actor_cutoff=self.actor_cutoff,
            actor_count=self.actor_count,
            spatial_features=self.spatial_features,
            missing_fields=self.missing_fields,
            role_pooling=self.encoder.role_pooling,
            context_layer_norm=self.encoder.context_layer_norm,
            actor_relative_points=self.actor_relative_points,
            actor_geometry=self.actor_geometry,
            encoder_backend=getattr(self.encoder, "backend", "numpy"),
            relational_attention=getattr(self.encoder, "relational_attention", False),
        )
        np.savez_compressed(
            path, **self.parameters, configuration=json.dumps(configuration)
        )

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as archive:
            configuration = json.loads(str(archive["configuration"]))
            encoder_kind = JointEntityEncoder
            encoder_options = {}
            if configuration.get("encoder_backend", "numpy") == "torch":
                from src.learning.entity_torch_encoder import TorchEntityEncoder

                encoder_kind = TorchEntityEncoder
                encoder_options["relational_attention"] = configuration.get(
                    "relational_attention", False
                )
            encoder = encoder_kind(
                *configuration["dimensions"],
                hidden=configuration["hidden"],
                role_pooling=configuration.get("role_pooling", False),
                context_layer_norm=configuration.get("context_layer_norm", False),
                **encoder_options,
            )
            policy = cls(
                encoder,
                configuration["delays"],
                refinement=configuration.get("refinement", False),
                actor_cutoff=configuration.get("actor_cutoff", False),
                actor_count=configuration.get("actor_count", False),
                spatial_features=configuration.get("spatial_features", 2),
                missing_fields=configuration.get("missing_fields", False),
                actor_relative_points=configuration.get("actor_relative_points", False),
                actor_geometry=configuration.get("actor_geometry", False),
            )
            for name, parameter in policy.parameters.items():
                if archive[name].shape != parameter.shape:
                    raise ValueError("Checkpoint parameter shape mismatch")
                parameter[:] = archive[name]
        return policy, configuration["metadata"]
