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

Completed after independent review and pre-launch repairs: configuration hashes,
direct cached logits, finite-value guards and exact per-row reload predictions
are verified. Cached logit max error4.84e-6, gradient8.08e-8, finite difference
5.39e-11. Both optimizers finish their250iteration budget: Adam250evaluations in
0.58seconds; L-BFGS281evaluations in0.89seconds, status1iteration limit rather
than convergence. Actor objective0.443365→0.357067(Adam), →0.0179665(L-BFGS).

Adam reaches actors54/complete53; L-BFGSactors61/complete59. Both retain
targets60, all62abilities/modes/queues and43known timings. L-BFGS passes all
small-set gates; Adam fails actor/complete gates. L-BFGS fixes nine of ten
baseline actor errors with no new ones; only523:513remains. Encoder and other
parameters are byte-identical, and every saved/reloaded ordinary command
prediction matches. Source/code/configuration/checkpoint bindings verify.

L-BFGS selection-weight norm rises8.39→731.75(max coefficient164.05); this must
be reported in subsequent generalization tests. It is no evidence of native
competence or reliable Hard wins. No promotion, other replay predictions,
native games or RL. Evidence:
`logs/roadmap/professional-convex-actor-01/{contract,comparison}.json` and both
run reports/checkpoints, including all62predictions/margins/fixed/new errors.
