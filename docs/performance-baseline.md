# Measured simulation baseline

Measured locally on 2026-10-04 using the installed Python 3.12 environment,
BurnySC2 7.1.1 and Linux SC2 build 75689. These are diagnostic experiments on
unchanged scripted bots, not an implemented training loop or learned-policy result.

## Simulation cadence

Scripted MassReaperBot, Terran vs Hard Zerg, Simple64, game seed 7, Python
random seed 7, DEV logging disabled, 180-game-second limit. One isolated match
per setting; no concurrent SC2 benchmark during these measurements.

| Game step | Callbacks | Startup seconds | Gameplay wall seconds | Total wall seconds | Workers / army supply at cutoff |
| --- | ---: | ---: | ---: | ---: | --- |
| 8 | 505 | 4.929 | 3.924 | 9.957 | 20 / 4 |
| 16 | 253 | 5.009 | 2.683 | 8.786 | 21 / 3 |
| 32 | 127 | 4.795 | 1.908 | 7.788 | 20 / 3 |

Every run was truncated with a Tie and saved a nonempty replay. None proves a
win or a full-game win rate. Increasing the step reduced gameplay wall time by
51% from 8 to 32 in this one test, but total wall time only fell by 22%. Startup
and teardown matter, and the policy execution changed: army/economy snapshots
are not identical. Cadence selection must include full-game behavior checks.

## Worker contention

Four short matches per group, game step 8, same bot/map/opponent/difficulty,
seeds 7 through 10. Run groups sequentially, with fresh game startup for every
match. Wall time includes supervisor/child startup. Each group completed four
truncated matches with no recorded callback errors and nonempty replays.

| Concurrent workers | Four-match wall seconds | Aggregate simulated seconds per wall second |
| ---: | ---: | ---: |
| 1 | 38.899 | 18.510 |
| 2 | 21.933 | 32.827 |
| 4 | 11.788 | 61.079 |

Four workers delivered 3.30 times the one-worker throughput for this workload.
This does not establish the optimum for long games, larger armies, or neural
training. The old sixteen-worker default has not been measured. Start with a
small explicit pool and measure again on the real training workload. Also
investigate retaining game processes between episodes: nearly five seconds of
startup dominated these short games, and the installed library contains a
multi-game hosting API. Reuse needs lifecycle/replay/error tests before adoption.

## Logging cost

A separate in-memory benchmark created 2,000 rows with 70 float columns. Growing
a pandas DataFrame with `.loc[len(df)] = row` took 2.313 seconds; appending records
to a list followed by `DataFrame.from_records` took 0.00731 seconds. pandas
asserted the resulting frames equal. That is about 316 times faster for this
logging-only microbenchmark. It is not an overall SC2 speedup measurement.

## Scripted Hard-opponent comparison

One complete game per race with MassReaperBot, Simple64, seed 7, game step 8,
Hard difficulty, default RandomBuild, 1,200-game-second limit. These three games
ran concurrently after the contention benchmark; their wall times are not
isolated throughput measurements.

| Hard opponent | Result | Game seconds | Wall seconds | Replay bytes |
| --- | --- | ---: | ---: | ---: |
| Terran | Defeat | 511.071 | 23.707 | 31,821 |
| Protoss | Defeat | 611.071 | 27.886 | 38,908 |
| Zerg | Defeat | 773.571 | 33.819 | 53,308 |

All three reached terminal Defeat, not the cutoff, with no recorded callback
errors and saved replays. This shows that a ready-made Terran example cannot be
assumed to satisfy the requested Hard target. Three games on a single simple map
and seed cannot establish a general win rate; no RL policy has been trained here.

## Reproduction evidence

Raw receipts, subprocess logs, replays and diagnostic scripts are retained in
`logs/audit/` in the isolated worktree. Run diagnostic scripts with the original
checkout's `.venv/bin/python`; they explicitly set the existing external game
path and import this worktree's bot code. The scripts contain machine-specific
paths and are measurements, not intended user-facing commands.

Files: `reaper-step8.json`, `reaper-step16.json`, `reaper-step32.json`,
`contention.json`, `logging-benchmark.json`, `benchmark.py`, `contention.py`.

These baseline measurements precede the implementation. The training/replay commands
and later learning results are documented in README.md and experiment-results.md.
No learning parameters or production bot logic were changed to generate this baseline.

## Parallel learning collection

The implemented parent learner was also measured with four real180-second VeryEasy
smoke episodes, same initial seed7, one-second macro cadence and game step8.
Run groups sequentially without another SC2 experiment during this measurement:

| Collection workers | Run wall seconds | Simulated seconds | Updates | Failures |
| --- | ---: | ---: | ---: | ---: |
| 1 | 35.997 | 720 | 676 | 0 |
| 4 | 10.619 | 720 | 676 | 0 |

The four-worker run was3.39 times faster in this short workload. Every game saved
its replay and was a cutoff Tie, not a win. Serial collection updates behavior
between each game, while the parallel batch shares its starting behavior snapshot;
these are throughput measurements, not equal trajectory or strength comparisons.
Both checkpoints advanced to four episodes and676 parent learner updates.
Receipts/checkpoints are in `logs/parallel-benchmark/{one,four}/`.

A separate real interruption test observed four running SC2 binaries, interrupted
only its own trainer, and confirmed no surviving descendants, unchanged canonical
checkpoint and no candidate/temporary saves. Linux names the engine process
`Main_Thread`; executable identity was used to count the engines correctly.
