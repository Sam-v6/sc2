"""Optional CPU timing/choice components for the declared mixed-source experiment."""

import json

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from src.learning.goal_first_policy import GoalFirstPolicy


class ProductionComponent(nn.Module):
    def __init__(
        self,
        dimensions,
        kind,
        abilities=(),
        hidden=64,
        seed=8207,
        type_status=False,
        observation_memory=False,
    ):
        super().__init__()
        if kind not in ("timing", "choice") or (kind == "choice" and not abilities):
            raise ValueError("Require timing or a choice vocabulary")
        self.kind, self.abilities = kind, tuple(abilities)
        self.configuration = dict(
            dimensions=list(dimensions),
            kind=kind,
            abilities=list(abilities),
            hidden=hidden,
            seed=seed,
            type_status=type_status,
            observation_memory=observation_memory,
        )
        self.encoder = GoalFirstPolicy(
            dimensions, (0,), hidden=hidden, seed=seed, type_status=type_status
        )
        with torch.random.fork_rng(devices=[]), torch.device("cpu"):
            torch.manual_seed(seed + 1)
            self.head = nn.Linear(hidden, 1 if kind == "timing" else len(abilities))
            if observation_memory:
                self.observation_gru = nn.GRU(hidden + 2, hidden, batch_first=True)
                self.memory_projection = nn.Linear(hidden, hidden, bias=False)
                nn.init.zeros_(self.memory_projection.weight)

    def current_context(self, inputs):
        raw, _, _, _, history, _ = inputs["encoder"]
        if len(history) or (raw.shape[1] >= 94 and np.any(raw[:, 30:94])):
            raise ValueError(
                "Production components require current state without history"
            )
        return self.encoder.encode_context(inputs)[1]

    def logits(self, inputs):
        context = self.current_context(inputs)
        prefix = inputs.get("observation_prefix")
        if prefix is not None:
            if not self.configuration["observation_memory"] or len(prefix) != 3:
                raise ValueError("Observation memory requires three past-state slots")
            available = []
            frames = []
            for slot, lag in zip(prefix, (45, 112, 336)):
                if slot is None:
                    frames.append(torch.zeros(len(context) + 2, device="cpu"))
                    continue
                state, age = slot
                if not np.isfinite(age) or age < lag:
                    raise ValueError("Past observations must precede the requested lag")
                available.append(age)
                frames.append(
                    torch.cat(
                        (
                            self.current_context(state),
                            context.new_tensor([age / 336, 1]),
                        )
                    )
                )
            if available != sorted(available):
                raise ValueError("Past observation ages must increase with slot lag")
            if available:
                _, hidden = self.observation_gru(torch.stack(frames[::-1])[None])
                context = context + self.memory_projection(hidden[0, 0])
        return self.head(context)

    def loss(self, inputs, target):
        logits = self.logits(inputs)
        if self.kind == "timing":
            return F.binary_cross_entropy_with_logits(
                logits[0], torch.tensor(float(target), device="cpu")
            )
        index = self.abilities.index(int(target))
        return F.cross_entropy(logits[None], torch.tensor([index], device="cpu"))

    @torch.no_grad()
    def predict(self, inputs):
        logits = self.logits(inputs)
        if self.kind == "timing":
            return float(torch.sigmoid(logits[0]))
        probabilities = torch.softmax(logits, dim=0).numpy()
        return dict(zip(self.abilities, map(float, probabilities)))

    def save(self, path, metadata):
        arrays = {
            name: value.detach().numpy() for name, value in self.state_dict().items()
        }
        np.savez_compressed(
            path,
            configuration=np.asarray(json.dumps(self.configuration)),
            metadata=np.asarray(json.dumps(metadata)),
            **arrays,
        )

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as archive:
            policy = cls(**json.loads(str(archive["configuration"])))
            policy.load_state_dict(
                {
                    name: torch.from_numpy(archive[name].copy())
                    for name in policy.state_dict()
                }
            )
            metadata = json.loads(str(archive["metadata"]))
        return policy, metadata
