# Training trajectory self imitation

The user requested literature-informed improvement beyond Hard. Prioritize a
training-only self-imitation experiment over launching the unfinished saving
probe. Preserve the saving foundation; no saving games have launched.

Source: Oh et al. (2018), https://proceedings.mlr.press/v80/oh18b.html,
equations 1–3. Implement positive-current-advantage actor loss with stopped
weights and a one-sided value loss. Use uniform sample means initially: this
omits the paper's prioritized replay and is explicitly a simplification.
No PPO importance ratio applies to this separate SIL loss. Never reuse old
trajectories in the ordinary on-policy PPO objective.

1. Test exact loss, gradients, no learning for nonpositive advantages, legal masks,
   and use of current values rather than archived advantages. No game needed.
2. Audit a corpus of completed *training* episodes with identical observation,
   actions, reward scale/version, gamma and cadence. Include all outcomes;
   per-transition positive advantage determines learning. Reject development,
   evaluation, reserved cases, incomplete/error episodes and context mismatch.
   Reconstruct rewards/returns from immutable ledgers and bind input hashes.
3. Measure positive support, race/action coverage, actor/critic/shared-body
   gradient scales and parent KL before declaring a bounded optimizer schedule.
   Review source/corpus before fitting. Do not overwrite retained checkpoints.
4. Evaluate a separately frozen candidate on fresh paired development cases,
   then test bounded PPO plus SIL continuation only if justified. Offline loss
   improvement is not gameplay improvement. Hard is an intermediate benchmark;
   graduate training by demonstrated per-race/map/build performance toward
   VeryHard, Elite and later cheating difficulties, with separate held-out cases.

Keep CPU-only execution and current load limits. Save replays without showing
videos until the user goal is complete. No human demonstration download,
scripted macro recipe, or training on evaluation victories is authorized by this
plan. SIL evidence is Atari/MuJoCo, not proof of full-game SC2 transfer. Recurrence,
entity representation and sustained investment remain separate later changes;
do not bundle their effects into this first experiment.
