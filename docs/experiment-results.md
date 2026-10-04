# Local experiment results — 2026-10-04

All results below are development experiments, not final acceptance. Replays,
action observations, checkpoint snapshots and JSON receipts are retained under
`logs/` in `.worktrees/terran-rl`. No learned Hard strength has been established.
The final target remains frozen evaluation against all three races and varied
builds/maps, using a fresh seed bank after development choices are finished.

## Infrastructure evidence

- Real 120-second training smoke games produced updates, saved checkpoints and
  nonempty replays. Resuming preserved the optimizer, replay experience and RNG.
- Frozen evaluation left the checkpoint SHA-256 unchanged. A forced one-second
  wall timeout also left the canonical checkpoint unchanged.
- Linux replay rendering used the already installed SC2 4.10 build 75689,
  OSMesa and ffmpeg. A learned-agent replay exported 124 frames at 640x480;
  the 31-second MP4 represents 120 game seconds at four frames per second.
- The current unit suite includes command ordering, replay terminal observations,
  encoder error preservation and early-failure receipt regressions.

## Initial five-second macro experiment

| Run | Completed / requested | Wins | Losses | Cutoffs | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hard training | 20 / 20 | 0 | 20 | 0 | 0 |
| Frozen Hard development evaluation | 6 / 6 | 0 | 6 | 0 | 0 |
| Random Hard comparison | 6 / 6 | 0 | 6 | 0 | 0 |
| VeryEasy curriculum, manually interrupted for repair | 13 / 20 | 10 | 1 | 2 | 0 |

The six-game comparisons use Simple64, Rush and Macro builds, all three races,
and seeds 10000–10005. The learned checkpoint after Hard training has SHA-256
`f94113376c30151f2ea357874111c936da54527ff46753adeb28f8020fc3aa0c`.
Both frozen and random comparisons preserved that checkpoint. The three scripted
Hard losses in `performance-baseline.md` used a different seed/build setup and
are not a matched comparison to these runs.

Review found a primitive bug: worker redistribution ran after macro construction
and could issue a gather command to the newly selected builder, canceling its
build order. Some traces logged a command as issued without the expected resource
expenditure or pending structure at the next observation. These data remain useful
for debugging, but do not represent the repaired executor. Gathering now runs
before macro decisions; a regression test reproduces the old ordering failure.

The frozen policy also rarely trained workers and built excessive infrastructure.
Five seconds per atomic action limited production. The next experiment starts a
fresh checkpoint with repaired command ordering and one-second macro decisions,
beginning with easier opponents. Its live feature representation and action space
are still explicitly experimental. None of these changes scripts a build order
or chooses an army mix on the policy's behalf.

## Representation limits

Visible enemy counts and distances are observed during play, but the compact
encoder loses unit identities, terrain and detailed positions. This is not the
end state requested by the user. Broader perception should be evaluated after
this first experiment establishes a reliable learning and replay workflow.

## Repaired executor and learning diagnostics

The fresh one-second, gamma .99 v2 batch completed 20 VeryEasy games: 16 wins,
1 loss, 3 cutoffs, no failures. An early frozen development snapshot lost all six
VeryEasy games by repeatedly choosing wait; exploratory training wins were not
reliable greedy-policy strength. The separate gamma .998 v3 batch completed
20 VeryEasy games: 16 wins and 4 cutoffs, no failures.

A controlled offline probe trained 32-step returns and masked Double-DQN from an
eight-game v3 snapshot: frozen VeryEasy evaluation yielded 4 wins and 2 cutoffs;
frozen Hard evaluation yielded 6 losses. These probes use development seeds
10000–10005, Simple64, Rush/Macro, all three races. Their buffers are diagnostic
artifacts and explicitly cannot be resumed with the earlier one-step trainer.

The current trainer uses up to 32 decision rewards, records the actual bootstrap
discount, and uses online action selection with target-network valuation. Version2
checkpoints retain these discounts and load version1 experience as one-step.
Partial cutoff horizons bootstrap; terminal horizons stop. For a new checkpoint,
gamma=.99**(macro_seconds/5) preserves the initial physical discount horizon.
Uncorrected long returns include exploratory continuation; frozen evaluation must
check whether this credits waiting for later exploratory actions.

A learned exploratory VeryEasy Terran win exported fully: 512 frames, 501.79 game
seconds, 128-second MP4. The viewed frame shows excessive infrastructure, reinforcing
that easy wins alone do not establish useful macro strategy or Hard strength.

## Spatial primitives and parallel collection

Independent review traced one frozen game to357 failed expansions out of358
selections, and another to repeated queued tech-lab commands without construction.
Expansion now requires an eligible builder, a reachable and placeable destination;
execution uses that same builder/destination. Add-on choices use feasible producers,
and later construction preserves vacant add-on footprints. These are execution
constraints, not a prescribed expansion timing or technology strategy.

The earlier Easy curriculum finished30 games:17 wins,4 losses,9 cutoffs. The repaired
v5 Medium batch finished40 games:8 wins,25 losses,7 cutoffs, no engine failures.
Its starting and post-Medium frozen Hard evaluations each lost six games.
Replay experience from the earlier spatial defects was cleared while retaining
weights/target/optimizer/RNG; that migration is recorded in `logs/learning-v5/`.

The current trainer collects four games per behavior snapshot, then the parent
learns from successful episode samples in launch order. Worker models never
replace newer parent weights.46 unit tests pass, including mixed-failure schedule
resume and cancellation. Real short collection measured3.39x throughput with four
workers; details are in performance-baseline.md. A real four-engine interruption
preserved the canonical checkpoint, removed candidate saves and left no descendants.

## First frozen Hard victory

A separate frozen-only economic-capacity shaping probe replayed the same20-game
v3 observation buffer, using32-step returns and10000 Double-DQN updates from fresh
seed19 weights. Its potential is:

`max(0, .5*workers + .2*army_supply + 2*bases - .002*resource_bank)`

Resource bank uses the encoder's clipped mineral/gas values; terminal results
remain+100/-100. There is no scripted macro build order or army mix. This diagnostic
checkpoint must not resume under the trainer's older reward potential.

Frozen Hard evaluation on the reused development bank won1/6 games, with5 terminal
losses and no failures. The win was Terran versus Hard Protoss Rush, Simple64,
seed10001,851.79 game seconds. The selected actions included44 SCVs and44 marine
commands; peak observed workforce54, army supply47, marines30. Evaluation performed
no updates; SHA-256 before/after remained:
`5b335bde6c0593980cbdd0139f40d8362af8f9babb4a49996e25000ac3446251`.

The descriptive Wilson95% interval for1/6 is approximately3%–56%; these seeds have
been used for development selection, so fresh holdout evaluation is still required.
One victory does not meet the all-race/reliable Hard target. Raw evidence is in
`logs/economy-hard-eval/`, the frozen probe and its objective receipt in
`logs/economy-probe/`, and the probe script in `logs/audit/economy-potential-probe.py`.
