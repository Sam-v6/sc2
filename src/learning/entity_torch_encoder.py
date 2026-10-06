"""Optional CPU autograd encoder with learned relationships among known units."""

import numpy as np

try:
    import torch
except ModuleNotFoundError as error:
    raise RuntimeError(
        "The relational encoder requires the optional CPU PyTorch runtime"
    ) from error

from src.learning.entity_encoder import JointEntityEncoder


class TorchEntityEncoder(JointEntityEncoder):
    backend = "torch"

    def __init__(self, *args, relational_attention=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.relational_attention = relational_attention
        if relational_attention:
            if (
                self.parameters["entity"].shape[0] < 2
                or self.parameters["scene"].shape[0] < 3
            ):
                raise ValueError(
                    "Relational distances need unit positions and map dimensions"
                )
            hidden = self.parameters["entity"].shape[1]
            rng = np.random.default_rng(kwargs.get("seed", 0) + 100)
            for name in ("query", "key", "value"):
                self.parameters["attention_" + name] = rng.normal(
                    0, 1 / np.sqrt(hidden), (hidden, hidden)
                ).astype(np.float32)
            self.parameters["attention_output"] = np.zeros((hidden, hidden), np.float32)
            self.parameters["attention_distance"] = np.zeros(1, np.float32)

    def forward(self, entities, unit_types, orders, scene, history, history_roles):
        entities, scene, history_roles = [
            np.asarray(x, dtype=np.float32) for x in (entities, scene, history_roles)
        ]
        unit_types, orders, history = [
            np.asarray(x, dtype=np.int64) for x in (unit_types, orders, history)
        ]
        p = {
            name: torch.from_numpy(value).requires_grad_(True)
            for name, value in self.parameters.items()
        }
        if (
            entities.ndim != 2
            or entities.shape[1] != p["entity"].shape[0]
            or unit_types.shape != (len(entities),)
            or orders.shape != (len(entities),)
        ):
            raise ValueError("Each entity needs one feature row, type and order")
        if (
            history.ndim != 1
            or len(history) > 32
            or history_roles.shape != (len(history), p["history_roles"].shape[0])
            or scene.shape != (p["scene"].shape[0],)
        ):
            raise ValueError("History roles and scene must match encoder dimensions")
        e, s, roles = [torch.from_numpy(x) for x in (entities, scene, history_roles)]
        types, commands, events = [
            torch.from_numpy(x) for x in (unit_types, orders, history)
        ]
        encoded = torch.tanh(
            e @ p["entity"]
            + p["types"][types]
            + p["abilities"][commands]
            + p["entity_bias"]
        )
        hidden = encoded.shape[1]
        if self.relational_attention:
            query = encoded @ p["attention_query"]
            key = encoded @ p["attention_key"]
            value = encoded @ p["attention_value"]
            # Normalized coordinates * map dimensions /32 gives world distance.
            positions = e[:, :2] * s[1:3] * 8
            distance = ((positions[:, None] - positions[None, :]) ** 2).sum(dim=2)
            scores = (
                query @ key.T / np.sqrt(hidden) - distance * p["attention_distance"][0]
            )
            attention = torch.softmax(scores, dim=1)
            encoded = encoded + (attention @ value) @ p["attention_output"]
        if self.role_pooling:
            observed = e[:, 5] > 0
            groups = torch.stack([observed & (e[:, i] > 0) for i in (2, 3, 4)], dim=1)
            groups = torch.cat((groups, ~groups.any(dim=1, keepdim=True)), dim=1)
            counts = groups.sum(dim=0).to(dtype=torch.float32)
            weights = groups.to(dtype=torch.float32) / counts.clamp_min(1)
            pooled = torch.cat(
                (weights.T @ encoded, (torch.log1p(counts) / 5)[:, None]), dim=1
            ).flatten()
        else:
            pooled = encoded.sum(dim=0) / max(len(encoded), 1)
        event_vectors = torch.tanh(
            p["abilities"][events] + roles @ p["history_roles"] + p["history_bias"]
        )
        padded = torch.cat(
            (
                torch.zeros(
                    (32 - len(history), hidden), dtype=torch.float32, device="cpu"
                ),
                event_vectors,
            ),
            dim=0,
        )
        projection = (
            s @ p["scene"]
            + pooled @ p["pool"]
            + padded.flatten() @ p["history"]
            + p["context_bias"]
        )
        if self.context_layer_norm:
            centered = projection - projection.mean()
            projection = centered / torch.sqrt((centered**2).mean() + 1e-5)
        context = torch.tanh(projection)
        cache = dict(context=context, encoded=encoded, parameters=p)
        return context.detach().numpy(), encoded.detach().numpy(), cache

    def backward(self, cache, context_gradient, entity_gradient):
        gradients = torch.autograd.grad(
            (cache["context"], cache["encoded"]),
            tuple(cache["parameters"].values()),
            grad_outputs=tuple(
                torch.as_tensor(g, dtype=torch.float32, device="cpu")
                for g in (context_gradient, entity_gradient)
            ),
            allow_unused=True,
        )
        return {
            name: np.zeros_like(self.parameters[name])
            if gradient is None
            else gradient.detach().numpy()
            for name, gradient in zip(cache["parameters"], gradients)
        }
