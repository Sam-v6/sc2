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
