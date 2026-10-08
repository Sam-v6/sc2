# Human production forecast coverage audit

Current work is human imitation only. No optimizer, native game, RL, checkpoint
selection or reserved replay is authorized by this experiment.

Question: can existing teaching observations supervise upcoming human production
decisions more densely than the rare immediate production commands?

Use only the six already fitted games 294, 870, 955, 839, 991 and 523 from
pro-demonstrations-07. The audit taxonomy is engine abilities whose friendly names
start with Build, Train or Research. This is a limited diagnostic taxonomy, not a
restriction on the controller's raw action vocabulary or the final macro scope.

For each retained command observation, find the current or next retained production
command in exact (game loop, source sequence) order. Label its ability and remaining
time. Censor the label when any unresolved issued event intervenes, or no production
event remains. Never put future observations, targets, actors or commands into inputs.
Require one command per retained event and reject inconsistent event identities.

Report source hashes, immediate versus forecast counts by ability, unique target
events, delay distribution, counts within 1/5/15/30 seconds and unknown/end
censoring. Repeated labels for one future command are not independent demonstrations.
Independently reconstruct every label with a direct forward scan, check sources and
observations remain unchanged, and run focused and full normal tests.

Coverage alone cannot establish predictability or competence. Choose a separate,
bounded supervised predictability test only after reviewing this audit. Do not
extend a previous failed full-controller fit or run another execution-only opener.
