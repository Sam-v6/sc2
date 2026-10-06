# Wider human imitation after successful selection-head optimization

The62-row test passes with frozen-feature L-BFGS (actors61/complete59), unlike
matched Adam (54/53). Its coefficients grow sharply; test transfer before
accepting it. This phase still trains from human decisions, without RL.

First implement a compact optional actor-head fitter for the same baseline
score family: entity/query, relative geometry and cutoff; no nonlinear/count
heads. Preserve the existing loss and the rest of the policy. Avoid allocating
the context×candidate outer product for every candidate in every game. Cache
contexts and candidate features separately, compute row queries by matrix
multiplication and gradients through segment reductions. Verify factored scores,
loss and gradients against the successful dense probe and the original policy;
include finite differences, checkpoint compatibility and unchanged other heads.
Use installed CPU SciPy only when fitting is explicitly selected. No default
optimizer/dependency installation change. Independently review before fitting.

Then freeze one full-corpus comparison: parent fit05, nine corpus07teaching
games/4510representable rows. Add zero actor-geometry coefficients to a derivative
of fit05; verify all initial teaching/diagnostic predictions exactly equal the
original checkpoint. Other encoder/head parameters stay frozen throughout.
Compare full-batch actor-only Adam(.001) and L-BFGS from identical initial weights,
each250iterations capped at300optimizer seconds, two BLAS threads. Record
evaluations, loss, parameter norms, memory/cache sizes and whole-machine load.
Stop at approximately80%CPU ceiling if competing work pushes beyond it; no GPU.

Reuse774only as an explicitly reused cross-game diagnostic. Reserved
848/51483/51886 remain untouched. Bind exact sources/code/runtime/configuration,
initial prediction parity, caches, checkpoints and selected exclusions. Teacher
labels train actor weights; ordinary evaluation receives neither human ability
nor group. Report all fields, per-teaching-game results, margins/fixed/new errors
and exact saved/reloaded predictions. Do not evaluate774during optimization.

Gates for the L-BFGS candidate: teaching actors>=2546/4513, complete>=1277/4513,
complete gains in at least7of9games; diagnostic actors>=73/292, complete>=24/292,
targets>=62/292; ability predictions must remain exactly unchanged in all games.
Teacher/diagnostic denominators retain original excluded rows consistently.
These gates test useful wider copying, not native competence. A failure ends
the experiment without extensions, sweeps or promotion. Teaching-only success
calls for diagnosing transfer; passing both only permits a separately frozen
imitation-only native behavior test, with known replay/native observation gaps
and untaught input support addressed. No RL or Hard-win claim follows here.

Compact fitter implemented in `src/learning/entity_actor_fit.py`. Four tests
RED→GREEN, then a fifth adds cooperative-wall-bound and Adam/checkpoint checks.
Five focused tests pass; full342tests pass10.30seconds with six optional-framework
skips. Ruff/diff pass. Independent review verifies dense/original/factored math
and both optimizers; no remaining findings. Simulated SciPy absence passes four
tests/skips one, preserving the optional dependency boundary. Default training
and checkpoint formats are unchanged. No wider fitting result yet.
