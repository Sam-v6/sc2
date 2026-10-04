"""Small NumPy DQN experiment: replay learning, target network, explicit schema."""
from collections import deque
import json
from pathlib import Path
import numpy as np


class Policy:
    def __init__(self, features, actions, seed=7):
        self.features = list(features)
        self.actions = list(actions)
        self.rng = np.random.default_rng(seed)
        n, k, hidden = len(features), len(actions), 64
        self.network = [self.rng.normal(0, 1 / np.sqrt(n), (n, hidden)), np.zeros(hidden),
                        self.rng.normal(0, 0.01, (hidden, k)), np.zeros(k)]
        self.target = [p.copy() for p in self.network]
        self.m = [np.zeros_like(p) for p in self.network]
        self.v = [np.zeros_like(p) for p in self.network]
        self.gamma = 0.99
        self.epsilon = 0.5
        self.updates = 0
        self.episodes = 0
        self.attempts = 0
        self.macro_seconds = None
        self.experience = deque(maxlen=20000)

    @property
    def parameters(self):
        return np.concatenate([p.ravel() for p in self.network])

    def values(self, observations, target=False):
        w1, b1, w2, b2 = self.target if target else self.network
        return np.tanh(np.asarray(observations) @ w1 + b1) @ w2 + b2

    def act(self, observation, legal_mask, explore):
        mask = np.asarray(legal_mask, dtype=bool)
        legal = np.flatnonzero(mask)
        if not len(legal):
            raise ValueError('No legal action, including wait')
        if explore and self.rng.random() < self.epsilon:
            return int(self.rng.choice(legal))
        return int(np.argmax(np.where(mask, self.values(observation), -np.inf)))

    def remember(self, observation, action, reward, next_observation, next_mask, terminal, discount=None):
        self.experience.append((np.asarray(observation, dtype=float), int(action), float(reward),
                                np.asarray(next_observation, dtype=float), np.asarray(next_mask, dtype=bool), bool(terminal), self.gamma if discount is None else float(discount)))

    def targets(self, rewards, next_observations, masks, terminals, discounts=None):
        selected = np.argmax(np.where(masks, self.values(next_observations), -np.inf), axis=1)
        target = self.values(next_observations, target=True)
        bootstrap = target[np.arange(len(selected)), selected]
        return rewards + (self.gamma if discounts is None else discounts) * np.where(terminals, 0, bootstrap)

    def learn(self, batch_size=64):
        if not self.experience:
            return None
        indices = self.rng.integers(len(self.experience), size=min(batch_size, len(self.experience)))
        batch = [self.experience[int(i)] for i in indices]
        states, actions, rewards, nxt, masks, terminals, discounts = map(np.array, zip(*batch))
        w1, b1, w2, b2 = self.network
        hidden = np.tanh(states @ w1 + b1)
        q = hidden @ w2 + b2
        error = q[np.arange(len(batch)), actions] - self.targets(rewards, nxt, masks, terminals, discounts)
        delta = np.zeros_like(q)
        delta[np.arange(len(batch)), actions] = np.clip(error, -1, 1) / len(batch)
        back = (delta @ w2.T) * (1 - hidden * hidden)
        gradients = [states.T @ back, back.sum(axis=0), hidden.T @ delta, delta.sum(axis=0)]
        self.updates += 1
        for i, (parameter, gradient) in enumerate(zip(self.network, gradients)):
            self.m[i] = .9 * self.m[i] + .1 * gradient
            self.v[i] = .999 * self.v[i] + .001 * gradient * gradient
            parameter -= .001 * (self.m[i] / (1 - .9 ** self.updates)) / (np.sqrt(self.v[i] / (1 - .999 ** self.updates)) + 1e-8)
        if self.updates % 100 == 0:
            self.target = [p.copy() for p in self.network]
        return float(np.mean(np.where(abs(error) < 1, .5 * error * error, abs(error) - .5)))

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {'version': 2, 'features': self.features, 'actions': self.actions,
                    'gamma': self.gamma, 'epsilon': self.epsilon, 'updates': self.updates,
                    'episodes': self.episodes, 'attempts': self.attempts, 'macro_seconds': self.macro_seconds, 'rng': self.rng.bit_generator.state}
        data = {'metadata': np.array(json.dumps(metadata))}
        for name in ('network', 'target', 'm', 'v'):
            for i, array in enumerate(getattr(self, name)):
                data[f'{name}{i}'] = array
        n, k = len(self.features), len(self.actions)
        columns = list(zip(*self.experience)) if self.experience else [()] * 7
        for key, column, shape in zip(('states', 'actions', 'rewards', 'next_states', 'masks', 'terminals', 'discounts'), columns,
                                      ((-1, n), (-1,), (-1,), (-1, n), (-1, k), (-1,), (-1,))):
            data[key] = np.asarray(column).reshape(shape)
        temporary = path.with_name(path.name + '.tmp')
        with temporary.open('wb') as file:
            np.savez_compressed(file, **data)
        temporary.replace(path)

    @classmethod
    def load(cls, path, features, actions):
        with np.load(path, allow_pickle=False) as data:
            metadata = json.loads(str(data['metadata']))
            if metadata['version'] not in (1, 2) or metadata['features'] != list(features) or metadata['actions'] != list(actions):
                raise ValueError('Checkpoint observation/action schema mismatch')
            policy = cls(features, actions)
            for name in ('network', 'target', 'm', 'v'):
                setattr(policy, name, [data[f'{name}{i}'].copy() for i in range(4)])
            for key in ('gamma', 'epsilon', 'updates', 'episodes'):
                setattr(policy, key, metadata[key])
            policy.attempts = metadata.get('attempts', policy.episodes)
            policy.macro_seconds = metadata.get('macro_seconds')
            policy.rng.bit_generator.state = metadata['rng']
            discounts = data['discounts'] if metadata['version'] == 2 else np.full(len(data['actions']), policy.gamma)
            for state, action, reward, nxt, mask, terminal, discount in zip(
                    *(data[key] for key in ('states', 'actions', 'rewards', 'next_states', 'masks', 'terminals')), discounts):
                policy.remember(state, action, reward, nxt, mask, terminal, discount)
        return policy
