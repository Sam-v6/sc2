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

Terminal wider comparison: initial ordinary predictions equal fit05 row by row,
and original aggregate fields reproduce. Cache117,087,296bytes versus
3,517,408,256bytes for dense outer products. Both optimizers finish250iterations:
Adam250evaluations/19.25seconds, L-BFGS275evaluations/21.34seconds, the latter
stops at the iteration limit. Actor objective0.636428→0.595732(Adam),
→0.586038(L-BFGS). L-BFGS teaching actors1869→1965, complete825→853; diagnostic
actors53→43, complete6→5, targets62→61, abilities remain3814/149. Only7of9game
improvement and ability-parity gates pass; all other gates fail. No extension.

Frozen encoder/non-actor parameters, exact row-by-row save/reload predictions,
code/configuration/source/checkpoint/cache hashes and terminal telemetry verify.
Whole-host CPU peaks15.7%, memory31.0%; child RSS5,580,959,744bytes. Watchdog
completes exit0 without stopping. Independent wrapper review's CPU-monitor gap
was fixed before launch and re-review found no remaining findings. No model
promotion, native games, reserved predictions or RL. Evidence:
`logs/roadmap/professional-wider-actor-01/{contract,comparison,verification}.json`,
both run reports/checkpoints/cache and the final telemetry sidecar.

A subsequent frozen-cache diagnostic finds no exact opposite-membership feature
collisions across4510rows. Final actor gradient norm0.00213145; it does not prove
convergence or that the shared score family can fit the wider corpus. This
rejects exact frozen-feature collisions as the direct explanation here; it
does not establish raw observation adequacy or justify another optimizer sweep.
Receipt: `professional-wider-actor-01/frozen-feature-diagnosis.json`.
