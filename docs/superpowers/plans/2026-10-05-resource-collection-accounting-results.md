# Resource collection accounting results

The [separately declared collection task](2026-10-05-resource-collection-curriculum.md)
passes its physical accounting gate. This establishes usable reward counters,
not learning, transfer or reliable Hard strength. The preceding
[net-loss objective failure](2026-10-05-economic-accounting-failure.md) remains
closed and preserved.

Fixture113001 completes all eight checks on Simple64, with isolated debug setup
and no policy training. Ordinary depot spending100, cancellation/refund75 and
Orbital Command morph spending150 leave both collected counters unchanged.
Isolated mineral mining adds25 minerals; isolated gas mining adds56 gas without
mineral income. An enemy-damage Marauder death is observed by its protocol death
tag, leaves collected counters unchanged and adds100/25 to descriptive loss
counters. Subsequent settling adds no collection. Losses/refunds are excluded
from this new objective.

The run retains777 incremental observations, all checks and a10,985-byte actual
SC2 replay, build75689. It reaches270 game seconds in14.585 wall seconds; checks
finish at138.571 game seconds. Seven sampled CPU windows average3.9603% and
peak6.0373%. No GPU learner runs.

Independent completed-data review verifies44 frozen hashes and reconstructs
every check from raw observations, including bank changes, separate harvesting,
death and settling. Five synthetic tests pass, including refund-loss exclusion
and SIGKILL evidence retention. Receipt:
`logs/audit/resource-collection-fixture-complete-independent-review.json`.
The receipt binds actual JSONL/replay hashes separately: its observations/checks
summary fields are counts/lists, while raw file paths are fixed by the frozen
driver. Original failed fixture and all unplayed curriculum/transfer banks remain
preserved. No task checkpoint, training or evaluation games have run.

The isolated task migration and evaluation-adapter core is implemented and
independently reviewed: actor/body/RNG remain exact, critic and every optimizer
moment/age reset, strict task gamma1/scale.001/version context, normal production
loader rejection and frozen Hard evaluation with ordinary combat scoring.
Five migration tests and an independent nonzero-critic finite-return check pass.
Receipt: `logs/audit/resource-collection-task-migration-review.json`.
A sixth local test checks terminal-only collection reward without ordinary
potential, victory or kill leakage in the separate task bot.

Next: implement and separately review the curriculum worker, Torch helper and
supervised controller, then freeze them before the fixed32 training episodes.
The task bot and future runtime are not yet independently reviewed or frozen;
passing accounting does not bypass those implementation checks. Artifacts live
in `logs/resource-collection-curriculum/`; the retained parent is unchanged.
