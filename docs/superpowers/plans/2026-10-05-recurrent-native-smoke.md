# Recurrent backend: two native games before the strength experiment

This is an engineering smoke, not a strength comparison, curriculum or checkpoint
selection opportunity. Do not count its outcomes toward Hard acceptance. Its
fitted checkpoints cannot initialize the later controlled training experiment.

Start both typed models from the retained `frozen-easy40.npz` parent SHA256
`0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6`.
The entire parent encoder/actor/value network remains frozen. Only the six new
GRU/residual arrays learn, with fresh Adam moments/clocks. Both arms use the same
32-unit GRU initialization (seed331), previous selected action, zero residual
projections and exact initial parent outputs. The control resets hidden state
at every decision; the recurrent arm resets at episode start. The identical
parameterization isolates access to history while preserving existing behavior.

Declare exactly one game per arm: seed/policy seed119000, Terran Rush computer,
Medium, Simple64, Terran learner, ordinary combat-kills-v1 objective and retained
discount/scaling, macro1 second, game limit1200 seconds and wall limit180 seconds.
Check the case has not appeared in prior receipts before freezing. Record native
replays, full action ledgers, chronological transition journals and typed training
trajectories. No replacement games, reward/action/micro changes or macro recipes.

Then perform exactly four PPO updates per arm on its own complete game. Entire
episodes are minibatches, with full sequence BPTT and reconstruction from episode
start; no isolated-transition shuffle or truncated hidden state. Reconstruct the
actual behavior likelihoods and values before training. Verify finite full-match
Monte Carlo returns, advantages and terminal boundaries. PPO clip.2,lr.0003,
eps1e-5,entropy.01,value.5,gradient limit.5. Advantages are normalized over the
collected batch; each whole-episode loss is a mean, so games have equal minibatch
weight rather than weight proportional to length. Save fresh fitted typed models,
Adam clocks/moments and every optimizer metric. No fitting during native games.

The mechanism diagnostic passed: ordered history has mean Brier.1185465 versus
current.1292684 and shuffled.1254414 on20 whole-game-held-out predictor episodes.
The representation had previously been trained on those games, so this is
information evidence in a prelearned encoder, not unseen-game policy generalization.
Independent receipt:`logs/audit/recurrent-history-diagnostic-independent-review.json`.
The v1 loader was aborted for repeated decompression and preserved separately;
the single v2 predictor result uses unchanged data/split/targets/gates.

Before native launch, review/freeze the worker, NumPy/Torch policy, fitter,
controller and used runtime dependencies. Verify the unique spawn import with
zero games. This smoke uses at most two engines, CPU-only,one numerical thread,
eight-CPU affinity,nice10,baseline50% and whole-machine ceiling80%. The guard
also supervises the Torch subprocess. Preserve failures and partial artifacts;
never hot-edit frozen sources or re-run an observed completed case. Replays stay
unopened and no videos are shown. Evidence validity can pass even when both
native games lose; reliable all-race Hard remains a separate unmet requirement.
