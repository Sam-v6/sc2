"""Bounded CPU autograd helper, run with an already installed Torch interpreter."""
import json
from pathlib import Path
import sys
import numpy as np
import torch
from src.rl.actor_critic import ActorCritic


def update(path):
    torch.set_num_threads(1)
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data['metadata']))
    policy = ActorCritic.load(path, metadata['features'], metadata['actions'])
    if not policy.rollout:
        raise ValueError('No validated rollout samples')
    parameters = [torch.nn.Parameter(torch.from_numpy(p.copy())) for p in policy.network]
    optimizer = torch.optim.Adam(parameters, lr=policy.settings['learning_rate'], eps=1e-5)
    for i, parameter in enumerate(parameters):
        optimizer.state[parameter] = {'step': torch.tensor(float(policy.updates)),
                                      'exp_avg': torch.from_numpy(policy.m[i].copy()),
                                      'exp_avg_sq': torch.from_numpy(policy.v[i].copy())}
    states, chosen, legal, old_log_probs, advantages, returns = map(np.array, zip(*policy.rollout))
    states, legal = torch.from_numpy(states), torch.from_numpy(legal)
    chosen = torch.from_numpy(chosen).long()
    old_log_probs, advantages, returns = [torch.from_numpy(p) for p in (old_log_probs, advantages, returns)]
    advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)

    def forward(indices):
        w1, b1, w2, b2, wv, bv = parameters
        hidden = torch.tanh(states[indices] @ w1 + b1)
        logits = (hidden @ w2 + b2).masked_fill(~legal[indices], -1e9)
        return torch.distributions.Categorical(logits=logits), hidden @ wv + bv

    # Detect activation/orientation/mask/precision drift before any update.
    indices = torch.arange(len(states))
    distribution, values = forward(indices)
    torch.testing.assert_close(distribution.probs, torch.from_numpy(policy.probabilities(states.numpy(), legal.numpy())), atol=1e-10, rtol=1e-10)
    torch.testing.assert_close(values, torch.from_numpy(policy.forward(states.numpy())[1]), atol=1e-10, rtol=1e-10)
    torch.testing.assert_close(distribution.log_prob(chosen), old_log_probs, atol=1e-10, rtol=1e-10)
    losses = []
    for _ in range(policy.settings['epochs']):
        order = policy.rng.permutation(len(states))
        for start in range(0, len(states), policy.settings['batch_size']):
            indices = torch.from_numpy(order[start:start + policy.settings['batch_size']])
            distribution, values = forward(indices)
            ratio = torch.exp(distribution.log_prob(chosen[indices]) - old_log_probs[indices])
            unclipped = ratio * advantages[indices]
            clipped = ratio.clamp(1 - policy.settings['clip'], 1 + policy.settings['clip']) * advantages[indices]
            actor_loss = -torch.minimum(unclipped, clipped).mean()
            value_loss = (values - returns[indices]).square().mean()
            entropy = distribution.entropy().mean()
            loss = actor_loss + policy.settings['value'] * value_loss - policy.settings['entropy'] * entropy
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters, policy.settings['max_grad_norm'])
            optimizer.step()
            policy.updates += 1
            losses.append(float(loss.detach()))
    policy.network = [p.detach().numpy().copy() for p in parameters]
    policy.m = [optimizer.state[p]['exp_avg'].numpy().copy() for p in parameters]
    policy.v = [optimizer.state[p]['exp_avg_sq'].numpy().copy() for p in parameters]
    policy.backend = 'torch ' + torch.__version__
    count = len(policy.rollout)
    policy.rollout.clear()
    policy.save(path)
    ActorCritic.load(path, policy.features, policy.actions)  # Validate before returning success.
    return {'learner_samples': count, 'mean_loss': float(np.mean(losses)), 'backend': policy.backend}


if __name__ == '__main__':
    print(json.dumps(update(Path(sys.argv[1]))))
