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
