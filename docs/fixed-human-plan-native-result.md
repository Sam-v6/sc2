# Fixed human production playback: execution diagnosis

This report covers native01–13. See [command-repeat recovery and later native results](human-command-repeat-recovery.md) for the current state.

October 7, 2026. A native controller now executes the fixed Clem opening with
persistent producer and worker identities, exact placements, original queue flags,
and the established mining/construction/combat helpers. This is scripted playback,
not a fitted policy or RL. Useful human imitation remains unproven.

Native13 resolves 127 of 212 instructions before stopping on a missing
source Factory. It has 49 workers, 39 army supply and zero idle workers at the stop.
The trace independently verifies a Factory landing on its intended shared Tech Lab.
All diagnostic failures intentionally leave the game; their `Defeat` receipts do
not measure natural opponent victories. The opponent is VeryEasy Zerg Rush on
Acropolis, source-side spawn, seed 817501, with no debug setup. This does not replace
the separately verified scripted Hard baseline.

## Execution defects found and repaired

- A repeated Depot construction request now resumes its bound foundation or records
  an already completed foundation, rather than buying or placing a duplicate.
- Smart orders resuming construction protect their workers from reassignment.
- Cancel Last resolves to the queried actor-specific ability (308 on the Command
  Center, 306 on other tested producers). Empty queues and canceled unsubmitted
  requests are recorded explicitly. Research tiers are never aliased this way.
- Waiting production orders reserve future supply. Checking current free supply
  alone had accepted a Hellion that later failed with NotEnoughFood.
- Independent producers can proceed while another producer is blocked. The oldest
  earlier unfinished request reserves its resources so later spending cannot
  starve its Orbital morph. Lift/Land have zero production cost; Orbital pricing
  subtracts the existing Command Center cost.
- Nine original SCV movement commands preserve queue flags and stable worker
  bindings. Mining does not commandeer prepositioned builders. Explicit unqueued
  human movement may interrupt construction; recovery helpers resume the abandoned
  foundation. These movements are labels, not future observation features.
- Landing clearance moves owned ground units out of the footprint and keeps combat
  or mining assistance from immediately sending them back during flight. Native12
  and native13 attach the Factory at (131.5,44.5) to the full-tag Tech Lab at
  (134,44), first verified at loop8592, with zero delayed action errors.
- One unsubmitted source Depot request at8268 has no source foundation and is
  superseded by the actual unqueued worker move at8284, followed by construction
  at a different site at8297. The executor records that retirement explicitly.
- SDK startup/callback failures cannot produce a successful zero-frame episode.

## Bounded diagnostic results

Each job retains its contract, source hashes, trace and replay. Source snapshots
preserve the implementation used before subsequent changes. The game horizon is
600 seconds, wall deadline300 seconds, and per-instruction allowance30 seconds;
they were not expanded to pass a failed test.

| Native canary | Resolved instructions | Terminal finding |
| --- | ---: | --- |
| 01 | 47/203 | Repeated Depot site rejected; supervisor also failed after episode completion |
| 02 | 49/203 | Generic Cancel Last absent from native query |
| 03 | 91/203 | Empty-queue Cancel stall; trace also contained a delayed supply error |
| 04 | 82/203 | Stops at first delayed Hellion supply error |
| 05 | 77/203 | Global instruction order stalls independent supply/production |
| 06 | 35/203 | Later producer spending starves earlier Orbital morph |
| 07 | 0 | Startup KeyError on passive upgrade metadata; invalid game evidence |
| 08 | 85/203 | Worker travel/supply timing misses Hellion deadline |
| 09 | 0 | Callback failure: custom worker binding name collided with SDK attribute |
| 10 | 60/212 | Executor deferred an intentionally unqueued worker movement |
| 11 | 118/212 | Ground army blocks Factory landing after initial legal query |
| 12 | 120/212 | Source Depot request never produces a matching foundation |
| 13 | 127/212 | Later Lift refers to a Factory omitted from the source command plan |

Native12/13 independently verify terminal trace length, failure location, original
source snapshots, exact Factory attachment, replay seed, zero delayed errors and
whole-host CPU peaks5.5%/5.4%. Resolved counts include documented cancellations,
retirements and completed-foundation repeats; they do not count completed products.

## Next repair: command target updates

The original replay contains `SCmdUpdateTargetPointEvent` at7171 with point
(134.5,37.5), following Factory command636 at7168. The accompanying command-manager
event advances to sequence637. The source Factory4392484873 first appears there at
7262 with build progress0.0073. The existing raw-command dump includes only the
initial command and omits this update, leaving that Factory absent from playback.

Evidence is in `logs/roadmap/missing-factory-target-update-01/audit.json`. Resolve
inherited ability, queue behavior and selected/actual worker from original events
and observed source orders before adding a teaching label. Do not invent a build
from its eventual birth alone. Audit other target-update events as well; this may
explain additional missing human commands. Then rerun the bounded fixed plan before
fitting another imitation model. RL remains paused.

The verified builder plan and native checks are in:

- `logs/roadmap/fixed-human-production-plan-03/verification.json`
- `logs/roadmap/fixed-human-plan-native-12/verification.json`
- `logs/roadmap/fixed-human-plan-native-13/verification.json`

The complete suite passes543 tests with32 skipped; focused execution tests and
Ruff checks pass. Neither these tests nor a successful prefix establish useful
learned strategy, full human-command coverage, or learned Hard victories.
