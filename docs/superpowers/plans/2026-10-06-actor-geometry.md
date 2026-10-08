# Learned actor geometry

Frozen small-set evidence: 46/62 exact actors, 59/62 correct type/count groups,
and 47/62 exact actors with human count supplied. Of 11 construction mismatches,
7 alternate workers are over two Euclidean tiles farther from the human target;
several differences exceed 20 tiles. Position and first orders are present in
the player-visible data. This motivates better within-type spatial ranking;
it does not establish illegal commands or prove geometry is the sole cause.

Implement an opt-in learned residual on actor logits. Features are each known
entity's dx/dy from the mean eligible actor position, scaled by 32 world tiles,
plus dx²/dy². The ability-conditioned context learns four score coefficients.
No human target or actors enter ordinary inference. No nearest-worker rule,
action restriction or new gameplay primitive is introduced. Zero initialization
preserves all starting scores and RNG draws; disabled defaults and legacy
checkpoint loading remain unchanged. Cache/save/load the flag and expose it in
the human trainer's CLI/configuration. All actor losses train the residual and
shared context through the existing gradients.

Checks: RED→GREEN tests for residual/shared gradients, translated feature
invariance, entity permutation, zero/default parity and save/load. Full unittest,
Ruff/diff checks and independent review before fitting. Preserve source/code
bindings of historical runs; never rerun old receipts with changed production
code and describe them as unchanged.

First bounded experiment uses exactly the 62 selected teaching rows from the
small-set contract, identical initialization/shuffle/200epochs/800updates and
120optimizer-second cap, with only actor geometry enabled. No importance or
context normalization. Require at least56 complete,56 exact actors,62 abilities
and59 targets. Verify sources/code/checkpoint and terminal evidence. Failure
ends this test, with no extension or sweep. Success only permits a later frozen
cross-game human comparison, not promotion, native competence or RL. CPU-only,
two BLAS threads, no download, reserved or diagnostic predictions in this test.

The context audit's first attempt stopped on a floating-point mean comparison:
changing selected-row order alters point means by1.39e-17. Corrected audit keeps
all integer/field totals exact and bounds only those mean differences at1e-10.
Training and source data were unchanged. Receipt:
`logs/roadmap/professional-small-set-01/actor-context.json`.

Implementation verified: four tests observed RED→GREEN; fifth checks that a
learned geometric score can prefer an interior unit. Full327tests pass in10.06s;
Ruff/diff checks pass. Independent reviewer reports no Critical/Important/Minor
findings. Default initialization/legacy loading and all combined BCE/ranking
gradient branches are verified. At implementation commit, the fixed experiment
had not yet run; its subsequent outcome is recorded below.

The experiment is now terminal: same62commands/33abilities, same200epochs and
800updates,12.17optimizer seconds. Zero-residual initial audit exactly matches
the baseline; selected row indices and source hashes match. Complete copying
improves44→51, exact actors46→52, targets59→60; abilities/modes/queues stay62/62
and known timing43/43. Complete/actor gates fail56; ability/target gates pass.
Checkpoint, source/code bindings and exact updates verify. No extension, sweep,
cross-game fit, native competence, promotion or RL follows this failed gate.

Frozen new actor audit: count/type composition60/62; human-count oracle exact54.
Eight remaining mismatches choose another single SCV; two select two same-type
production/research buildings where the human chose one. The residual improves
this controlled fitting test, but does not resolve ranking or generalization.
Artifacts: `professional-small-set-actor-geometry-01/{contract,report,actor-diagnosis}.json`.
