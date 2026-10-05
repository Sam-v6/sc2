# Saved-checkpoint SCV preference and credit audit

The corrected sensory continuation regresses to7/30Medium wins and almost stops
choosing SCV production. Astra recommends locating that failure before another
training arm. Assumption: the saved behavior checkpoints and raw observations
can expose when preference changed; this is not a gameplay counterfactual.

First freeze a measurement bank from the six original parent probe games86000–5:
decision time below180seconds and SCV legal. Primary stratum additionally requires
the recorded parent greedy choice to be SCV. Select states solely by these original
conditions, before inspecting updated checkpoints. Hash inputs and encoder source.
Evaluate initial and every four-game boundary through40games, including the final
frozen policy. Report SCV probability, SCV-minus-wait logit margin, greedy SCV rate,
and tanh saturation. Repeat with appended inputs zeroed for functional attribution
only. Locate the earliest primary mean margin at or below zero that remains at or
below zero at every later saved boundary. If none exists, report that explicitly;
do not change the criterion to manufacture a reversal.

Then inspect the exact four-game batch preceding that boundary: reconstruct
behavior values, Monte Carlo returns and actual batch-normalized advantages;
separate terminal, combat and telescoping potential terms. Compare early SCV/wait
samples by game. Inspect actor, critic and entropy gradient directions against the
fixed-bank margin and saved Adam momentum, distinguishing local derivatives from
the realized multi-minibatch update. Stop on reproducible attribution or explicitly
inconclusive evidence. No automatic GAE, reward or scouting experiment follows.

Checks: synthetic persistent-boundary tests must reject temporary crossings;
verify fixed-bank parent choices and exact encoder prefixes, checkpoint hashes,
finite metrics, and unchanged checkpoint bytes. Later component attribution needs
telescoping-return and gradient finite-difference checks before claims.

Limits: zero new games, zero optimizer updates, no checkpoint writes, CPU only,
one BLAS/Torch thread under existing low_load, no sudo or downloads. Diagnostic
source and artifacts live in ignored `logs/scv-credit-audit/`; main code is unchanged.

## Completed fixed-state preference audit

The frozen bank contains134early SCV-legal states, including74primary states where
the original parent chose SCV. Three persistent-crossing tests pass. Independent
review verifies selection, encoder prefixes, all11checkpoint hashes and metrics.
Initial mean SCV-minus-wait margin is .43430; the first persistent crossing occurs
at180episodes (after36new training games), from .09455 at176 to -.11882 at180 and
-.18826 at184. Appended-input-zero inference also remains negative at184 (-.19106),
so directly zeroing those inputs does not restore the saved policy's preference.
Across the reversal boundary, the margin changes -.21337 with all inputs and
-.21397 with appended inputs zeroed; the crossing persists in both views.
No hidden units cross the chosen .99 saturation threshold on the primary bank.
These findings do not establish whether earlier representation updates caused it.

## Preceding-batch credit diagnostic

The176-to180 boundary uses seeds88176–88179: one defeat and three ties,4425total
transitions. The saved update counter advances1104to1176:72minibatches, four epochs
of18. Observation arrays are encoded and hashed in the project environment;
the sibling Torch environment receives those exact arrays and saved schema metadata.
Its incompatible live encoder is not used. Initial setup failures are preserved.
Six focused tests pass; reward components reproduce recorded rewards and completed
Monte Carlo returns, and potential terms telescope exactly within numeric tolerance.
A finite-difference check confirms the fixed-bank margin gradient.
Independent review verifies cached encoding, all4425return decompositions and
normalization, with separate NumPy gradients and component finite differences
agreeing with the Torch results. Its analytical momentum projection also agrees.

The batch contains48early SCV and547early wait decisions. Mean raw SCV advantage
is positive (.16330), but actual whole-batch normalization gives it -.27488;
early wait is also negative (-.29452). Three games have negative normalized early
SCV means and one positive; no game supplies a terminal victory reward. This is
not evidence that SCV alone is penalized or that simply removing normalization
would improve gameplay.

At behavior weights, the full-batch actor negative-gradient direction decreases
the fixed-bank SCV/wait margin (derivative -.10843). Weighted critic direction
slightly increases it (+.00367); entropy decreases it (-.00144). Saved momentum's
analytical zero-new-gradient Adam direction also decreases it (-.000923), using
separate old/new row ages. Actual saved parameter displacement projects negatively
on the local margin gradient (-.21718). These are local derivatives and projections,
not a causal decomposition of the actual multi-minibatch update.

Evidence supports inspecting temporal credit and batch weighting next, before
changing primitives or adding sensory fields. It does not prove a GAE setting or
reward change will win games. No new training arm is launched by this audit.
Receipts: `logs/scv-credit-audit/inputs.json`, `preference.json`, `credit-inputs.json`,
`credit.json`, `logs/audit/scv-preference-independent-review.json`, and
`logs/audit/scv-credit-independent-review.json`.
