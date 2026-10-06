# Test a nonlinear unit selection score

Human imitation remains the only learning stage. The best fixed62-command check
uses actor geometry: actors52 and complete51, below56. Attention gives47actors
and47complete, despite all62targets matching. Frozen attention pairs prove the
wrong candidates are not identical inputs; seven differ only in XY. Frozen
geometry diagnosis finds an active ranking-learning signal, rather than proof
of dead gradients. Neither observation proves the current model cannot fit.

Astra's user-authorized consultation recommends one bounded capacity change:
let a learned per-candidate score combine the candidate and game context before
a nonlinearity. The current query is linear over the final candidate features.
This residual can learn different local shapes for different contexts. It is
not a nearest-worker rule or a guarantee of better learning/generalization.

Implement an opt-in NumPy residual with32hidden units:
`v @ tanh([entity, relative XY, squared XY] @ W_entity + conditioned @ W_context + bias)`.
Use the same eligible-actor-centroid geometry scaled by32 as the existing
geometry feature. Add the scalar to actor logits. Start `v` at zero, using a
separate RNG for new matrices, preserving baseline initialization/scores.
All actor candidates retain the same eligibility mask and existing losses.
No human target, unit identity or command label enters ordinary inference.
Keep all existing raw ability/group/target/queue/timing controls and sensing.

Propagate actor gradients into every residual parameter, candidate embeddings
and conditioned context. Defaults/old checkpoints retain the existing path.
Persist the flag and new arrays through save/load and expose one CLI opt-in.
Do not change the encoder, optimizer, count/cutoff, target factorization or loss
weights. This isolates scoring capacity from another representation change.

Verification: finite differences for new heads plus existing shared parameters;
zero-output exact score/default initialization parity; permutation behavior;
checkpoint round-trip; synthetic context-dependent interior candidate ranking;
full suite, Ruff/diff checks and independent review before human fitting.

Then freeze a matched geometry-baseline/residual comparison on the same62
selected teaching rows, same200epochs/800updates/batch16/rate.001/seeds, each
capped at120optimizer seconds with two CPU threads. Geometry stays enabled in
both; attention, normalization and importance stay disabled. Bind selected rows,
source/code/configuration/initial audits/checkpoints before optimizer updates.
Require actors>=56, complete>=56, abilities62 and targets>=59. Report both runs,
all fields, losses, updates/time and final ranking versus group-count errors.
Report actor margins and resolution of the geometry baseline's ten failures.
Failure ends the experiment without extending or sweeping parameters. Success
only permits a separately frozen cross-game human-imitation test. No native
games, reserved/diagnostic replay predictions, promotion or RL in this test.
