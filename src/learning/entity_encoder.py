"""Compact shared entity/history encoder for joint human command learning."""

import numpy as np


class JointEntityEncoder:
    def __init__(
        self,
        features,
        scene_features,
        history_features,
        unit_types,
        abilities,
        hidden=32,
        seed=0,
    ):
        rng = np.random.default_rng(seed)

        def matrix(rows, scale=None):
            return rng.normal(
                0, scale or 1 / np.sqrt(max(rows, 1)), (rows, hidden)
            ).astype(np.float32)

        self.parameters = {
            "entity": matrix(features),
            "types": matrix(unit_types, 0.1),
            "abilities": matrix(abilities, 0.1),
            "scene": matrix(scene_features),
            "pool": matrix(hidden),
            "history": matrix(32 * hidden),
            "history_roles": matrix(history_features),
            "entity_bias": np.zeros(hidden, dtype=np.float32),
            "context_bias": np.zeros(hidden, dtype=np.float32),
            "history_bias": np.zeros(hidden, dtype=np.float32),
        }

    def forward(self, entities, unit_types, orders, scene, history, history_roles):
        """Return context, per-entity embeddings and a backward-pass cache.

        Entities have no positional index features. History is chronological,
        right-aligned in the 32-command window; unused slots contribute zero.
        Categorical IDs use the complete vocabulary, rather than strategy recipes.
        """
        p = self.parameters
        entities, scene, history_roles = map(
            np.asarray, (entities, scene, history_roles)
        )
        unit_types, orders, history = (
            np.asarray(values, dtype=int) for values in (unit_types, orders, history)
        )
        if (
            entities.ndim != 2
            or entities.shape[1] != p["entity"].shape[0]
            or unit_types.shape != (len(entities),)
            or orders.shape != (len(entities),)
        ):
            raise ValueError("Each entity needs one feature row, type and order")
        if (
            history.ndim != 1
            or history_roles.shape != (len(history), p["history_roles"].shape[0])
            or scene.shape != (p["scene"].shape[0],)
        ):
            raise ValueError("History roles and scene must match their feature shapes")
        if len(history) > 32:
            raise ValueError("Encoder history window is 32 commands")
        encoded = np.tanh(
            entities @ p["entity"]
            + p["types"][unit_types]
            + p["abilities"][orders]
            + p["entity_bias"]
        )
        pooled = encoded.sum(axis=0) / max(len(encoded), 1)
        events = np.tanh(
            p["abilities"][history]
            + history_roles @ p["history_roles"]
            + p["history_bias"]
        )
        padded = np.zeros((32, encoded.shape[1]), dtype=events.dtype)
        if len(history):
            padded[-len(history) :] = events
        context = np.tanh(
            scene @ p["scene"]
            + pooled @ p["pool"]
            + padded.ravel() @ p["history"]
            + p["context_bias"]
        )
        cache = {
            "entities": entities,
            "unit_types": unit_types,
            "orders": orders,
            "scene": scene,
            "history": history,
            "history_roles": history_roles,
            "encoded": encoded,
            "pooled": pooled,
            "events": events,
            "padded": padded,
            "context": context,
        }
        return context, encoded, cache

    def backward(self, cache, context_gradient, entity_gradient):
        """Propagate any downstream command losses into the shared parameters."""
        p, c = self.parameters, cache
        gradients = {name: np.zeros_like(value) for name, value in p.items()}
        context_delta = np.asarray(context_gradient) * (1 - c["context"] ** 2)
        gradients["scene"] = np.outer(c["scene"], context_delta)
        gradients["pool"] = np.outer(c["pooled"], context_delta)
        gradients["history"] = np.outer(c["padded"].ravel(), context_delta)
        gradients["context_bias"] = context_delta
        entity_delta = (
            np.asarray(entity_gradient)
            + (context_delta @ p["pool"].T) / max(len(c["encoded"]), 1)
        ) * (1 - c["encoded"] ** 2)
        gradients["entity"] = c["entities"].T @ entity_delta
        gradients["entity_bias"] = entity_delta.sum(axis=0)
        np.add.at(gradients["types"], c["unit_types"], entity_delta)
        np.add.at(gradients["abilities"], c["orders"], entity_delta)
        if len(c["history"]):
            history_delta = (context_delta @ p["history"].T).reshape(c["padded"].shape)
            history_delta = history_delta[-len(c["history"]) :] * (1 - c["events"] ** 2)
            gradients["history_roles"] = c["history_roles"].T @ history_delta
            gradients["history_bias"] = history_delta.sum(axis=0)
            np.add.at(gradients["abilities"], c["history"], history_delta)
        return gradients
