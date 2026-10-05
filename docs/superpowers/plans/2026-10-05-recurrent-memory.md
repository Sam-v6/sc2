# Apply recurrent memory to learned Terran macro

The literature review recommended a recurrent core after compatible experience
reuse. The completed self-imitation bootstrap did not improve its declared
full-game comparison, so that candidate is not promoted. Its sparse advanced
production support also limits what replay can teach. Memory addresses a different
problem: this policy currently makes decisions without retaining earlier observed
threats, actions or commitments. It does not itself supply missing strategies.

## Minimal implementation

Retain the original 64-unit observation encoder and all macro actions, masks,
reward, cadence and worker/combat execution. Add a 32-unit GRU receiving the
current encoding and previous selected action. Its hidden state contributes
residual actor logits and value. Zero initial residual projections preserve the
parent exactly; new parameters need fresh optimizer state. Macro decisions remain
learned. No build order, unit quota or attack timing is supplied.

The CPU inference core is at
`tools/recurrent_memory/recurrent_core.py`. Four tests currently pass:
parent equivalence at initialization, complete/chunked sequence equivalence,
different histories with the same current observation, and agreement with the
existing Torch GRU cell. The information diagnostic and native backend smoke are now complete, with
independent reviews. Typed checkpoints, full-sequence PPO and a collecting game
worker exist; each smoke arm performed four actual updates. This verifies the
backend, not gameplay improvement. See [results](2026-10-05-recurrent-memory-results.md).

## Checks before native training

Use compatible training trajectories only to check whether ordered recent history
improves prediction of future observed threats and producer availability over a
current-observation control. Split by whole episodes and include shuffled-history
controls. This bounded diagnostic must not use evaluation trajectories or unseen
enemy state, and prediction improvement cannot establish gameplay improvement.
If ordering provides no additional information, revisit the memory hypothesis
before spending a native training budget.

The implemented sequence PPO uses: contiguous trajectories, episode-boundary resets,
full-episode hidden-state reconstruction, exact recorded behavior likelihoods,
and checkpoint/resume agreement. Full BPTT avoids truncated chunks and burn-in
approximations in this version. Shuffling individual transitions is invalid for
a recurrent policy. Verify NumPy inference against Torch training and preserve the
retained feedforward parent. Freeze reviewed source, budgets and inputs before
launch; no current experiment is authorized to modify frozen source generations.

## Bounded gameplay comparison

After the mechanism and implementation checks, declare 64 completed training
games per arm, recurrent versus an identical-parameter memory-reset control, on the same
balanced Medium/Hard schedule. Freeze the parent network in both arms and train
only the new GRU/residual parameters; this preserves the learned initialization
while isolating memory access. Both arms start anew from the retained parent;
exclude fitted engineering-smoke models. Keep rewards and exposure equal. Freeze a fresh paired Hard panel and
an Easy sampled retention panel before fitting. Evaluate greedy and sampled
behavior separately. The seed bank, update schedule and strength gate still need
explicit declaration before this comparison starts; do not select them from its
results. No final acceptance seeds are consumed during this development step.

Use CPU-only learning, one numerical thread, eight-CPU affinity, nice 10, at most
four engines and the user's 80% whole-machine CPU ceiling. Preserve all outcomes
and native replays without displaying videos. A successful development comparison
must precede an opponent-difficulty curriculum: retain demonstrated skills while
progressing through Hard, Harder, VeryHard and Elite. Reliable Hard performance
remains unmet.
