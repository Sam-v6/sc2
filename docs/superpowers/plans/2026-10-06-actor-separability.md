# Frozen unit-selection separability diagnostic

The nonlinear actor score lowers loss without improving52/62exact selections.
Before changing architecture again, distinguish selection-feature support from
the learned mapping between game context and selection scores.

Use the frozen matched geometry baseline from
`professional-small-set-nonlinear-01/baseline/policy.npz` and its exact62selected
human teaching rows. Reconstruct inputs with the same collector settings and
bind source/current-code/checkpoint/helper/runtime hashes. No other replay
predictions, native games, deployed-policy updates or RL.

For each row, use the frozen unit embedding, relative XY/squares and a constant
cutoff feature. Solve a linear maximum-margin probe using the human membership
labels: every gold actor must score positively and every other eligible actor
negatively. Bound each coefficient to[-1,1]. A separately chosen query per row
is an explicit diagnostic oracle, not ordinary inference or generalization.

Then solve one shared linear probe on the outer product of the frozen
ability-conditioned context with those same candidate features. This is exactly
the baseline actor/geometry/cutoff score family with frozen encoder/context;
verify its reconstruction of original actor logits before solving. Shared
coefficients have the same[-1,1]bounds. This tests score-family support, not the
ability of the existing training procedure to find a useful general solution.

Use installed SciPy/HiGHS, CPU only, one solver thread/two BLAS threads. Cap each
per-row solver at2seconds, all per-row solvers at90seconds, and shared solver at
45seconds. Verify achieved signed margins directly from returned coefficients.
Report terminal statuses, margins, original exact selection and feature
collisions. Do not call a time limit, numerical failure or near-zero margin proof
of impossibility. A verified positive margin proves only finite-set separation
with the chosen frozen features. Human labels and independent per-row probes
never enter a deployed checkpoint. Preserve all results; no budget extension.

Completed: all62independent solvers terminate optimally, with minimum achieved
margin0.000925 and no opposite-label feature collisions. The shared solver
terminates optimally in31.03seconds, achieving0.015785843624879448 signed margin
with coefficient bounds[-1,1]. Direct original-score reconstruction and
source/code/checkpoint bindings pass. This demonstrates finite-set support in
the frozen score family; it is no learned held-out/native result. No policy is
updated or promoted. Evidence:
`logs/roadmap/professional-actor-separability-01/{contract,report}.json`.
