# Bounded PPO comparison

The DQN workflow produces valid training, checkpoints and replays, including
individual frozen Hard wins. Its broader frozen checks remain 1/30, and repeated
return/reward/action-interface probes have not established reliable strength.
This comparison changes the learner while preserving execution and evidence.
It remains an explicit compact-observation experiment, not the final perception.

## Runtime and constraints

Use the existing PyTorch 2.7.1 CPU backend in
`/home/sam/repos/sc2-repos/SC2RL/.venv/bin/python` (Python 3.11), read-only.
The SC2 workers remain in the project's Python 3.12 environment. Do not download
PyTorch, change the sibling environment, add Gym polling, or script macro choices.
NumPy handles actor/critic inference in workers; a bounded helper uses PyTorch
only for gradients after completed, validated games. Use one CPU thread.

## Interface and verification

1. Add a masked categorical actor and value head with explicit algorithm/schema,
   reward scale, optimizer, RNG and cadence metadata. Save/load atomic NPZ without
   pickle. Keep DQN loading and behavior intact. Check masked inference and RNG,
   serialization, bad schema rejection, terminal versus cutoff GAE, and parity
   between NumPy inference and PyTorch's calculation.
2. Collect current legal masks, old log probabilities and values under the frozen
   worker policy. Compute GAE with gamma derived from macro cadence and lambda .95;
   completed terminal results omit bootstrap, cutoff results retain it. Keep each
   game's boundary explicit. Do not apply DQN's greedy-continuation cuts to PPO.
3. Update using clipped PPO ratio (.2), four epochs, minibatches 256, Adam 3e-4,
   entropy coefficient .01, value coefficient .5 and gradient norm cap .5. Normalize
   advantages. Scale capacity/terminal rewards by .01, recorded as a distinct
   context; do not reuse DQN replay or weights as PPO trajectories. Preserve old
   log probabilities across all updates using the collected batch.
4. Prefer one update over the entire collected batch before canonical promotion.
   Reject helper failure/timeout before changing canonical state. Preserve the
   parent RNG rather than replacing it with worker RNG. Test helper failure and
   mixed game failures, then complete real short train/resume/frozen games.
5. Complete a bounded easier curriculum, then Hard training and frozen development
   comparisons against DQN and uniform random on declared races/builds/maps/seeds.
   Greedy PPO evaluation is the initial protocol; any stochastic evaluation must
   be separately labeled and matched to its random comparison. Reserve fresh
   seed bank 50000 for acceptance after development choices finish. Retain all
   replay/checkpoint/receipt evidence and report failure honestly.

The clipped policy objective follows the
[original PPO paper](https://arxiv.org/abs/1707.06347); local Stable-Baselines3 2.6.0
source provides a reference for advantage normalization and clipping. Neither
source establishes that this observation/action space can reliably beat Hard.
