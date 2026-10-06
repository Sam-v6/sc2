# Test selection-head optimization with frozen human features

The frozen separability probe finds one bounded shared score separating all62
human selections. More candidate features are not required for this finite set.
Next test optimization rather than another architecture change. This does not
establish that those features generalize or that the actor loss is ideal.

Start both candidates from the matched geometry baseline checkpoint. Freeze its
encoder and all non-actor heads. Cache the exact legitimate context/candidate
outer products used by actor/geometry/cutoff scoring, verifying original-logit
parity. Use the same62teaching rows and existing mean BCE plus ranking objective,
averaged equally across commands. Human labels supervise weights during fitting;
ordinary inference remains the existing policy with no oracle/lookup/LP solver.

Compare two full-batch actor-head optimizers: Adam(rate.001) and installed SciPy
L-BFGS. Both have at most250iterations and120optimizer seconds, two BLAS threads.
Use the same initial weights, objective, examples and fixed encoder; this isolates
optimization within the frozen score family, not overall joint-training quality.
The original unchanged checkpoint is a reference, not an equal-budget treatment.
Before fitting, bind source/code/runtime/cache/checkpoint/configuration and check
cached loss/gradient parity against the original policy and finite differences.
No new loss weighting, regularization, features, solver-derived initialization,
parameter search or extra iterations after failure.

Save candidates with parent provenance and audit all ordinary command fields.
Require actors>=56, complete>=56, ability62 and targets>=59. Report initial/final
full actor objective, parameter norms, solver status/evaluations/iterations/time,
all command fields and margins, including original errors fixed/new errors.
Checkpoint reload predictions and unchanged data/encoder/non-actor parameters
must verify. A success only enables separately frozen cross-game imitation;
neither optimizer is accepted for native play/RL here. Failure stops this test.
No other replay predictions, native games, large downloads or GPU.
