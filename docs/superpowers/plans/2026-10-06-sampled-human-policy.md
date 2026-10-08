# Sample learned ability probabilities in frozen native imitation

The corrected, engine-conditioned greedy policy produces three workers but then
issues Smart repeatedly without a depot. Inspect one alternative deployment of
exactly those learned scores: seeded categorical ability sampling, temperature1,
with all other command arguments selected as before. No weights, objective,
expert labels or strategic rules change. This is imitation inference, not RL.

Implement explicit optional ability seed for GoalFirst only. Sample after engine
candidate masking, so masked abilities have zero probability. Keep default greedy
behavior and supervised/forced-label behavior unchanged. Local RNG advances only
when a real prediction selects an ability; independent trace reconstruction must
initialize the same seed and reproduce all draws, commands and issued history.
Preserve engine guards, observation profile, raw traces and query provenance.
Record the ability seed in the episode receipt.

Checks: reproducible seeded predictions, unchanged weights/input masks/default
behavior, non-greedy choices appear in a controlled distribution, masks remain
respected, forced labels are not randomized, and empty candidates do not consume
RNG state. Full normal/focused Torch tests, Ruff/diff and independent review.
Then one predeclared native baseline opener with ability seed120603, existing
profile/engine candidates, AcropolisLE/VeryEasyZerg/RandomBuild/game seed120602,
180game seconds/120wall seconds, cap32, two CPU threads, 80%wholeCPUguard.

Inspect actual worker/depot/barracks construction, bad targets/placements, command
errors and economy. Independently reconstruct its trace and immutable weights.
Do not extend/select a seed because of its outcome, promote the failed checkpoint,
or infer reliable planning from chance construction. If legal sampling reveals
argument/execution faults, diagnose them before another full-controller fit.
Useful human imitation, learned micro transfer and Hard/higher gates stay open.
