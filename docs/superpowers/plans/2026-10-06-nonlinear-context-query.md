# Human imitation: nonlinear context-to-selection query

The wider frozen-feature linear fit fails copying/transfer gates, while each
teaching row has an independently separating query. All4510conditioned contexts
are numerically unique and have centered rank32. This supports testing capacity
in the shared context mapping; it does not prove the original linear mapping
is mathematically incapable or observations sufficient.

Add one opt-in selection residual:
`tanh(conditioned @ input + bias) @ output`, with64hidden units and37outputs
for32entity-query coordinates, four existing relative geometry coefficients,
and one membership cutoff. Score each candidate by the dot product of its
existing37features with this query. No tags, human group, human target,
current selection label or replay identity is an inference input. The ability
is teacher-forced only during supervised training, ordinary predicted at
evaluation. Geometry/cutoff are required for this experiment; do not add new
candidate observations or change group selection semantics.

Initialize input with a separate deterministic RNG and output to zero. Preserve
all existing parameter arrays/RNG/default predictions. Test residual scores,
analytical head/shared encoder gradients with finite differences, actor-order
equivariance, save/load and legacy checkpoint behavior before fitting. Keep
framework/dependency installs unchanged. Independently review implementation
and frozen fitting wrapper before launch.

Use the same hash-bound4510-row teaching cache and parent fit05 derivative as
the previous wider comparison. Encoder and other heads stay frozen. Train the
existing selection heads plus residual parameters with installed CPU L-BFGS,
250iterations and300optimizer seconds, two BLAS threads. This objective is
nonconvex; no convergence/global-optimum claim follows a stopped fit. Verify
cached/ordinary score and gradient parity and zero-residual initial predictions
against the parent. Reuse the completed linear comparison as a bound control,
not as new training. No diagnostic labels enter fitting or stopping.

Reconstruct ordinary teaching and reused774diagnostic reports, verifying every
save/reload prediction and unchanged other arrays. Bind source/runtime/helper,
cache/checkpoints/configuration, exclusions, norms, losses and final telemetry.
Use the existing whole-host guard pattern: CPU-only, stop this child after
three consecutive samples above80%, no GPU. Reserved848/51483/51886 untouched.

Retain the previous gates: teaching actors>=2546/4513, complete>=1277/4513,
complete gains in at least7of9games; diagnostic actors>=73/292,
complete>=24/292, targets>=62/292; ability predictions unchanged in every row.
Failure ends this test without extensions/sweeps/promotion/native/RL. Passing
both only permits a separately frozen imitation-only native competence test
with replay/native observation gaps and untaught feature support addressed.
The full roadmap remains incomplete until native competence, learned micro
transfer and later independent full-game RL/difficulty gates pass.
