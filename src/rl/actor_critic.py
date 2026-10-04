"""Masked PPO inference and completed-episode rollouts without a Torch dependency."""
import json
from pathlib import Path
import numpy as np


class ActorCritic:
    algorithm = 'ppo'
    reward_scale = .01
    settings = {'clip': .2, 'epochs': 4, 'batch_size': 256, 'learning_rate': .0003,
                'entropy': .01, 'value': .5, 'max_grad_norm': .5, 'gae_lambda': .95}

    def __init__(self, features, actions, seed=7):
        self.features, self.actions = list(features), list(actions)
        self.rng = np.random.default_rng(seed)
        n, k = len(features), len(actions)
        self.network = [self.rng.normal(0, 1 / np.sqrt(n), (n, 64)), np.zeros(64),
                        self.rng.normal(0, .01, (64, k)), np.zeros(k), np.zeros(64), np.array(0.)]
        self.m, self.v = [[np.zeros_like(p) for p in self.network] for _ in range(2)]
        self.gamma, self.epsilon = .99, 0
        self.updates = self.episodes = self.attempts = 0
        self.macro_seconds = self.reward_version = self.backend = None
        self.rollout = []

    @property
    def parameters(self):
        return np.concatenate([p.ravel() for p in self.network])

    def forward(self, observations):
        w1, b1, w2, b2, wv, bv = self.network
        hidden = np.tanh(np.asarray(observations) @ w1 + b1)
        return hidden @ w2 + b2, hidden @ wv + bv

    def probabilities(self, observations, masks):
        logits, _ = self.forward(observations)
        masks = np.asarray(masks, dtype=bool)
        if not np.all(masks.any(axis=-1)):
            raise ValueError('No legal action, including wait')
        logits = np.where(masks, logits, -np.inf)
        weights = np.exp(logits - logits.max(axis=-1, keepdims=True))
        return weights / weights.sum(axis=-1, keepdims=True)

    def act(self, observation, legal_mask, explore):
        probabilities = self.probabilities(observation, legal_mask)
        if not explore:
            return int(probabilities.argmax())
        if self.epsilon == 1:  # Explicit uniform-random comparison only.
            return int(self.rng.choice(np.flatnonzero(legal_mask)))
        return int(self.rng.choice(len(self.actions), p=probabilities))

    def collect_episode(self, transitions, masks):
        if not transitions or len(transitions) != len(masks):
            raise ValueError('Incomplete PPO trajectory')
        states, actions, rewards, nxt, _, terminal = map(np.array, zip(*transitions))
        states, nxt = states.astype(float), nxt.astype(float)
        masks = np.asarray(masks, dtype=bool)
        probabilities = self.probabilities(states, masks)
        _, values = self.forward(states)
        _, next_values = self.forward(nxt)
        advantages = np.zeros(len(transitions))
        carry = 0.
        for index in reversed(range(len(transitions))):
            continuation = float(not terminal[index])
            delta = rewards[index] + self.gamma * continuation * next_values[index] - values[index]
            carry = delta + self.gamma * self.settings['gae_lambda'] * continuation * carry
            advantages[index] = carry
        log_probs = np.log(probabilities[np.arange(len(actions)), actions])
        self.rollout.extend(zip(states, actions, masks, log_probs, advantages, advantages + values))

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {'version': 3, 'algorithm': self.algorithm, 'features': self.features, 'actions': self.actions,
                    'gamma': self.gamma, 'epsilon': self.epsilon, 'updates': self.updates, 'episodes': self.episodes,
                    'attempts': self.attempts, 'macro_seconds': self.macro_seconds, 'reward_version': self.reward_version,
                    'reward_scale': self.reward_scale, 'settings': self.settings, 'backend': self.backend,
                    'rng': self.rng.bit_generator.state}
        data = {'metadata': np.array(json.dumps(metadata))}
        for group in ('network', 'm', 'v'):
            data.update({f'{group}{i}': p for i, p in enumerate(getattr(self, group))})
        columns = list(zip(*self.rollout)) if self.rollout else [()] * 6
        for key, column, shape in zip(('states', 'chosen', 'legal', 'log_probs', 'advantages', 'returns'), columns,
                                      ((-1, len(self.features)), (-1,), (-1, len(self.actions)), (-1,), (-1,), (-1,))):
            data[key] = np.asarray(column).reshape(shape)
        temporary = path.with_name(path.name + '.tmp')
        with temporary.open('wb') as file:
            np.savez_compressed(file, **data)
        temporary.replace(path)

    @classmethod
    def load(cls, path, features, actions):
        with np.load(path, allow_pickle=False) as data:
            metadata = json.loads(str(data['metadata']))
            if (metadata['version'] != 3 or metadata['algorithm'] != cls.algorithm
                    or metadata['features'] != list(features) or metadata['actions'] != list(actions)):
                raise ValueError('Checkpoint algorithm/observation/action schema mismatch')
            if metadata['reward_scale'] != cls.reward_scale or metadata['settings'] != cls.settings:
                raise ValueError('Checkpoint reward scale/PPO settings mismatch')
            policy = cls(features, actions)
            for group in ('network', 'm', 'v'):
                expected = getattr(policy, group)
                arrays = [data[f'{group}{i}'].copy() for i in range(6)]
                if any(a.shape != b.shape or not np.isfinite(a).all() for a, b in zip(arrays, expected)):
                    raise ValueError('Invalid PPO parameters or optimizer state')
                setattr(policy, group, arrays)
            for key in ('gamma', 'epsilon', 'updates', 'episodes', 'attempts', 'macro_seconds', 'reward_version', 'backend'):
                setattr(policy, key, metadata[key])
            policy.rng.bit_generator.state = metadata['rng']
            columns = [data[key] for key in ('states', 'chosen', 'legal', 'log_probs', 'advantages', 'returns')]
            if any(len(column) != len(columns[0]) or not np.isfinite(column).all() for column in columns):
                raise ValueError('Invalid PPO rollout')
            states, actions_taken, masks, *_ = columns
            masks = masks.astype(bool)
            if (states.shape != (len(states), len(features)) or masks.shape != (len(states), len(actions))
                    or np.any(actions_taken != actions_taken.astype(int))
                    or np.any(actions_taken < 0) or np.any(actions_taken >= len(actions))
                    or (len(states) and not masks[np.arange(len(states)), actions_taken.astype(int)].all())):
                raise ValueError('Invalid PPO rollout state/action/mask')
            policy.rollout = list(zip(states, actions_taken.astype(int), masks, *columns[3:]))
        return policy
