# Native placement primitive: verified result

The explicit `--engine-placement` adapter option reuses the existing local engine
placement resolver. Original model commands and actual dispatched commands stay
separate in traces. Exact placement requests/responses and helper decisions are
recorded. History remembers adjusted dispatched commands; rejected intentions
never dispatch or enter history. Ability and placement blocks are counted separately.
Default behavior is unchanged; building/actor/group/queue choices remain learned.

New integration tests initially fail for missing actual-command fields and absent
rejection handling, then pass. They inspect the actual protobuf sent to the fake
engine, adjusted history, rejection with no action/history, and default behavior.
Existing primitive tests cover nearest legal point/group/queue preservation.
Normal suite: 390 tests, 31 optional skips. Focused Torch/execution suite: 30 tests.
Ruff/diff and independent implementation/wrapper review pass.

## Frozen native check

Watcher61363 and verifier76397 are terminal exit0. Same fixed checkpoint, source
profile, engine candidates, ability seed120603 and game seed120602 as the sampled
opening; AcropolisLE/VeryEasyZerg/RandomBuild; 180 game seconds, cadence cap32.
The deliberately truncated episode is not a completed game or a victory.

-125model decisions and dispatched commands;122Success,3NotSupported.
-Three point adjustments; no placement-location failures or placement/ability blocks.
-One new completed CommandCenter, two completedDepots and two completedRefineries.
-Final total workers16 (four new observed worker tags); noBarracks orarmy.
-Final minerals885,gas400,foodused/cap17/46; clearly inefficient excess supply.
-Whole-host CPUpeak10.5%; noGPU,fitting,resource stop orRL.

The model requests two CommandCenters at nearly the same original point; both
resolve to137.5,33.0, with distances4.32and4.58tiles. Only one additionalCommandCenter
actually completes. OneDepot adjusts0.70tiles. The existing helper uses a square
local search, so Euclidean adjustment can exceed four tiles. No new expansion
strategy is supplied. Final raw observations explicitly show build_progress1.0
for all six structures including the initialCommandCenter.

Independent reconstruction reproduces all sampled choices, exact placement
requests, saved engine responses, helper selections, decoded dispatched arguments,
delays and actual issued history. It checks source/profile/checkpoint hashes, prior
fit verification chain, counters and raw action results. Evidence:
`logs/roadmap/placement-human-native-01/verification.json` with bound trace,
static/episode/replay/telemetry/policy files. Historical source is kept in Git.

## Limits and next concrete problem

The primitive removes observed point-placement failures in this opening, but it
does not establish competent macro behavior. NoBarracks was selected in the new
trajectory, so this cannot demonstrate repair of the previousBarracks attempt.
Actual adjusted-command history changes subsequent predictions; the same RNG
seed does not force the same commands after that state/history change. Do not
extend or sweep this closed diagnostic or promote the failed fitted checkpoint.

Three BuildRefinery unit-target commands returnNotSupported. The point resolver
currently passes unit-target construction through unchanged. Next investigate
those selected resource targets and engine placement responses at their exact
visible positions. If occupied-resource placement is the cause, add validation
that preserves the chosen unit target and rejects invalid construction; avoid
silently choosing a different gas location. Ability availability alone does not
prove target validity. This is execution validation, not a learned build strategy.
Further human imitation quality and full-game assessment remain necessary before
RL. Micro transfer, reliable all-raceHard wins and higher-difficulty gates stay open.
